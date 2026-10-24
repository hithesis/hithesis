"""Exercise the dev backports through PDF geometry, link targets and label/list data."""
import argparse
import ctypes
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pypdfium2 as pdfium
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('compatibility', ROOT / 'tests/compatibility.py')
compatibility = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compatibility)


def pdf_lines(path):
    pages = []
    with pdfium.PdfDocument(path) as document:
        for page in document:
            text = page.get_textpage()
            rows = {}
            for index in range(text.count_chars()):
                char = text.get_text_range(index, 1)
                if not char.strip():
                    continue
                x, y = ctypes.c_double(), ctypes.c_double()
                assert pdfium.raw.FPDFText_GetCharOrigin(text.raw, index, ctypes.byref(x), ctypes.byref(y))
                rows.setdefault(round(y.value, 1), []).append((x.value, char))
            pages.append([(y, round(min(x for x, _ in chars), 3),
                ''.join(c for _, c in sorted(chars, key=lambda pair: pair[0])))
                for y, chars in sorted(rows.items(), reverse=True)])
            text.close()
            page.close()
    return pages


def number(aux, key):
    match = re.search(r'\\newlabel\{' + re.escape(key) + r'\}\{\{([^}]*)\}', aux)
    return match.group(1) if match else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT / 'build' /
        ('small-features-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f')))
    parser.add_argument('--baseline', type=Path, help='Optional pre-backport runtime for geometry comparisons')
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    results = []

    def compile_case(name, source, runtime=ROOT):
        folder = args.work / name
        folder.mkdir()
        for suffix in ('*.cls', '*.cfg', '*.sty', '*.bst', '*.ist', '*.eps'):
            for path in runtime.glob(suffix):
                shutil.copy2(path, folder / path.name)
        (folder / 'main.tex').write_text(source)
        environment = os.environ | {'TEXINPUTS': str(folder) + ':',
            'TEXMFLOCAL': str(ROOT / 'build/dependencies/texmf'),
            'SOURCE_DATE_EPOCH': '1700000000', 'FORCE_SOURCE_DATE': '1'}
        with (folder / 'compile.log').open('w') as output:
            for _ in range(3):
                subprocess.run(['xelatex', '-no-shell-escape', '-interaction=nonstopmode',
                    '-halt-on-error', '-recorder', 'main.tex'], cwd=folder, env=environment,
                    stdout=output, stderr=subprocess.STDOUT, check=True, timeout=180)
        log = (folder / 'main.log').read_text()
        assert 'undefined references' not in log and 'Missing character:' not in log, name
        assert 'docxlike.sty' not in (folder / 'main.fls').read_text(), name
        pages = pdf_lines(folder / 'main.pdf')
        results.append({'case': name, 'pages': len(pages), 'status': 'PASS',
            'pdf_sha256': hashlib.sha256((folder / 'main.pdf').read_bytes()).hexdigest()})
        return folder, pages, log

    keywords = r'''\documentclass[fontset=fandol,type=doctor OPTIONS]{hithesisbook}
CONTROL
\begin{document}\ExplSyntaxOn
\group_begin:\hsize=170bp\relax
\cs_if_exist:NTF \__hit_keywords_typeset:nn
  {\__hit_keywords_typeset:nn}{\use:c{hit@put@keywords}}
  {Keywords:~}{Alpha~Beta~Gamma~Delta~Epsilon~Zeta~Eta~Theta~Iota~Kappa~Lambda~Mu~Nu~Xi~Omicron~Pi~Rho~Sigma~Tau~Upsilon~Phi~Chi~Psi~Omega}
\group_end:\ExplSyntaxOff\end{document}'''
    keyword_pages = {}
    for name, options, control, hanging in [
        ('keywords-default', '', '', False),
        ('keywords-explicit-false', ',keywords-hanging=false', '', False),
        ('keywords-class-true', ',keywords-hanging=true', '', True),
        ('keywords-runtime-true', '', r'\hitsetup{keywords-hanging=true}', True),
        ('keywords-bare-key', ',keywords-hanging', '', True),
    ]:
        _, pages, _ = compile_case(name, keywords.replace('OPTIONS', options).replace('CONTROL', control))
        rows = [row for page in pages for row in page]
        first = next(i for i, row in enumerate(rows) if row[2].startswith('Keywords:'))
        delta = rows[first + 1][1] - rows[first][1]
        assert delta > 20 if hanging else abs(delta) < .01, (name, delta)
        keyword_pages[name] = pages
    assert keyword_pages['keywords-default'] == keyword_pages['keywords-explicit-false']
    if args.baseline:
        old_folder, pages, _ = compile_case('keywords-old-default', keywords.replace('OPTIONS', '').replace('CONTROL', ''), args.baseline)
        assert pages == keyword_pages['keywords-class-true']
        assert compatibility.signature(old_folder / 'main.pdf') == compatibility.signature(
            args.work / 'keywords-class-true/main.pdf')

    dates = r'''\documentclass[fontset=fandol,OPTIONS]{CLASS}
\hitsetup{cdate={2026-06}}
\begin{document}\ExplSyntaxOn
ZH:\__hit_date_use:nV{zh}\g__hit_info_cdate_tl\par
EN:\__hit_date_use:nn{en}{2026-06-15}\par
YEAR:\__hit_date_use:nn{zh}{2026}\par
LEAP:\__hit_date_use:nn{zh}{2024-02-29}\par
CENTURY:\__hit_date_use:nn{zh}{2000-02-29}\par
INVALID:\__hit_date_use:nn{zh}{2026-02-29}\par
BADMONTH:\__hit_date_use:nn{zh}{2026-13}\par
LEGACY:\__hit_date_use:nn{zh}{二〇二六年六月}\par
COMMAND:\__hit_date_use:nn{zh}{\textbf{ManualDate}}\par
\iow_term:x{RAW-DATE=\tl_to_str:V\g__hit_info_cdate_tl}
EXTRA
\ExplSyntaxOff\end{document}'''
    classes = [('book', 'hithesisbook', 'type=doctor'),
        ('art', 'hithesisart', 'type=master,stage=opening'),
        ('artplus', 'hithesisartplus', 'type=doctor,campus=shenzhen,stage=midterm')]
    for name, cls, options in classes:
        extra = r'FIRST:\__hit_date_use:nV{zh}\g__hit_info_firstpagecdate_tl\par' if cls == 'hithesisbook' else ''
        _, pages, log = compile_case('date-' + name, dates.replace('CLASS', cls).replace('OPTIONS', options).replace('EXTRA', extra))
        text = '\n'.join(row[2] for page in pages for row in page)
        for expected in ['ZH:2026年6月', 'EN:June15,2026', 'YEAR:2026年', 'LEAP:2024年2月29日',
            'CENTURY:2000年2月29日', 'INVALID:2026-02-29', 'BADMONTH:2026-13', 'LEGACY:二〇二六年六月', 'COMMAND:ManualDate']:
            assert expected in text, (name, expected, text)
        assert 'RAW-DATE=2026-06' in log
        if extra:
            assert 'FIRST:2026年6月' in text

    anchors = r'''\documentclass[fontset=fandol,OPTIONS]{CLASS}
CONTROL
\begin{document}\begin{titlepage}AnchorCover\end{titlepage}
\pagenumbering{arabic}
\makeatletter\typeout{ANCHOR-STATE=\ifHy@pageanchor true\else false\fi}\makeatother
\pdfbookmark{Alpha\enskip Beta\\Gamma}{probe}MainAnchorPage\par
\end{document}'''
    for name, cls, options in classes:
        for disabled in (False, True):
            source = anchors.replace('CLASS', cls).replace('OPTIONS', options).replace('CONTROL',
                r'\hypersetup{pageanchor=false}' if disabled else '')
            folder, _, log = compile_case('anchors-' + name + ('-disabled' if disabled else ''), source)
            reader = PdfReader(folder / 'main.pdf')
            target = reader.named_destinations.get('page.1')
            assert ('ANCHOR-STATE=false' if disabled else 'ANCHOR-STATE=true') in log
            assert target is None if disabled else reader.get_destination_page_number(target) == 1
            assert 'Alpha Beta Gamma' in [str(item.title) for item in reader.outline if not isinstance(item, list)]

    english = r'''\documentclass[fontset=fandol,type=doctor]{hithesisbook}
\hitsetup{etitle={Short title},eauthor={Candidate Name},esupervisor={Professor Name},esubject={Mechanical Engineering},
eaffil={School of Engineering},edate={June, 2026}EXTRA}
\begin{document}\ExplSyntaxOn
\cs_if_exist:NTF \__hit_engcover: {\__hit_engcover:}{\use:c{hit@engcover}}
\ExplSyntaxOff\end{document}'''
    for name, extra in [('short', ''), ('manual', r',eaffil={\emultiline{School of Engineering\\Research Center}}'),
        ('long', ',eassosupervisor={Associate Example},ecosupervisor={Industry Example},'
         'esubject={Advanced Mechanical Engineering and Intelligent Manufacturing Technologies with International Collaborative Research},'
         'eaffil={School of Advanced Mechanical Engineering and Intelligent Manufacturing Research with International Collaborative Studies}')]:
        source = english.replace('EXTRA', extra)
        folder, pages, log = compile_case('english-fields-' + name, source)
        assert len(pages) == 1 and 'Overfull \\hbox' not in log, name
        with pdfium.PdfDocument(folder / 'main.pdf') as document:
            for page in document:
                text = page.get_textpage()
                boxes = [text.get_charbox(i) for i in range(text.count_chars()) if text.get_text_range(i, 1).strip()]
                assert min(b[0] for b in boxes) >= 84 and max(b[2] for b in boxes) <= 511, name
                text.close()
                page.close()
        if args.baseline and name != 'long':
            old_folder, old, _ = compile_case('english-fields-' + name + '-old', source, args.baseline)
            assert pages == old, name
            assert compatibility.signature(old_folder / 'main.pdf') == compatibility.signature(folder / 'main.pdf'), name

    captions = r'''\documentclass[fontset=fandol,OPTIONS]{CLASS}
\begin{document}HEADING
\begin{figure}[htbp]\centering\rule{20mm}{4mm}
\caption[ShortOne]{PrimaryOne}[SecondaryOne]\label{new}\typeout{EXPECT-NEW=\thefigure}\end{figure}
\begin{figure}[htbp]\centering\rule{20mm}{4mm}
\label{legacy-before}
\bicaption[legacy-in]{LegacyShort}{LegacyPrimary}{Fig.}{LegacySecondary}\label{legacy-after}
\typeout{EXPECT-LEGACY=\thefigure}\end{figure}
\begin{figure}[htbp]\centering\rule{20mm}{4mm}\caption*{PlainUnnumbered}[OtherUnnumbered]\end{figure}
\begin{figure}[htbp]\centering\rule{20mm}{4mm}\caption[EmptyShort]{EmptyPrimary}[]\label{empty}\end{figure}
\clearpage\typeout{FIGURE-COUNT=\arabic{figure}}
\begin{longtable}{p{80mm}}
\caption[ShortLT]{PrimaryLT}[SecondaryLT]\label{lt}\\First row.\\
\caption*{StarPrimaryLT}[StarSecondaryLT]\\Second row.\\
\caption{NextLT}\label{lt-next}\\Third row.\\\end{longtable}
\typeout{TABLE-COUNT=\arabic{table}}\listoffigures\listoftables
\end{document}'''
    caption_cases = classes + [('book-en', 'hithesisbook', 'type=master,language=english'),
        ('art-caption', 'hithesisart', 'type=bachelor,campus=shenzhen,stage=opening')]
    for name, cls, options in caption_cases:
        heading = r'\mainmatter\chapter{Test}[Test]' if cls == 'hithesisbook' else r'\section{Test}'
        source = captions.replace('CLASS', cls).replace('OPTIONS', options).replace('HEADING', heading)
        folder, pages, log = compile_case('captions-' + name, source)
        aux = (folder / 'main.aux').read_text()
        assert number(aux, 'new') == re.search(r'EXPECT-NEW=([^\n]+)', log).group(1)
        assert number(aux, 'legacy-in') == re.search(r'EXPECT-LEGACY=([^\n]+)', log).group(1)
        assert number(aux, 'legacy-after') == number(aux, 'legacy-before'), 'Legacy caption reference scope changed'
        assert 'FIGURE-COUNT=3' in log and 'TABLE-COUNT=1' in log
        lof, lot = (folder / 'main.lof').read_text(), (folder / 'main.lot').read_text()
        assert 'ShortOne' in lof and 'LegacyShort' in lof and 'SecondaryOne' not in lof and 'LegacySecondary' not in lof
        assert 'ShortLT' in lot and 'NextLT' in lot and 'SecondaryLT' not in lot and 'StarPrimaryLT' not in lot
        text = '\n'.join(row[2] for page in pages for row in page)
        for expected in ['PrimaryOne', 'SecondaryOne', 'LegacyPrimary', 'LegacySecondary', 'PlainUnnumbered',
                'OtherUnnumbered', 'PrimaryLT', 'SecondaryLT', 'StarPrimaryLT', 'StarSecondaryLT', 'NextLT']:
            assert expected in text, (name, expected)
        for unnumbered in ['PlainUnnumbered', 'OtherUnnumbered', 'StarPrimaryLT', 'StarSecondaryLT']:
            assert any(row[2] == unnumbered for page in pages for row in page), (name, unnumbered)
        secondary_name = '图' if name == 'book-en' else 'Fig.'
        assert secondary_name + number(aux, 'empty') not in text, (name, 'Empty secondary caption printed a label')

    (args.work / 'results.json').write_text(json.dumps({'results': results, 'baseline': str(args.baseline)},
        ensure_ascii=False, indent=2) + '\n')
    print('Small-feature PDF/label/link regressions:', len(results), 'PASS')


if __name__ == '__main__':
    main()
