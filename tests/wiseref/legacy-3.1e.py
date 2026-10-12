"""Test the unmodified hithesis v3.1e classes with the current wiseref.

Supply a git-archive snapshot extracted with hithesis.ins. Builds are isolated
and use XeLaTeX, the only engine supported by these legacy classes. Baseline and
observation preserve ordinary labels, glyph positions and links; auto mode is
recorded separately from explicit language/name configuration.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2].parent / 'latex-wiseref'
SPEC = importlib.util.spec_from_file_location('reference_tests', ROOT / 'test/run.py')
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
TAG_COMMIT = '366e37f5b3c621242229a8dc20fb41a47699b9a8'


def cases():
    result = []
    for degree in ('bachelor', 'master', 'doctor', 'postdoc'):
        for campus in ('harbin', 'weihai', 'shenzhen'):
            for lang in ('zh', 'en'):
                result.append(dict(name=f'book-{degree}-{campus}-{lang}',
                                   cls='hithesisbook', degree=degree, campus=campus, lang=lang, tags=False))
    for degree, campus, stages in (
        ('master', 'harbin', ('opening', 'midterm')),
        ('bachelor', 'weihai', ('opening', 'midterm')),
        ('master', 'shenzhen', ('opening', 'midterm')),
        ('doctor', 'harbin', ('opening', 'midterm')),
        ('doctor', 'shenzhen', ('opening',)),
    ):
        for stage in stages:
            result.append(dict(name=f'art-{degree}-{campus}-{stage}', cls='hithesisart',
                               degree=degree, campus=campus, stage=stage, lang='zh'))
    result.append(dict(name='artplus-doctor-shenzhen-midterm', cls='hithesisartplus',
                       degree='doctor', campus='shenzhen', stage='midterm', lang='zh'))
    for name in ('book-master-harbin-zh', 'book-master-shenzhen-en',
                 'art-master-harbin-opening', 'artplus-doctor-shenzhen-midterm'):
        case = next(c for c in result if c['name'] == name)
        result.append(case | dict(name=name + '-preload', preload=True))
    for lang in ('zh', 'en'):
        case = next(c for c in result if c['name'] == f'book-master-harbin-{lang}')
        result.append(case | dict(name=case['name'] + '-cm-math', cm_math=True))
        result.append(case | dict(name=case['name'] + '-style', style=True))
        result.append(case | dict(name=case['name'] + '-tags', tags=True))
        result.append(case | dict(name=case['name'] + '-tags-fixed', tags=True, index_fix=True))
    return result


def driver(case, phase):
    loaded = phase != 'baseline'
    options = f'fontset=fandol,type={case["degree"]},campus={case["campus"]}'
    if case['cls'] == 'hithesisbook':
        options += ',language=' + ('english' if case['lang'] == 'en' else 'chinese')
    else:
        options += ',stage=' + case['stage']
    if case.get('cm_math'):
        options += ',newtxmath=false'
    lines = [r'\errorcontextlines=100']
    if case.get('preload') and loaded:
        lines.append(r'\RequirePackage{wiseref}')
    lines.append(r'\documentclass[' + options + ']{' + case['cls'] + '}')
    if case.get('style'):
        lines += [r'\usepackage{hithesis}', r'\def\WiseStyle{1}']
    if loaded and not case.get('preload'):
        lines.append(r'\usepackage{wiseref}')
    if case['cls'] == 'hithesisbook':
        lines.append(r'\def\WiseBook{1}')
    if case.get('tags', True):
        lines.append(r'\def\WiseTags{1}')
    if case.get('index_fix'):
        lines += [r'\makeatletter', r'\let\WiseOriginalEqucaption\equcaption',
                  r'\renewcommand\equcaption[1]{\begingroup\let\Hy@make@anchor\@empty\WiseOriginalEqucaption{#1}\endgroup}',
                  r'\makeatother']
    if phase == 'configured':
        gap = '~' if case['lang'] == 'en' else ''
        eq_name = r'\equationname' if case['cls'] == 'hithesisbook' else '式'
        lines += [r'\wiserefsetup{lang=' + case['lang'] + ',',
                  r' figure={prefix={\figurename' + gap + '},prefix-plural={' + ('Figures~' if case['lang'] == 'en' else r'\figurename') + '}},',
                  r' subfigure={prefix={\figurename' + gap + '}},',
                  r' table={prefix={\tablename' + gap + '}},',
                  r' equation={prefix={' + eq_name + gap + r'},number-format={\textup{(#1)}}},',
                  r' algocf={prefix={Algorithm~}},lstlisting={prefix={Listing~}}}']
    if phase in ('auto', 'configured'):
        lines += [r'\def\WiseChecks{1}', r'''
\newcommand\WiseCase[2]{\par\noindent CASE-#1-BEGIN #2 CASE-#1-END\par}
\ExplSyntaxOn
\cs_new_eq:NN\WiseOriginalResolve\__wise_resolve_options:
\cs_set_protected:Npn\__wise_resolve_options:
  {\WiseOriginalResolve\iow_term:e{LEGACY-LANG:\l__wise_selected_lang_tl}}
\ExplSyntaxOff
''']
    lines.append(r'\input{cases.tex}')
    return '\n'.join(lines) + '\n'


def compile_phase(root, source, work, case, phase):
    folder = root / phase
    folder.mkdir(parents=True)
    for name in ('hithesisbook.cls', 'hithesisart.cls', 'hithesisartplus.cls',
                 'hithesisbook.cfg', 'hithesisart.cfg'):
        shutil.copy2(source / name, folder / name)
    if case.get('style'):
        shutil.copy2(source / 'examples/hitbook/chinese/hithesis.sty', folder / 'hithesis.sty')
    shutil.copy2(work / 'candidate.sty', folder / 'wiseref.sty')
    shutil.copy2(Path(__file__).with_name('legacy-3.1e.tex'), folder / 'cases.tex')
    (folder / 'main.tex').write_text(driver(case, phase))
    env = os.environ.copy()
    env.update(TEXINPUTS='.:', TEXMFHOME=str(work / 'empty-texmf'))
    with (folder / 'compile.log').open('w') as stream:
        for run in range(5):
            subprocess.run(['xelatex', '-no-shell-escape', '-interaction=nonstopmode',
                            '-halt-on-error', '-recorder', 'main.tex'], cwd=folder, env=env,
                           stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=120)
            log = (folder / 'main.log').read_text(errors='replace')
            rerun = re.search(r'undefined references|Label\(s\) may have changed|Rerun to get wiseref', log)
            if run >= 2 and not rerun:
                break
    assert not rerun, 'References did not converge'
    assert 'Missing character:' not in log
    assert 'v3.1e' in log, 'Unexpected template version'
    return log


def outputs(path, marker, keys):
    text = ''.join(page[0] for page in base.pdf_signature(path))
    result = {}
    for key in keys:
        match = re.search(marker + '-' + key + '-BEGIN(.*?)' + marker + '-' + key + '-END', text, re.S)
        assert match, ('Missing output', key)
        result[key] = re.sub(r'\s+', '', match[1])
    return result


def test_case(work, source, case):
    root = work / case['name']
    phase = 'baseline'
    result = dict(case=case['name'], settings=case)
    try:
        compile_phase(root, source, work, case, phase)
        labels = base.records(root / phase / 'main.aux', 'newlabel', 2)
        baseline = base.pdf_signature(root / phase / 'main.pdf')
        std_keys = ('fig', 'fig-b', 'fig-c', 'table', 'eq', 'eq-native',
                    'panel', 'theorem', 'lemma', 'item', 'note')
        if case.get('tags', True):
            std_keys += ('tag', 'bare')
        if case['cls'] == 'hithesisbook':
            std_keys += ('chapter', 'appendix', 'app-eq')
        if case.get('style'):
            std_keys += ('algorithm', 'listing')
        std = outputs(root / phase / 'main.pdf', 'B', std_keys)
        phase = 'observed'
        compile_phase(root, source, work, case, phase)
        assert labels == base.records(root / phase / 'main.aux', 'newlabel', 2), 'Standard labels changed'
        assert baseline == base.pdf_signature(root / phase / 'main.pdf'), 'Loading wiseref changed text/positions'
        assert base.link_signature(root / 'baseline/main.pdf') == base.link_signature(root / phase / 'main.pdf'), 'Standard links changed'
        ref_keys = ('fig', 'table', 'eq', 'panel', 'theorem', 'lemma',
                    'item', 'note', 'star', 'numbers', 'link-off', 'range', 'mix')
        if case.get('tags', True):
            ref_keys += ('tag', 'bare')
        if case['cls'] == 'hithesisbook':
            ref_keys += ('chapter', 'appendix', 'app-eq')
        if case.get('style'):
            ref_keys += ('algorithm', 'listing')
        phase = 'auto'
        auto_log = compile_phase(root, source, work, case, phase)
        auto = outputs(root / phase / 'main.pdf', 'CASE', ref_keys)
        phase = 'configured'
        log = compile_phase(root, source, work, case, phase)
        actual = outputs(root / phase / 'main.pdf', 'CASE', ref_keys)
        wise = base.records(root / phase / 'main.aux', 'wiserefRecord', 3)
        types = {'a': 'figure', 'table': 'table', 'equation': 'equation',
                 'line-a': 'equation', 'panel': 'subfigure', 'theorem': 'theorem',
                 'lemma': 'lemma', 'proof': '', 'item': 'enumi', 'note': 'footnote', 'unnumbered': ''}
        if case.get('tags', True):
            types.update({'tagged': 'equation', 'bare': 'equation', 'numeric-tag': 'equation'})
        if case['cls'] == 'hithesisbook':
            types.update({'chapter': 'chapter', 'appendix': 'appendix', 'appendix-equation': 'equation'})
        if case.get('style'):
            types.update({'algorithm': 'algocf', 'listing': 'lstlisting'})
        for key, kind in types.items():
            assert wise.get(key, [None])[0] == kind, (key, 'wrong type', wise.get(key), kind)
        star_mode = 'bare'
        if case.get('tags', True):
            assert wise['tagged'][1] == 'tag'
            assert wise['bare'][1] == star_mode, ('bare tag mode', wise['bare'], star_mode)
            assert wise['numeric-tag'][1] == star_mode
        assert labels == base.records(root / phase / 'main.aux', 'newlabel', 2), 'Using wref changed standard labels'
        en = case['lang'] == 'en'
        names = ('Figure', 'Table', 'Equation', 'Theorem', 'Lemma', 'Item', 'Footnote') if en else ('图', '表', '公式', '定理', '引理', '项', '脚注')
        if not en and case['cls'] != 'hithesisbook':
            names = ('图', '表', '式', '定理', '引理', '项', '脚注')
        wanted = {'fig': names[0] + std['fig'], 'table': names[1] + std['table'],
                  'eq': names[2] + '(' + std['eq'] + ')',
                  'panel': names[0] + std['panel'], 'theorem': names[3] + std['theorem'],
                  'lemma': names[4] + std['lemma'], 'item': names[5] + std['item'],
                  'note': names[6] + std['note'], 'star': names[0] + std['fig'],
                  'numbers': names[0] + std['fig'], 'link-off': names[0] + std['fig'],
                  'range': ('Figures' if en else '图') + std['fig'] + ('–' if en else '至') + std['fig-c'],
                  'mix': names[0] + std['fig'] + (',' if en else '，') + names[1] + std['table'] + ('and' if en else '和') + names[2] + '(' + std['eq'] + ')'}
        if case.get('tags', True):
            wanted.update({'tag': names[2] + '(S)',
                           'bare': names[2] + ('(S)' if star_mode == 'tag' else 'S')})
        if case.get('style'):
            wanted.update({'algorithm': 'Algorithm' + std['algorithm'],
                           'listing': 'Listing' + std['listing']})
        if case.get('index_fix'):
            auxiliary = re.sub(r'\s+', '', (root / phase / 'main.aux').read_text())
            assert r'\numberline{S}' in auxiliary, 'Custom tag was lost from the equation index'
        if case['cls'] == 'hithesisbook':
            wanted.update({'chapter': 'Chapter' + std['chapter'] if en else '第' + std['chapter'] + '章',
                           'appendix': ('Appendix' if en else '附录') + std['appendix'],
                           'app-eq': names[2] + '(' + std['app-eq'] + ')'})
        for key, value in wanted.items():
            assert actual[key] == value, (key, value, actual[key])
        assert set(re.findall(r'LEGACY-LANG:(\S+)', log)) == {'english' if en else 'chinese'}
        links, _ = base.link_signature(root / phase / 'main.pdf')
        base.assert_case_links(root / phase / 'main.pdf', links, actual)
        inputs = (root / phase / 'main.fls').read_text()
        assert 'docxlike.sty' not in inputs and 'hithesis.cls' not in inputs
        loaded_classes = [Path(line[6:]) for line in inputs.splitlines()
                          if line.startswith('INPUT ') and Path(line[6:]).name == case['cls'] + '.cls']
        assert loaded_classes, 'Requested legacy class not loaded'
        loaded_class = loaded_classes[0]
        if not loaded_class.is_absolute():
            loaded_class = root / phase / loaded_class
        class_hash = hashlib.sha256(loaded_class.read_bytes()).hexdigest()
        assert class_hash == hashlib.sha256((source / (case['cls'] + '.cls')).read_bytes()).hexdigest()
        result.update(status='PASS', output=actual, default_auto_output=auto,
                      default_auto_profiles=sorted(set(re.findall(r'LEGACY-LANG:(\S+)', auto_log))),
                      type_assertions=len(types), unchanged_labels=len(labels), links=len(links),
                      loaded_class=str(loaded_class), loaded_class_sha256=class_hash)
    except Exception as error:
        result.update(status='BLOCKED_BASELINE' if phase == 'baseline' else 'FAIL',
                      phase=phase, error=str(error), log=str(root / phase / 'compile.log'))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--cases', nargs='+')
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    (args.work / 'empty-texmf').mkdir()
    shutil.copy2(ROOT / 'wiseref.sty', args.work / 'candidate.sty')
    sources = {name: hashlib.sha256((args.source / name).read_bytes()).hexdigest()
               for name in ('hithesis.dtx', 'hithesisbook.cls', 'hithesisart.cls', 'hithesisartplus.cls')}
    assert all('v3.1e' in (args.source / name).read_text() for name in sources if name.endswith('.cls'))
    selected = [case for case in cases() if not args.cases or case['name'] in args.cases]
    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(test_case, args.work, args.source, case) for case in selected]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(result['case'], result['status'], result.get('error', ''), flush=True)
            (args.work / 'results.json').write_text(json.dumps(dict(
                tag='v3.1e', tag_commit=TAG_COMMIT, source_sha256=sources,
                candidate_sha256=hashlib.sha256((args.work / 'candidate.sty').read_bytes()).hexdigest(),
                results=results), ensure_ascii=False, indent=2))
    print('Counts:', {status: sum(r['status'] == status for r in results)
                      for status in ('PASS', 'FAIL', 'BLOCKED_BASELINE')}, flush=True)
    raise SystemExit(any(r['status'] != 'PASS' for r in results))


if __name__ == '__main__':
    main()
