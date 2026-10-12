"""Check the three Chinese backends, UTF-8 handling and complete examples."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('variants', ROOT / 'scripts/refresh-desktop-variants.py')
variants = importlib.util.module_from_spec(spec)
spec.loader.exec_module(variants)

def check_backend(recorder, engine):
    inputs = {line[6:] for line in recorder.read_text().splitlines() if line.startswith('INPUT ')}
    names = {Path(p).name for p in inputs}
    required = {
        'lualatex': {'book.cls', 'luatexja.sty'},
        'xelatex': {'book.cls', 'xeCJK.sty', 'ctexhook.sty', 'ctexpatch.sty'},
        'pdflatex': {'ctexbook.cls', 'CJKutf8.sty'},
    }[engine]
    assert required <= names, (engine, required - names)
    assert 'hit-xecjk-hooks.sty' not in names
    if engine != 'pdflatex':
        assert 'ctexbook.cls' not in names and 'ctex.sty' not in names
    if engine == 'lualatex':
        assert not any('/ctex/' in p for p in inputs)

def check(source, work, job, epoch):
    result = variants.build(source, work, job, epoch)
    result.update(engine=job['engine'], name=job['name'])
    if result['status'] != '已更新':
        return result
    recorder = Path(result['pdf']).with_suffix('.fls')
    try:
        check_backend(recorder, job['engine'])
    except AssertionError as error:
        result['status'] = 'dependency failure'
        result['error'] = str(error)
    return result

def check_small(source, work, engine, fallback=False):
    name = engine + ('-fallback' if fallback else '-detail')
    folder = work/name
    shutil.copytree(source, folder)
    shutil.copy2(ROOT/'tests/chinese-backends.tex', folder/'probe.tex')
    (folder/'main.tex').write_text(('\\def\\BackendFallback{1}' if fallback else '') + '\\input{probe.tex}\n')
    with (folder/'compile.log').open('w') as stream:
        for _ in range(2):
            subprocess.run([engine, '-recorder', '-interaction=nonstopmode', '-halt-on-error', 'main.tex'],
                           cwd=folder, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=120)
    check_backend(folder/'main.fls', engine)
    reader = PdfReader(folder/'main.pdf')
    text = ''.join(page.extract_text() for page in reader.pages)
    assert '中文标题测试' in text.replace(' ', '').replace('\n', ''), text
    assert len(reader.pages) == 2
    assert reader.outline[0].title.endswith('中文标题测试'), reader.outline
    log = (folder/'main.log').read_text(errors='replace')
    if fallback:
        assert 'c70gbsn.fd' in log and 'c70zh' not in log
    print(name + ': UTF-8, text, bookmarks, pages and dependencies PASS', flush=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--jobs', type=int, default=6)
    parser.add_argument('--small-only', action='store_true')
    parser.add_argument('--extended', action='store_true', help='Also cover postdoctoral, professional and bachelor variants')
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    source, fingerprint = variants.snapshot(args.work)
    for engine in variants.ENGINE_NAMES:
        check_small(source, args.work, engine)
    check_small(source, args.work, 'pdflatex', fallback=True)
    if args.small_only:
        return
    cases = {
        'doctor': 'stage=final,degree-level=doctor,campus=harbin',
        'bachelor': 'stage=final,degree-level=bachelor,campus=harbin',
        'english': 'stage=final,degree-level=master,campus=shenzhen,lang=en',
        'weihai-proposal': 'stage=proposal,degree-level=master,campus=weihai',
        'shenzhen-proposal': 'stage=proposal,degree-level=master,campus=shenzhen',
        'shenzhen-proposal-en': 'stage=proposal,degree-level=doctor,campus=shenzhen,lang=en',
        'shenzhen-interim': 'stage=interim,degree-level=master,campus=shenzhen',
        'shenzhen-interim-en': 'stage=interim,degree-level=doctor,campus=shenzhen,lang=en',
    }
    if args.extended:
        cases.update({
            'postdoc': 'stage=final,degree-level=postdoc,campus=harbin',
            'professional-doctor': 'stage=final,degree-level=doctor,campus=harbin,degree-type=professional',
            'weihai-bachelor': 'stage=final,degree-level=bachelor,campus=weihai',
            'shenzhen-bachelor-proposal': 'stage=proposal,degree-level=bachelor,campus=shenzhen',
            'shenzhen-bachelor-interim-en': 'stage=interim,degree-level=bachelor,campus=shenzhen,lang=en',
        })
    jobs = [dict(engine=e, name=n, options=o+',fontset=windows')
            for e in variants.ENGINE_NAMES for n, o in cases.items()]
    results = []
    epoch = int(time.time())
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(check, source, args.work, j, epoch) for j in jobs]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f'{len(results)}/{len(jobs)} {result["engine"]}/{result["name"]}: {result["status"]}', flush=True)
            (args.work/'results.json').write_text(json.dumps(dict(source_sha256=fingerprint, results=results), ensure_ascii=False, indent=2))
    failed = [r for r in results if r['status'] != '已更新']
    print(f'PASS {len(results)-len(failed)}/{len(jobs)}', flush=True)
    raise SystemExit(bool(failed))

if __name__ == '__main__':
    main()
