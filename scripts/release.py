"""Prepare source-only l3build inputs and verify maintenance release artifacts."""
import argparse
import hashlib
import io
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import zipfile

import dependencies

ROOT = Path(__file__).resolve().parents[1]
VERSION_PATTERN = r'\\ProvidesFile\{hithesis\.dtx\}\[([^ ]+) ([^ ]+) '
EXPL_VERSION_PATTERN = (r'\\ProvidesExpl(?:Class|File|Package)\{[^}]+\}'
    r'\{(\d{4}/\d{2}/\d{2})\}\{v([^}]+)\}')


def source_copy(source, target):
    if source.suffix in ('.dtx', '.ins', '.tex', '.bib', '.bst', '.md'):
        content = source.read_text(encoding='utf-8-sig')
        target.write_text(content, encoding='utf-8', newline='\n')
    else:
        shutil.copy2(source, target)


def version():
    source = (ROOT / 'hithesis.dtx').read_text(encoding='utf-8')
    match = re.search(VERSION_PATTERN, source)
    assert match, 'Missing package version'
    date, number = match.groups()
    assert re.fullmatch(r'\d{4}/\d{2}/\d{2}', date)
    banners = re.findall(EXPL_VERSION_PATTERN, source)
    assert len(banners) == 6, 'Missing runtime version declarations'
    assert banners and all(item == (date, number) for item in banners)
    return number, date


def stage():
    destination = ROOT / 'build/release-source'
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    for name in ('hithesis.dtx', 'hithesis.ins', 'README.md'):
        source_copy(ROOT / name, destination / name)
    for path in (ROOT / 'examples').rglob('*'):
        if path.name.startswith('wiseref'):
            continue
        if path.is_file() and (path.suffix in ('.tex', '.bib') or
                path.name in ('empty-resolution.pdf', 'gbt7714-numerical-quanjiao.bst')):
            target = destination / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            source_copy(path, target)
    # docstrip writes to all four legacy example folders.
    for directory in ('hitbook/chinese/figures', 'hitbook/english/figures',
            'hitart/reports/figures', 'hitart/reportplus/figures'):
        (destination / 'examples' / directory).mkdir(parents=True, exist_ok=True)


def baseline(destination, ref):
    destination.mkdir(parents=True, exist_ok=False)
    # Docker runs as root while the mounted checkout belongs to the host user.
    # Trust only this checkout for this command, without writing Git config.
    archive = subprocess.check_output(
        ['git', '-c', f'safe.directory={ROOT}', 'archive', ref], cwd=ROOT)
    with tarfile.open(fileobj=io.BytesIO(archive)) as package:
        package.extractall(destination, filter='data')
    subprocess.run(['xetex', '-interaction=batchmode', '-halt-on-error', 'hithesis.ins'],
        cwd=destination, check=True)
    if ref != 'v3.1e':
        subprocess.run(['make', 'examples'], cwd=destination, check=True)


def notes():
    number, date = version()
    source = (ROOT / 'hithesis.dtx').read_text(encoding='utf-8')
    entries = re.findall(r'\\changes\{v' + re.escape(number) + r'\}\{([^}]+)\}\{([^}]+)\}', source)
    assert entries, 'Missing current-version change entries'
    text = f'## v{number}\n\nThis release of hithesis (the Harbin Institute of Technology thesis\n'
    text += 'template for all three campuses) includes the following changes:\n\n'
    text += ''.join(f'- {entry} ({when})\n' for when, entry in entries)
    (ROOT / 'RELEASE_NOTES.md').write_text(text, encoding='utf-8')
    print('v' + number)


