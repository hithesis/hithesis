#!/usr/bin/env python3
"""Freeze verified Word exports as text fixtures, or check the independent sequence gate."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('word_page_diagnostics', Path(__file__).with_name('diagnose-pages.py'))
diagnostics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostics)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def member(directory, name):
    if not name or Path(name).name != name or name in ('.', '..'):
        raise ValueError('Expected a plain file name: ' + str(name))
    return directory / name


def verified_bundle(prepared, exported, repo=ROOT):
    inputs = read_json(prepared / 'inputs.json')
    report = read_json(exported / 'verified-export.json')
    fonts = read_json(exported / 'fonts.json')
    if inputs.get('kind') != 'hithesis-content-aligned-word-inputs' or report.get('kind') != 'actual-windows-word-com-export':
        raise ValueError('Expected prepared inputs and an actual Windows Word export')
    checks = [(prepared / 'inputs.json', report['input_manifest_sha256']),
              (exported / 'fonts.json', report['font_record_sha256']),
              (repo / 'tests/reference/word-fonts.json', fonts['source_record_sha256']),
              (repo / 'tests/reference/word-reference-sources.json', inputs['seed_manifest_sha256']),
              (repo / 'scripts/word-reference.py', inputs['generator_sha256']),
              (repo / 'scripts/export-word-reference.py', report['exporter_sha256'])]
    expected_fonts = read_json(repo / 'tests/reference/word-fonts.json')['files']
    if fonts['files'] != expected_fonts:
        raise ValueError('Export font hashes differ from the approved font record')
    records = {e['name']: e for e in report['inputs']}
    if len(records) != len(report['inputs']) or set(records) != {d['name'] for d in inputs['documents']}:
        raise ValueError('Word export has duplicate or missing document records')
    if Counter(d['degree'] for d in inputs['documents']) != {'doctor': 1, 'bachelor': 1}:
        raise ValueError('Expected one doctor and one bachelor document')
    for d in inputs['documents']:
        if records[d['name']]['input_sha256'] != d['sha256']:
            raise ValueError('Word input hash differs from the prepared manifest')
        profile_file = member(prepared, d['content_profile'])
        checks += [(member(prepared, d['file']), d['sha256']), (profile_file, d['content_profile_sha256']),
                   (member(exported, d['name'] + '.pdf'), records[d['name']]['pdf_sha256'])]
        for path, expected in read_json(profile_file)['latex_sources'].items():
            source = (repo / path).resolve()
            if not source.is_relative_to(repo.resolve()):
                raise ValueError('Source path escapes the repository')
            checks.append((source, expected))
    for path, expected in checks:
        if digest(path) != expected:
            raise ValueError('Provenance hash mismatch: ' + str(path))
    return inputs, report, fonts


def fixture_text(document, name):
    lines = ['# Windows Word content-aligned reference; independent of historical pages-*.tsv',
             '# Source: ' + name + '; provenance and coverage: manifest.json']
    for i, page in enumerate(document, 1):
        lines.append('PAGE\t' + str(i))
        lines += [f'LINE\t{y:.2f}\t{x:.3f}\t{text}' for y, x, text in page]
    return '\n'.join(lines) + '\n'


def freeze(args):
    inputs, report, fonts = verified_bundle(args.prepared, args.exported)
    if args.output.exists():
        raise FileExistsError('Fixture directory already exists: ' + str(args.output))
    texts = {}; documents = {}
    for d in inputs['documents']:
        pdf = args.exported / (d['name'] + '.pdf')
        document = diagnostics.pages.pages(str(pdf))
        entry = next(e for e in report['inputs'] if e['name'] == d['name'])
        if len(document) != entry['pages']:
            raise ValueError('PDF page count differs from the actual Word export')
        filename = d['degree'] + '.tsv'
        texts[filename] = fixture_text(document, pdf.name)
        documents[d['degree']] = {'fixture': filename, 'fixture_sha256': hashlib.sha256(texts[filename].encode()).hexdigest(),
                                  'word_input_sha256': d['sha256'], 'word_pdf_sha256': entry['pdf_sha256'],
                                  'word_pages': len(document), 'content_profile': read_json(args.prepared / d['content_profile']),
                                  'changes': d['changes']}
    # Freeze only Word evidence here. Ratchet thresholds are reviewed separately;
    # this command never derives an acceptance threshold from the current LaTeX PDF.
    manifest = {'schema': 1, 'kind': 'hithesis-word-content-text-fixtures',
                'documents': documents, 'word_export': report, 'font_record': fonts,
                'prepared_manifest_sha256': digest(args.prepared / 'inputs.json'),
                'seed_manifest_sha256': inputs['seed_manifest_sha256'],
                'generator_sha256': inputs['generator_sha256'], 'freezer_sha256': digest(__file__),
                'coverage': inputs['coverage'], 'retained_differences': inputs['retained_differences'],
                'comparison': 'monotone one-to-one; only non-ambiguous exact full lines count; vertical tolerance 0.5bp'}
    args.output.mkdir(parents=True, exist_ok=False)
    for name, value in texts.items():
        (args.output / name).write_text(value, encoding='utf-8')
    (args.output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Frozen actual Word text fixtures:', args.output)


def evaluate(reference, actual, minimum, tolerance=0.5):
    report = diagnostics.align(reference, actual, tolerance)
    count = report['summary']['unique_exact_within_tolerance']
    report['gate'] = {'metric': 'unique_exact_within_tolerance', 'minimum': minimum,
                      'actual': count, 'passed': count >= minimum,
                      'excludes': ['ambiguous duplicate matches', 'prefix-only matches', 'short formula fragments']}
    return report


def check(args):
    manifest = read_json(args.reference / 'manifest.json')
    if manifest.get('kind') != 'hithesis-word-content-text-fixtures':
        raise ValueError('Expected independent Word content text fixtures')
    d = manifest['documents'][args.degree]
    fixture = member(args.reference, d['fixture'])
    if digest(fixture) != d['fixture_sha256']:
        raise ValueError('Frozen fixture hash mismatch')
    report = evaluate(diagnostics.flatten(diagnostics.pages.read_fixture(fixture)),
                      diagnostics.flatten(diagnostics.pages.pages(str(args.pdf))), args.min_ok)
    report['inputs'] = {'fixture': str(fixture), 'fixture_sha256': digest(fixture),
                        'pdf': str(args.pdf), 'pdf_sha256': digest(args.pdf),
                        'reference_manifest_sha256': digest(args.reference / 'manifest.json')}
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    diagnostics.print_report(report)
    print('独立顺序棘轮:', json.dumps(report['gate'], ensure_ascii=False))
    return 0 if report['gate']['passed'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    p = subs.add_parser('freeze')
    p.add_argument('--prepared', type=Path, required=True)
    p.add_argument('--exported', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = subs.add_parser('check')
    p.add_argument('--reference', type=Path, default=ROOT / 'tests/reference/word-content')
    p.add_argument('--degree', choices=('doctor', 'bachelor'), required=True)
    p.add_argument('--pdf', type=Path, required=True)
    p.add_argument('--min-ok', type=int, required=True)
    p.add_argument('--json', type=Path)
    args = parser.parse_args()
    if args.command == 'check' and args.min_ok <= 0:
        parser.error('--min-ok must be positive')
    return check(args) if args.command == 'check' else freeze(args)


if __name__ == '__main__':
    sys.exit(main())
