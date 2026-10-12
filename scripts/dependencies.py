"""Install the released wiseref source reproducibly for builds and example bundles."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'build/dependencies'
TEXMF = BASE / 'texmf'
COMMIT = 'a2bf5597726c7e954c81f6afb2cb66b2e9334c49'
URL = f'https://raw.githubusercontent.com/hithesis/wiseref/{COMMIT}/'
HASHES = {
    'wiseref.dtx': 'a9e04396f5e08115284366709fba08da3eb5e1415d9670177d9d8d81011bba4d',
    'wiseref.ins': '39ab345c2031ef4a646a418242314f567f198ff32d4b7bb99a9637b8377e41f2',
    'LICENSE': 'd8ae70a7aa16cdb26d8ceced9fddc2f9b15c12a02b4b7f0206a71ee06c75eeb4',
    'wiseref.sty': '10c1be20c0c28fca6c66200f91cb885a15c7597639ca4d7192d7031632909d2f',
}


def checked(path, name):
    content = path.read_bytes()
    assert hashlib.sha256(content).hexdigest() == HASHES[name], ('Unexpected dependency content', path)
    return content


def install():
    source = BASE / 'source/wiseref'
    source.mkdir(parents=True, exist_ok=True)
    for name in ('wiseref.dtx', 'wiseref.ins', 'LICENSE'):
        target = source / name
        if not target.exists():
            content = subprocess.check_output(['curl', '--fail', '--silent', '--show-error',
                '--location', '--proto', '=https', '--retry', '3', '--max-time', '60',
                URL + name], timeout=250)
            assert hashlib.sha256(content).hexdigest() == HASHES[name], ('Unexpected download', name)
            target.write_bytes(content)
        checked(target, name)
    with (source / 'extract.log').open('w') as output:
        subprocess.run(['xetex', '-interaction=nonstopmode', '-halt-on-error', 'wiseref.ins'],
            cwd=source, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=120)
    checked(source / 'wiseref.sty', 'wiseref.sty')
    destination = TEXMF / 'tex/latex/wiseref'
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / 'wiseref.sty', destination / 'wiseref.sty')
    subprocess.run(['mktexlsr', str(TEXMF)], check=True)
    print(f'wiseref v1.2026a source and generated runtime SHA256: PASS ({COMMIT})')
    print(f'TEXMFLOCAL={TEXMF}')


def payload():
    """Return the unmodified runtime and license for standalone user bundles."""
    source = BASE / 'source/wiseref'
    return {
        'wiseref.sty': checked(TEXMF / 'tex/latex/wiseref/wiseref.sty', 'wiseref.sty'),
        'wiseref-LICENSE': checked(source / 'LICENSE', 'LICENSE'),
    }


def examples():
    files = payload()
    for family in ('hitbook/chinese', 'hitbook/english', 'hitart/reports', 'hitart/reportplus'):
        folder = ROOT / 'examples' / family
        for name in ('wiseref.dtx', 'wiseref.ins'):
            stale = folder / name
            if stale.exists():
                checked(stale, name)
                stale.unlink()
        for name, content in files.items():
            (folder / name).write_bytes(content)
    print('All four example families include verified wiseref runtime and license only')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'examples'))
    args = parser.parse_args()
    globals()[args.action]()
