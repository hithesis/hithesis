"""Compare unchanged 3.1e public interfaces, PDF layout, labels and links."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading

import pypdfium2 as pdfium
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PDF_LOCK = threading.Lock()


def cases():
    result = []
    for degree in ('bachelor', 'master', 'doctor', 'postdoc'):
        for campus in ('harbin', 'weihai', 'shenzhen'):
            for lang in ('chinese', 'english'):
                result.append(dict(name=f'book-{degree}-{campus}-{lang}',
                    cls='hithesisbook', options=f'type={degree},campus={campus},language={lang}'))
    for degree in ('bachelor', 'master', 'doctor'):
        for campus in ('harbin', 'weihai', 'shenzhen'):
            for stage in ('opening', 'midterm'):
                if (degree, campus, stage) == ('doctor', 'shenzhen', 'midterm'):
                    continue
                result.append(dict(name=f'art-{degree}-{campus}-{stage}',
                    cls='hithesisart', options=f'type={degree},campus={campus},stage={stage}'))
    result.append(dict(name='artplus-doctor-shenzhen-midterm', cls='hithesisartplus',
        options='type=doctor,campus=shenzhen,stage=midterm'))
    for lang in ('chinese', 'english'):
        template = next(c for c in result if c['name'] == f'book-master-harbin-{lang}')
        for variant, extra in (
            ('cm-math', ',newtxmath=false'),
            ('geometry-one', ',newgeometry=one'),
            ('geometry-no', ',newgeometry=no'),
            ('library', ',library=true,openright=true'),
            ('bools', ',chapterbold=false,raggedbottom=false,fulltime=false,bsheadrule=false'),
            ('forwarded', ',draft=true'),
            ('caption-last-line', ',capcenterlast=true'),
            ('tags', ''), ('style', ''),
        ):
            result.append(template | dict(name=template['name'] + '-' + variant,
                options=template['options'] + extra, tags=variant == 'tags', style=variant == 'style'))
    return result


def signature(path, require_targets=True):
    pages = []
    with PDF_LOCK, pdfium.PdfDocument(path) as pdf:
        for page in pdf:
            text = page.get_textpage()
            try:
                pages.append((text.get_text_range(), [tuple(round(n, 4) for n in text.get_charbox(i))
                    for i in range(text.count_chars())]))
            finally:
                text.close()
            page.close()
    reader = PdfReader(path)
    links = []
    targets = reader.named_destinations
    for page_no, page in enumerate(reader.pages):
        for reference in page.get('/Annots', []):
            annotation = reference.get_object()
            action = annotation.get('/A', {})
            if action.get('/S') == '/GoTo':
                destination = action['/D']
                if destination not in targets:
                    assert not require_targets, ('Missing link target', destination)
                    links.append((page_no, tuple(round(float(n), 4) for n in annotation['/Rect']),
                        str(destination), None, 'UNRESOLVED', None, None))
                    continue
                target = targets[destination]
                links.append((page_no, tuple(round(float(n), 4) for n in annotation['/Rect']),
                    str(destination), reader.get_destination_page_number(target),
                    str(target.typ), str(target.left), str(target.top)))
    return pages, links


def compile_case(source, work, case, phase):
    folder = work / case['name'] / phase
    folder.mkdir(parents=True)
    for suffix in ('*.cls', '*.cfg', '*.sty', '*.bst', '*.ist', '*.eps'):
        for path in source.glob(suffix):
            shutil.copy2(path, folder / path.name)
    if case.get('style') and not (folder / 'hithesis.sty').exists():
        shutil.copy2(source / 'examples/hitbook/chinese/hithesis.sty', folder / 'hithesis.sty')
    shutil.copy2(ROOT / 'tests/compatibility.tex', folder / 'fixture.tex')
    lines = [r'\errorcontextlines=100',
        r'\documentclass[fontset=fandol,' + case['options'] + ']{' + case['cls'] + '}']
    if case['cls'] == 'hithesisbook':
        lines.append(r'\def\HitBook{1}')
    if case['cls'] == 'hithesisartplus':
        lines.append(r'\def\HitArtplus{1}')
    if case.get('style'):
        lines.extend((r'\usepackage{hithesis}', r'\def\HitStyle{1}'))
    if case.get('tags'):
        lines.append(r'\def\HitTags{1}')
        if phase == 'baseline':
            lines.extend((r'\makeatletter', r'\let\HitOriginalEqucaption\equcaption',
                r'\renewcommand\equcaption[1]{\begingroup\let\Hy@make@anchor\@empty\HitOriginalEqucaption{#1}\endgroup}',
                r'\makeatother'))
    lines.append(r'\input{fixture.tex}')
    (folder / 'main.tex').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    env = os.environ | dict(TEXINPUTS='.:', TEXMFHOME=str(work / 'empty-texmf'))
    with (folder / 'compile.log').open('w') as output:
        for run in range(5):
            subprocess.run(['xelatex', '-no-shell-escape', '-interaction=nonstopmode',
                '-halt-on-error', '-recorder', 'main.tex'], cwd=folder, env=env,
                stdout=output, stderr=subprocess.STDOUT, check=True, timeout=120)
            log = (folder / 'main.log').read_text(errors='replace')
            rerun = re.search(r'undefined references|Label\(s\) may have changed', log)
            if run >= 2 and not rerun:
                break
    assert not rerun, 'References did not converge'
    assert 'Missing character:' not in log, 'Missing glyphs'
    assert ('v3.1e' if phase == 'baseline' else 'v3.2a') in log
    assert 'docxlike.sty' not in (folder / 'main.fls').read_text()
    return folder, dict(re.findall(r'HIT-PROBE:([^=\n]+)=([^\n]*)', log))


def test_case(baseline, work, case):
    phase = 'baseline'
    try:
        old, old_probe = compile_case(baseline, work, case, phase)
        phase = 'candidate'
        new, new_probe = compile_case(ROOT, work, case, phase)
        assert old_probe == new_probe, ('Option/default/metadata changes', old_probe, new_probe)
        labels = lambda folder: re.findall(r'^\\newlabel.*$', (folder / 'main.aux').read_text(), re.M)
        assert labels(old) == labels(new), 'Standard labels changed'
        assert signature(old / 'main.pdf') == signature(new / 'main.pdf'), 'PDF text/positions/links changed'
        if case.get('tags'):
            auxiliary = (new / 'main.aux').read_text()
            assert re.search(r'\\numberline\s*\{S\}', auxiliary), 'Custom tag missing from equation index'
        return dict(case=case['name'], status='PASS', probes=len(new_probe),
            baseline_equation_index_workaround=bool(case.get('tags')))
    except Exception as error:
        return dict(case=case['name'], status='BLOCKED_BASELINE' if phase == 'baseline' else 'FAIL',
            phase=phase, error=str(error), log=str(work / case['name'] / phase / 'compile.log'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--cases', nargs='+')
    args = parser.parse_args()
    selected = cases()
    if args.cases:
        unknown = set(args.cases) - {c['name'] for c in selected}
        if unknown:
            parser.error('Unknown cases: ' + ', '.join(sorted(unknown)))
        selected = [c for c in selected if c['name'] in args.cases]
    args.work.mkdir(parents=True, exist_ok=False)
    (args.work / 'empty-texmf').mkdir()
    report = dict(baseline='v3.1e', candidate='v3.2a',
        baseline_sha256=hashlib.sha256((args.baseline / 'hithesis.dtx').read_bytes()).hexdigest(),
        candidate_sha256=hashlib.sha256((ROOT / 'hithesis.dtx').read_bytes()).hexdigest(), results=[])
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = [pool.submit(test_case, args.baseline, args.work, case) for case in selected]
        for job in as_completed(jobs):
            result = job.result()
            report['results'].append(result)
            print(result['case'], result['status'], result.get('error', ''), flush=True)
            (args.work / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('Counts:', {status: sum(r['status'] == status for r in report['results'])
        for status in ('PASS', 'FAIL', 'BLOCKED_BASELINE')})
    raise SystemExit(any(r['status'] != 'PASS' for r in report['results']))


if __name__ == '__main__':
    main()