def verify():
    number, date = version()
    required = {
        'tex/latex/hithesis/hithesisbook.cls',
        'tex/latex/hithesis/hithesisart.cls',
        'tex/latex/hithesis/hithesisartplus.cls',
        'tex/latex/hithesis/hithesisbook.cfg',
        'tex/latex/hithesis/hithesisart.cfg',
        'tex/latex/hithesis/hithesis.sty',
        'tex/latex/hithesis/hithesis-logo.eps',
        'tex/latex/hithesis/hithesis-bthesistitle.eps',
        'tex/latex/hithesis/hithesis-shenzhenbthesistitle.eps',
        'tex/latex/hithesis/hithesis-hrb-bachelor-bottommark.eps',
        'tex/latex/hithesis/hithesis-golfer.eps',
        'tex/latex/hithesis/hithesis-zfb.eps',
        'bibtex/bst/hithesis/hithesis.bst',
        'bibtex/bst/hithesis/hitszthesis.bst',
        'makeindex/hithesis/hithesis.ist',
        'source/latex/hithesis/hithesis.dtx',
        'source/latex/hithesis/hithesis.ins',
        'doc/latex/hithesis/hithesis.pdf',
    }
    with zipfile.ZipFile(ROOT / 'hithesis.tds.zip') as archive:
        names = set(archive.namelist())
        assert required <= names, ('Missing TDS files', sorted(required - names))
        assert 'tex/latex/hithesis/dtx-style.sty' not in names
        for name in names:
            assert not Path(name).name.startswith('wiseref'), ('Bundled dependency in CTAN/TDS', name)
            assert not name.startswith('/') and '..' not in Path(name).parts
            if '/examples/' in name:
                assert name.endswith('/') or Path(name).suffix in ('.tex', '.bib', '.bst', '.pdf')
            if name.endswith(('.cls', '.cfg', '/hithesis.sty')):
                assert re.findall(EXPL_VERSION_PATTERN, archive.read(name).decode()) == [
                    (date, number)], ('Stale version', name)
    with zipfile.ZipFile(ROOT / 'hithesis-ctan.zip') as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), 'Duplicate archive members'
        assert 'hithesis.tds.zip' in names, 'Missing bundled TDS archive'
        assert 'hithesis/hithesis.dtx' in names and 'hithesis/hithesis.pdf' in names
        for name in names:
            assert not Path(name).name.startswith('wiseref'), ('Bundled dependency in CTAN', name)
            assert not any(part.startswith('.') for part in Path(name).parts), ('Hidden payload', name)
            assert not name.endswith(('.aux', '.log', '.fls', '.cls', '.cfg', '.sty'))
            if Path(name).suffix in ('.dtx', '.ins', '.tex', '.bib', '.bst', '.md'):
                content = archive.read(name)
                assert not content.startswith(b'\xef\xbb\xbf') and b'\r' not in content, ('Invalid text format', name)
                content.decode('utf-8')
        assert archive.read('hithesis/hithesis.dtx') == (ROOT / 'hithesis.dtx').read_bytes()
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    checksums = []
    for name in ('hithesis-ctan.zip', 'hithesis.tds.zip'):
        shutil.copy2(ROOT / name, destination / name)
    for path in sorted(destination.glob('*.zip')):
        if path.name not in ('hithesis-ctan.zip', 'hithesis.tds.zip'):
            with zipfile.ZipFile(path) as archive:
                assert not any(Path(name).name in ('wiseref.dtx', 'wiseref.ins')
                    for name in archive.namelist()), ('Dependency sources in user archive', path)
                roots = {Path(name).parent.as_posix() for name in archive.namelist()
                    if name.endswith('.cls')}
                assert roots, ('Missing standalone class', path)
                for prefix in roots:
                    for filename, content in dependencies.payload().items():
                        assert archive.read(prefix + '/' + filename) == content, (
                            'Missing or stale standalone dependency', path, prefix, filename)
        checksums.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name)
    (destination / 'SHA256SUMS').write_text('\n'.join(checksums) + '\n')
    print('CTAN/TDS contents, versions and source provenance: PASS')


