"""Check class-loaded wiseref defaults and explicit user overrides."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compatibility', ROOT / 'tests/compatibility.py')
compatibility = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compatibility)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    results = []
    for name, cls, options, en in (
        ('book-zh', 'hithesisbook', 'type=master,campus=harbin', False),
        ('book-en', 'hithesisbook', 'type=master,campus=harbin,language=english', True),
        ('art', 'hithesisart', 'type=master,campus=shenzhen,stage=opening', False),
        ('artplus', 'hithesisartplus', 'type=doctor,campus=shenzhen,stage=midterm', False),
        ('book-zh-style', 'hithesisbook', 'type=master,campus=harbin', False),
        ('book-en-style', 'hithesisbook', 'type=master,campus=harbin,language=english', True),
        ('book-zh-preloaded', 'hithesisbook', 'type=master,campus=harbin', False),
        ('book-en-preloaded', 'hithesisbook', 'type=master,campus=harbin,language=english', True),
    ):
        folder = args.work / name
        folder.mkdir()
        for filename in (cls + '.cls', 'hithesisbook.cfg', 'hithesisart.cfg'):
            shutil.copy2(ROOT / filename, folder / filename)
        shutil.copy2(ROOT / 'tests/wiseref.tex', folder / 'fixture.tex')
        text = '\\errorcontextlines=100\n'
        if name.endswith('preloaded'):
            text += '\\RequirePackage{wiseref}\n'
        text += '\\documentclass[fontset=fandol,' + options + ']{' + cls + '}\n'
        text += '\\usepackage{wiseref}\n'
        if cls == 'hithesisbook':
            text += '\\def\\HitBook{1}\n'
        if en:
            text += '\\def\\HitEnglish{1}\n'
        if name.endswith('style'):
            shutil.copy2(ROOT / 'hithesis.sty', folder / 'hithesis.sty')
            text += '\\usepackage{hithesis}\n\\def\\HitStyle{1}\n'
        text += '\\input{fixture.tex}\n'
        (folder / 'main.tex').write_text(text)
        with (folder / 'compile.log').open('w') as output:
            for _ in range(3):
                subprocess.run(['xelatex', '-interaction=nonstopmode', '-halt-on-error',
                    '-recorder', 'main.tex'], cwd=folder,
                    env=os.environ | dict(TEXINPUTS='.:'), stdout=output,
                    stderr=subprocess.STDOUT, check=True, timeout=120)
        pages, links = compatibility.signature(folder / 'main.pdf')
        rendered = ''.join(page[0] for page in pages)
        found = {key: re.sub(r'\s+', '', value) for key, value in
            re.findall(r'CASE-(\w+)-BEGIN(.*?)CASE-\1-END', rendered, re.S)}
        prefix = ('Figure', 'Table', 'Equation') if en else (
            '图', '表', '公式' if cls == 'hithesisbook' else '式')
        for key, expected in zip(('figure', 'table', 'equation'), prefix):
            assert found[key].startswith(expected), (name, key, found)
        assert found['override'].startswith('Photo') and found['star'] == found['override']
        assert found['subfigure'].startswith(prefix[0]), found
        assert found['tagged'] == prefix[2] + '(S)', found
        assert found['bare'] == prefix[2] + 'T', found
        assert found['theorem'].startswith('Theorem' if en else '定理'), found
        assert found['renamed'].startswith('Illustration' if en else '示意图'), found
        assert found['eqoverride'].startswith('Eq.[') and found['bareoverride'] == 'Eq.T', found
        if name.endswith('style'):
            assert found['algorithm'].startswith('算法') and found['listing'].startswith('Listing'), found
        assert links and '\\wiserefRecord{figure}' in (folder / 'main.aux').read_text()
        if cls == 'hithesisbook':
            assert found['chapter'] == ('Chapter1' if en else '第1章'), found
            assert found['appendix'] == ('AppendixA' if en else '附录A'), found
        # A starred reference must have no annotation; ordinary cases must point
        # to an existing named destination (checked by compatibility.signature).
        for key in found:
            marker = 'CASE-' + key + '-BEGIN'
            for page_no, (page_text, boxes) in enumerate(pages):
                at = page_text.find(marker)
                if at >= 0:
                    y = (boxes[at][1] + boxes[at][3]) / 2
                    row_links = [link for link in links if link[0] == page_no and link[1][1] <= y <= link[1][3]]
                    assert bool(row_links) == (key != 'star'), (name, key, row_links)
                    break
            else:
                raise AssertionError(('Missing rendered case', name, key))
        results.append(dict(case=name, status='PASS', references=found, links=len(links)))
        (args.work / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
        print(name, 'PASS', found, flush=True)


if __name__ == '__main__':
    main()
