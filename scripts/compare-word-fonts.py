#!/usr/bin/env python3
"""Isolated whole-sample font controls; private VM fonts never enter the evidence bundle."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value


pages = load('font_control_pages', ROOT / 'scripts/check-pages.py')
sequence = load('font_control_sequence', ROOT / 'scripts/diagnose-pages.py')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def verify_fonts(directory):
    record = json.loads((directory / 'fonts.json').read_text())
    required = json.loads((ROOT / 'tests/reference/word-fonts.json').read_text())['files']
    for name, expected in record['files'].items():
        if Path(name).name != name or digest(directory / name) != expected:
            raise ValueError('Private font does not match hash record: ' + name)
    for name, expected in required.items():
        if record['files'].get(name) != expected:
            raise ValueError('Font differs from the actual Word content reference: ' + name)
    for name in ('timesi.ttf', 'timesbi.ttf'):
        if name not in record['files']:
            raise ValueError('Missing Times face: ' + name)
    return record


def prefix(fonts, cell, audit):
    features = []
    cjk_features = []
    directory = fonts.resolve().as_posix() + '/'
    if cell in ('latin', 'all'):
        features.append(r'\defaultfontfeatures[Times New Roman]{Path={' + directory +
                        r'},UprightFont=times.ttf,BoldFont=timesbd.ttf,ItalicFont=timesi.ttf,BoldItalicFont=timesbi.ttf}')
    if cell in ('cjk', 'all'):
        for alias, file in [('SimSun', 'simsun.ttc'), ('NSimSun', 'simsun.ttc'), ('SimHei', 'simhei.ttf'),
                            ('KaiTi', 'simkai.ttf'), ('KaiTi_GB2312', 'simkai.ttf'),
                            ('FangSong', 'simfang.ttf'), ('FangSong_GB2312', 'simfang.ttf')]:
            if (fonts / file).exists():
                index = ',FontIndex=0' if file.endswith('.ttc') else ''
                options = '[' + alias + ']{Path={' + directory + '},UprightFont=' + file + index + '}'
                features.append(r'\defaultfontfeatures' + options)
                cjk_features.append(r'\defaultjfontfeatures' + options)
    hook = r'\AddToHook{package/fontspec/after}{' + ''.join(features) + '}\n' if features else ''
    if cjk_features:
        # LuaTeX-ja maintains a separate per-font default feature table. Setting
        # fontspec alone affects baseline probes but not shipped CJK glyphs.
        hook += r'\AddToHook{package/luatexja-fontspec/after}{' + ''.join(cjk_features) + '}\n'
    hook += (r'\AddToHook{begindocument/end}{\directlua{hit_font_audit=dofile("' + audit.as_posix() + r'")}}' + '\n'
             + r'\AddToHook{shipout/before}{\directlua{hit_font_audit.page()}}' + '\n'
             + r'\AddToHook{enddocument/afterlastpage}{\directlua{hit_font_audit.finish()}}' + '\n')
    return hook


def prepare(args):
    fonts = args.fonts.resolve(); out = args.output.resolve()
    record = verify_fonts(fonts)
    if out.exists():
        raise FileExistsError('Control directory already exists: ' + str(out))
    out.mkdir(parents=True, exist_ok=False)
    runtime = out / 'runtime'; runtime.mkdir()
    products = subprocess.check_output(['python3', 'scripts/products.py', '--dist'], cwd=ROOT, text=True).split()
    for name in products:
        shutil.copy2(ROOT / name, runtime / name)
    audit = runtime / 'audit-used-fonts.lua'; shutil.copy2(ROOT / 'scripts/audit-used-fonts.lua', audit)
    source_hashes = {}
    original = out / 'original-sample'
    original.mkdir()
    for degree in ('doctor', 'bachelor'):
        source = ROOT / 'tests/sample' / degree
        dest = original / degree
        shutil.copytree(source, dest, ignore=shutil.ignore_patterns('*.aux', '*.log', '*.out', '*.fls', '*.fdb_latexmk', '*.synctex.gz', '*.bcf', '*.run.xml', '*.blg', '*.toc', '*.toe', '*.idx', '*.ilg', '*.ind', '*.bbl'))
        # main.pdf is archived as the pre-control production result, not reused as output.
        for path in dest.rglob('*'):
            if path.is_file(): source_hashes[str(path.relative_to(original))] = digest(path)
    jobs = []
    for cell in ('baseline', 'latin', 'cjk', 'all'):
        samples = out / cell / 'sample'
        shutil.copytree(original, samples)
        for degree in ('doctor', 'bachelor'):
            main = samples / degree / 'main.tex'
            main.write_text(prefix(fonts, cell, audit) + main.read_text())
            (samples / degree / 'main.pdf').unlink(missing_ok=True)
            jobs.append({'cell': cell, 'degree': degree, 'directory': str(main.parent)})
    manifest = {'kind': 'isolated-whole-sample-font-controls', 'snapshot': json.loads((ROOT / 'build/docxlike-import.json').read_text())['snapshot'],
                'generator_sha256': digest(__file__), 'private_font_directory': str(fonts), 'fonts': record,
                'source_sha256': source_hashes, 'runtime_sha256': {n: digest(runtime / n) for n in products},
                'audit_sha256': digest(audit), 'jobs': jobs,
                'cells': {'baseline': 'current host font lookup', 'latin': 'VM Times family only', 'cjk': 'VM CJK families only', 'all': 'VM Times and CJK families'},
                'reference_manifest_sha256': digest(ROOT / 'tests/reference/word-content/manifest.json'),
                'math_backend': 'unchanged LaTeX math fonts; instructional Word annotations remain different'}
    write_json(out / 'inputs.json', manifest)
    print('Prepared controls:', out)


def font_audit(directory, fonts, cell):
    rows = []
    for raw in (directory / 'used-fonts.tsv').read_text().splitlines()[1:]:
        identifier, name, filename, resolved, index = raw.split('\t')
        actual = next((Path(p) for p in (filename, resolved) if p and Path(p).is_file()), None)
        normalized = re.sub('[^a-z0-9]', '', name.lower())
        family = 'latin' if 'timesnewroman' in normalized else ('cjk' if any(k in normalized for k in ('simsun', 'simhei', 'kaiti', 'simkai', 'fangsong', 'simfang')) else 'other')
        matched = actual is not None and actual.resolve().is_relative_to(fonts.resolve())
        if family in ('latin', 'cjk') and cell in ('all', family) and not matched:
            raise ValueError('A selected font family still uses host files: ' + str((name, filename, resolved)))
        rows.append({'id': identifier, 'name': name, 'filename': str(actual) if actual else filename,
                     'sha256': digest(actual) if actual else None, 'subfont': index,
                     'family': family, 'from_private_vm_directory': matched})
    if not any(r['family'] == 'latin' for r in rows) or not any(r['family'] == 'cjk' for r in rows):
        raise ValueError('Shipped font audit is missing the actual main font families')
    return rows


def build(args):
    out = args.output.resolve(); manifest = json.loads((out / 'inputs.json').read_text())
    fonts = Path(manifest['private_font_directory']); verify_fonts(fonts)
    runtime = out / 'runtime'
    for name, expected in manifest['runtime_sha256'].items():
        if digest(runtime / name) != expected: raise ValueError('Control runtime changed: ' + name)
    env = os.environ | {'TEXINPUTS': str(runtime) + ':' + str(ROOT) + ':', 'LUAINPUTS': str(runtime) + ':',
                        'BSTINPUTS': str(runtime) + ':' + str(ROOT) + ':',
                        'TEXMFLOCAL': str(ROOT / 'build/dependencies/texmf'),
                        'SOURCE_DATE_EPOCH': '1700000000', 'FORCE_SOURCE_DATE': '1'}
    def compile_job(job):
        directory = Path(job['directory'])
        def run(label, command):
            proc = subprocess.run(command, cwd=directory, env=env, capture_output=True, text=True, timeout=180)
            (directory / (label + '.console')).write_text(proc.stdout + proc.stderr)
            if proc.returncode: raise RuntimeError(str((job['cell'], job['degree'], label, proc.returncode)))
        run('latex-1', ['lualatex', '-interaction=nonstopmode', '-halt-on-error', '-recorder', 'main.tex'])
        run('bibtex', ['bibtex', 'main'])
        if (directory / 'main-pub.aux').exists(): run('bibtex-pub', ['bibtex', 'main-pub'])
        previous = None; stable = False
        for number in range(2, 6):
            run('latex-' + str(number), ['lualatex', '-interaction=nonstopmode', '-halt-on-error', '-recorder', 'main.tex'])
            document = pages.pages(str(directory / 'main.pdf'))
            if document == previous: stable = True; break
            previous = document
        if not stable: raise RuntimeError('Unstable line geometry: ' + str(job))
        result = job | {'passes': number, 'pages': len(document), 'pdf_sha256': digest(directory / 'main.pdf'),
                        'used_fonts': font_audit(directory, fonts, job['cell'])}
        write_json(directory / 'build-result.json', result)
        print(job['cell'], job['degree'], 'stable', len(document), 'pages', flush=True)
        return result
    with ThreadPoolExecutor(max_workers=args.jobs) as pool: results = list(pool.map(compile_job, manifest['jobs']))
    write_json(out / 'build-results.json', results)


def report(args):
    out = args.output.resolve(); results = json.loads((out / 'build-results.json').read_text()); comparisons = {}
    for degree in ('doctor', 'bachelor'):
        documents = {r['cell']: pages.pages(str(Path(r['directory']) / 'main.pdf')) for r in results if r['degree'] == degree}
        reference = pages.read_fixture(ROOT / 'tests/reference/word-content' / (degree + '.tsv'))
        comparisons[degree] = {}
        for cell, document in documents.items():
            word = sequence.align(sequence.flatten(reference), sequence.flatten(document))
            host = sequence.align(sequence.flatten(documents['baseline']), sequence.flatten(document))
            value = {'word': word, 'host_baseline': host}
            write_json(out / (degree + '-' + cell + '-comparison.json'), value)
            comparisons[degree][cell] = {'word_summary': word['summary'], 'host_summary': host['summary'],
                                       'exactly_same_text_and_first_line_coordinates_as_host': document == documents['baseline']}
        original = pages.pages(str(out / 'original-sample' / degree / 'main.pdf'))
        comparisons[degree]['production_baseline_reproduced'] = documents['baseline'] == original
        if documents['baseline'] != original: raise ValueError('Unmodified host-font sample did not reproduce production: ' + degree)
    write_json(out / 'comparison-summary.json', comparisons)
    print(json.dumps(comparisons, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'build', 'report'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fonts', type=Path)
    parser.add_argument('--jobs', type=int, default=2)
    args = parser.parse_args()
    if args.action == 'prepare' and args.fonts is None: parser.error('prepare requires --fonts')
    {'prepare': prepare, 'build': build, 'report': report}[args.action](args)


if __name__ == '__main__':
    main()