def examples():
    number, _ = version()
    destination = ROOT / 'dist'
    destination.mkdir(exist_ok=True)
    configurations = []
    for language in ('chinese', 'english'):
        for campus in ('shenzhen', 'weihai', 'harbin'):
            for degree in ('doctor', 'master', 'bachelor', 'postdoc'):
                configurations.append((f'{language}-{campus}-{degree}',
                    f'hitbook/{language}', 'thesis.tex', degree, campus, None))
    for campus in ('shenzhen', 'weihai', 'harbin'):
        for degree in ('doctor', 'master', 'bachelor'):
            for stage_name in ('opening', 'midterm'):
                if (campus, degree, stage_name) == ('shenzhen', 'doctor', 'midterm'):
                    continue
                configurations.append((f'reports-{campus}-{degree}-{stage_name}',
                    'hitart/reports', 'report.tex', degree, campus, stage_name))
    configurations.append(('reportplus-shenzhen-doctor-midterm',
        'hitart/reportplus', 'report.tex', 'doctor', 'shenzhen', 'midterm'))
    assert len(configurations) == 42
    runtime = {
        'hitbook': ('hithesisbook.cls', 'hithesisbook.cfg', 'hithesis.sty', 'hithesis.ist'),
        'reports': ('hithesisart.cls', 'hithesisart.cfg'),
        'reportplus': ('hithesisartplus.cls', 'hithesisart.cfg'),
    }
    common = ('hithesis.bst', 'hitszthesis.bst', 'hithesis-logo.eps', 'hithesis-bthesistitle.eps',
        'hithesis-shenzhenbthesistitle.eps', 'hithesis-zfb.eps', 'hithesis-hrb-bachelor-bottommark.eps')
    sums = []
    with zipfile.ZipFile(destination / 'hithesis-examples.zip', 'w', zipfile.ZIP_DEFLATED) as combined:
        for name, source, main, degree, campus, stage_name in configurations:
            prefix = f'{name}-v{number}'
            payload = {}
            for path in (ROOT / 'examples' / source).rglob('*'):
                if path.is_file() and (path.suffix in ('.tex', '.bib') or path.name in
                        ('Makefile', 'latexmkrc', 'empty-resolution.pdf', 'gbt7714-numerical-quanjiao.bst')):
                    payload[path.relative_to(ROOT / 'examples' / source).as_posix()] = path.read_bytes()
            main_text = payload[main].decode('utf-8')
            for key, value in (('type', degree), ('campus', campus), ('stage', stage_name)):
                if value is not None:
                    main_text, count = re.subn(rf'{key}=[^\],}}\n]*', f'{key}={value}', main_text, count=1)
                    assert count == 1, ('Missing example option', source, key)
            payload[main] = main_text.encode('utf-8')
            family = 'hitbook' if source.startswith('hitbook/') else source.split('/')[1]
            payload.update(dependencies.payload())
            for filename in runtime[family] + common:
                payload[filename] = (ROOT / filename).read_bytes()
            payload['figures/hithesis-golfer.eps'] = (ROOT / 'hithesis-golfer.eps').read_bytes()
            with zipfile.ZipFile(destination / f'{name}.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
                for filename, content in sorted(payload.items()):
                    archive.writestr(f'{prefix}/{filename}', content)
                    combined.writestr(f'hithesis-examples/{prefix}/{filename}', content)
    for path in sorted(destination.glob('*.zip')):
        sums.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name)
    (destination / 'SHA256SUMS').write_text('\n'.join(sums) + '\n')
    print('Standalone example archives: 42 variants plus one combined archive')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('stage', 'baseline', 'version', 'notes', 'verify', 'examples'))
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--ref', default='v3.1e')
    args = parser.parse_args()
    if args.action == 'baseline':
        if not args.destination:
            parser.error('baseline requires --destination')
        baseline(args.destination, args.ref)
    elif args.action == 'version':
        print('v' + version()[0])
    else:
        globals()[args.action]()


if __name__ == '__main__':
    main()
