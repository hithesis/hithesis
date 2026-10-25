"""Check PDF properties and manual overrides, then compare page layout with the baseline."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compatibility', ROOT / 'tests/compatibility.py')
compatibility = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compatibility)

PROFILES = [
    ('book-zh', 'hithesisbook', 'type=doctor',
     r'ctitle={正文标题},ctitlecover={封面\\标题},cauthor={张三},ckeywords={关键词一,关键词二}',
     ('封面 标题', '张三', ['关键词一', '关键词二'])),
    ('book-en', 'hithesisbook', 'type=master,language=english',
     r'ctitle={中文标题},cauthor={张三},etitle={English\\Title},eauthor={Jane Example},ekeywords={alpha,beta}',
     ('English Title', 'Jane Example', ['alpha', 'beta'])),
    ('art', 'hithesisart', 'type=master,stage=opening',
     r'ctitlecover={开题报告标题},cauthor={张三}', ('开题报告标题', '张三', [])),
    ('artplus', 'hithesisartplus', 'type=doctor,campus=shenzhen,stage=midterm',
     r'ctitleone={中期报告},ctitletwo={研究题目},cauthor={张三}', ('中期报告 研究题目', '张三', [])),
]
BODY = r'''\begin{document}
\section{正文}\label{section}
正文与 English text。\ref{section}。
\begin{figure}[htbp]\centering\rule{20mm}{5mm}\caption{图题}\label{figure}\end{figure}
\begin{table}[htbp]\caption{表题}\begin{tabular}{cc}A&B\\1&2\end{tabular}\end{table}
\clearpage 图\ref{figure}。脚注\footnote{脚注内容。}
\end{document}'''


def compact(text):
    return ''.join(str(text).split())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    results = []
    def compile_case(name, cls, options, setup, manual='', runtime=ROOT, package_options=''):
        folder = args.work / name
        folder.mkdir()
        for pattern in ('*.cls', '*.cfg', '*.sty', '*.bst', '*.eps'):
            for path in runtime.glob(pattern):
                shutil.copy2(path, folder / path.name)
        prefix = ('\\PassOptionsToPackage{' + package_options + '}{hyperref}\n') if package_options else ''
        source = prefix + '\\documentclass[fontset=fandol,' + options + ']{' + cls + '}\n'
        source += '\\hitsetup{' + setup + '}\n' + manual + '\n' + BODY
        (folder / 'main.tex').write_text(source)
        env = os.environ | {'TEXINPUTS': str(folder.resolve()) + ':',
                            'TEXMFLOCAL': str(ROOT / 'build/dependencies/texmf'),
                            'SOURCE_DATE_EPOCH': '1700000000', 'FORCE_SOURCE_DATE': '1'}
        with (folder / 'compile.log').open('w') as output:
            for _ in range(3):
                subprocess.run(['xelatex', '-no-shell-escape', '-recorder', '-interaction=nonstopmode',
                    '-halt-on-error', 'main.tex'], cwd=folder, env=env,
                    stdout=output, stderr=subprocess.STDOUT, check=True, timeout=180)
        log = (folder / 'main.log').read_text()
        assert 'undefined references' not in log and 'Missing character:' not in log, name
        assert 'Token not allowed in a PDF string' not in log, name
        pdf = folder / 'main.pdf'
        properties = PdfReader(pdf).metadata
        results.append({'case': name, 'title': str(properties.get('/Title', '')),
                        'author': str(properties.get('/Author', '')),
                        'keywords': str(properties.get('/Keywords', '')), 'status': 'PASS'})
        return pdf, properties
    for name, cls, options, setup, expected in PROFILES:
        pdf, properties = compile_case(name, cls, options, setup)
        assert compact(properties.get('/Title', '')) == compact(expected[0]), (name, properties)
        assert properties.get('/Author', '') == expected[1], (name, properties)
        assert all(word in properties.get('/Keywords', '') for word in expected[2]), (name, properties)
        if args.baseline:
            old, _ = compile_case(name + '-baseline', cls, options, setup, runtime=args.baseline)
            assert compatibility.signature(old) == compatibility.signature(pdf), (name, 'Page text/geometry/links changed')
        _, overridden = compile_case(name + '-manual', cls, options, setup,
            r'\hypersetup{pdftitle={Manual title},pdfauthor={},pdfkeywords={}}')
        assert overridden.get('/Title') == 'Manual title' and overridden.get('/Author', '') == ''
        assert overridden.get('/Keywords', '') == '', (name, overridden)
        _, nested = compile_case(name + '-pdfinfo', cls, options, setup,
            r'\hypersetup{pdfinfo={Author={Manual author},Keywords={manual-keyword}}}')
        assert compact(nested.get('/Title', '')) == compact(expected[0]), (name, nested)
        assert nested.get('/Author') == 'Manual author' and nested.get('/Keywords') == 'manual-keyword'
        _, package = compile_case(name + '-package', cls, options, setup,
            package_options='pdftitle={Package title},pdfauthor={Package author}')
        assert package.get('/Title') == 'Package title' and package.get('/Author') == 'Package author', (name, package)
    _, blank = compile_case('blank-fields', 'hithesisbook', 'type=doctor', '')
    assert blank.get('/Title', '') == blank.get('/Author', '') == blank.get('/Keywords', '') == ''
    (args.work / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print('PDF metadata and unchanged visible layout:', len(results), 'PASS')


if __name__ == '__main__':
    main()
