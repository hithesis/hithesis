"""Check symbols column widths, eqdenote page breaks and URL spacing in bibliographies."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pypdfium2 as pdfium
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PROFILES = [('book', 'hithesisbook', 'type=doctor'),
            ('english', 'hithesisbook', 'type=master,language=english'),
            ('art', 'hithesisart', 'type=master,stage=opening'),
            ('artplus', 'hithesisartplus', 'type=doctor,campus=shenzhen,stage=midterm')]


def pdf_text(folder):
    pages = []
    with pdfium.PdfDocument(folder / 'main.pdf') as pdf:
        for page in pdf:
            text = page.get_textpage()
            pages.append(text.get_text_range())
            text.close()
            page.close()
    return pages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    results = []

    def compile_case(name, cls, options, body, preamble='', success=True, error_text='Each eqdenote entry'):
        folder = args.work / name
        folder.mkdir()
        for pattern in ('*.cls', '*.cfg', '*.sty', '*.bst', '*.eps'):
            for path in ROOT.glob(pattern):
                shutil.copy2(path, folder / path.name)
        source = (r'\errorcontextlines=100' + '\n' +
                  '\\documentclass[fontset=fandol,' + options + ']{' + cls + '}\n' +
                  preamble + '\n\\begin{document}\n' + body + '\n\\end{document}\n')
        (folder / 'main.tex').write_text(source)
        env = os.environ | {'TEXINPUTS': str(folder.resolve()) + ':',
            'TEXMFLOCAL': str(ROOT / 'build/dependencies/texmf'),
            'SOURCE_DATE_EPOCH': '1699964000', 'FORCE_SOURCE_DATE': '1', 'TZ': 'UTC'}
        with (folder / 'compile.log').open('w') as output:
            for _ in range(3 if success else 1):
                process = subprocess.run(['xelatex', '-no-shell-escape', '-interaction=nonstopmode',
                    '-halt-on-error', '-recorder', 'main.tex'], cwd=folder, env=env,
                    stdout=output, stderr=subprocess.STDOUT, timeout=180)
                if success and process.returncode:
                    raise AssertionError(f'{name}: compile failed; see {folder / "compile.log"}')
        log = (folder / 'main.log').read_text(errors='replace')
        if not success:
            assert process.returncode and error_text in log, (name, log)
            results.append({'case': name, 'status': 'PASS', 'expected_error': True})
            return folder, log
        for diagnostic in ('Missing character:', 'multiply defined', 'undefined references',
                           'destination with the same identifier', 'Overfull \\hbox'):
            assert diagnostic not in log, (name, diagnostic)
        assert 'docxlike.sty' not in (folder / 'main.fls').read_text()
        results.append({'case': name, 'status': 'PASS'})
        return folder, log

    # Check URL glue before, inside and after gbt7714/natbib bibliographies.
    for profile, cls, options in PROFILES:
        for setting in ('default', 'custom'):
            preamble = '' if setting == 'default' else r'\Urlmuskip=0mu plus 1mu\relax'
            body = r'''\typeout{URL-BEFORE=\the\Urlmuskip}
Normal paragraph before URL.
\begin{minipage}{55mm}\url{https://example.org/path_with_segments/file?key=value&next=item#anchor}\end{minipage}
\begin{thebibliography}{1}
\typeout{URL-BIB=\the\Urlmuskip}
\bibitem{web} Web. \url{https://example.org/path_with_segments/file?key=value&next=item#anchor}.
\end{thebibliography}
\typeout{URL-AFTER=\the\Urlmuskip}
Normal paragraph after URL.'''
            folder, log = compile_case(profile + '-url-' + setting, cls, options, body, preamble)
            values = re.findall(r'URL-(?:BEFORE|BIB|AFTER)=([^\n]+)', log)
            expected = '0.0mu' if setting == 'default' else '0.0mu plus 1.0mu'
            assert values == [expected] * 3, (profile, setting, values)
            links = [str(a.get_object().get('/A', {}).get('/URI', ''))
                     for page in PdfReader(folder / 'main.pdf').pages for a in page.get('/Annots', [])]
            target = 'https://example.org/path_with_segments/file?key=value&next=item#anchor'
            assert links.count(target) >= 2, (profile, setting, links)

    # Discarded width trials must leave counters and auxiliary labels unchanged.
    symbol_body = r'''\item[$x$] First symbol.\stepcounter{TrialCounter}\label{sym:first}
\typeout{SYMBOL-WIDTH=\the\labelwidth}
\item[LongSymbolLabel] A longer symbol with a short explanation.
\item[$\rho$] Density, kg/m$^3$.\footnote{A symbol footnote.}
'''
    preamble = r'\newcounter{TrialCounter}'
    for profile, cls, options in PROFILES[:2]:
        for setting in ('default', '3cm'):
            optional = '' if setting == 'default' else '[' + setting + ']'
            body = ('\\begin{symbols}' + optional + '\n' + symbol_body +
                    '\\end{symbols}\n' + r'\typeout{TRIAL-COUNTER=\arabic{TrialCounter}}' + '\n' +
                    r'\typeout{FOOTNOTE-COUNTER=\arabic{footnote}}' + '\n' + r'See \ref{sym:first}.')
            folder, log = compile_case(profile + '-symbols-' + setting.replace('=', '-'),
                                       cls, options, body, preamble)
            assert 'TRIAL-COUNTER=1' in log and 'FOOTNOTE-COUNTER=1' in log, log
            labels = (folder / 'main.aux').read_text().count(r'\newlabel{sym:first}')
            assert labels == 1, (profile, setting, labels)
            widths = [float(n) for n in re.findall(r'SYMBOL-WIDTH=([\d.]+)pt', log)]
            if setting == 'default':
                assert widths[-1] > 71.14, widths  # wider than the 2.5 cm minimum
            else:
                assert abs(widths[-1] - 85.35826) < .001, widths
            text = ''.join(pdf_text(folder))
            assert text.count('A symbol footnote.') == 1, (profile, setting, text)

    for name, setting in [('auto', 'auto'), ('key-value', 'labelwidth=3cm')]:
        compile_case('symbols-error-' + name, 'hithesisbook', 'type=master',
                     '\\begin{symbols}[' + setting + ']\\item[$x$] Symbol.\\end{symbols}',
                     success=False, error_text='Missing number')

    for profile, cls, options in PROFILES:
        rows = '\n'.join(r'\item $x_{' + str(i) + '}$ & EntryMark' + f'{i:03}' +
            r': an explanation with enough words to exercise aligned wrapping in the final column.'
            for i in range(90))
        body = r'''\setcounter{table}{7}
\begin{equation}\label{eq:force} F=ma \end{equation}
\begin{eqdenote}
\item $F$ & Force in N.
\item $m$ & Mass in kg.
\end{eqdenote}
\ExplSyntaxOn\iow_term:e{EQ-WIDTH-A=\dim_use:N\g__hit_eqdenote_sym_dim}\ExplSyntaxOff
\begin{eqdenote}[]
\item $a$ & Acceleration in m/s$^2$.
\end{eqdenote}
\ExplSyntaxOn\iow_term:e{EQ-WIDTH-B=\dim_use:N\g__hit_eqdenote_sym_dim}\ExplSyntaxOff
\begin{eqdenote}[Note]
''' + rows + r'''
\end{eqdenote}
\typeout{EQ-TABLE-COUNTER=\arabic{table}}
\typeout{EQ-EQUATION-COUNTER=\arabic{equation}}
Equation reference: \ref{eq:force}. AFTERMARK.
'''
        folder, log = compile_case(profile + '-eqdenote', cls, options, body)
        assert 'EQ-TABLE-COUNTER=7' in log and 'EQ-EQUATION-COUNTER=1' in log, log
        assert re.search(r'EQ-WIDTH-A=([^\n]+)', log)[1] == re.search(r'EQ-WIDTH-B=([^\n]+)', log)[1]
        pages = pdf_text(folder)
        text = ''.join(pages)
        assert len(pages) >= 3, (profile, len(pages))
        for index in range(90):
            assert text.count(f'EntryMark{index:03}') == 1, (profile, index)
        assert 'AFTERMARK' in text and '续表' not in text and 'Continued' not in text
        assert ('where' if profile == 'english' else '式中') in text, (profile, text)
        auxiliary = (folder / 'main.aux').read_text()
        assert not re.search(r'\@writefile\{lot\}', auxiliary), auxiliary

    for name, body in [('empty', ''), ('missing-item', '$x$ & explanation'),
                       ('missing-ampersand', r'\item $x$ explanation')]:
        compile_case('eqdenote-error-' + name, 'hithesisbook', 'type=master',
                     '\\begin{eqdenote}\n' + body + '\n\\end{eqdenote}', success=False)
    (args.work / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(f'Symbols, eqdenote and URL bibliography settings: {len(results)} cases PASS')


if __name__ == '__main__':
    main()
