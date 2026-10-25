"""Check Beijing dates across time zones and month boundaries, including manually supplied dates."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
BEIJING = timezone(timedelta(hours=8))
TIMESTAMPS = [
    'D:20261025120000Z', 'D:20261024180000Z', 'D:20261231180000Z',
    "D:20260101013000+14'00'", "D:20261231233000-12'00'",
    "D:20261025120000+08'00'", "D:20261025235900+05'30'",
    "D:20261025003000-06'30'", 'D:20240228200000Z',
    'D:20000228200000Z', 'D:19000228200000Z', 'D:21000228200000Z',
    'D:20260430180000Z', 'D:20260228180000Z', 'D:20261024180000',
]
PROFILES = [('book', 'hithesisbook', 'type=doctor'),
            ('book-en', 'hithesisbook', 'type=master,language=english'),
            ('art', 'hithesisart', 'type=master,stage=opening'),
            ('artplus', 'hithesisartplus', 'type=doctor,campus=shenzhen,stage=midterm')]


def expected(stamp):
    local = datetime.strptime(stamp[2:16], '%Y%m%d%H%M%S')
    suffix = stamp[16:]
    offset = 0
    if suffix and suffix != 'Z':
        offset = (int(suffix[1:3])*60 + int(suffix[4:6])) * (-1 if suffix[0] == '-' else 1)
    return local.replace(tzinfo=timezone(timedelta(minutes=offset))).astimezone(BEIJING).strftime('%Y-%m-%d')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    results = []
    def compile_case(name, cls, options, body, epoch, tz='UTC'):
        folder = args.work / name
        folder.mkdir()
        for pattern in ('*.cls', '*.cfg', '*.sty', '*.bst', '*.eps'):
            for path in ROOT.glob(pattern):
                shutil.copy2(path, folder / path.name)
        source = '\\documentclass[fontset=fandol,' + options + ']{' + cls + '}\n' + body
        (folder / 'main.tex').write_text(source)
        env = os.environ | {'TEXINPUTS': str(folder.resolve()) + ':',
            'TEXMFLOCAL': str(ROOT / 'build/dependencies/texmf'), 'TZ': tz,
            'SOURCE_DATE_EPOCH': str(epoch), 'FORCE_SOURCE_DATE': '1'}
        with (folder / 'compile.log').open('w') as output:
            subprocess.run(['xelatex', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', 'main.tex'],
                cwd=folder, env=env, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=180)
        return folder, (folder / 'main.log').read_text()
    probe = r'''\cs_new_protected:Npn\DateProbe #1
  {\iow_term:e{DATE:#1=\int_use:N\g__hit_engine_today_year_int-\int_use:N\g__hit_engine_today_month_int-\int_use:N\g__hit_engine_today_day_int}}
'''
    epoch = int(datetime(2025, 12, 31, 18, tzinfo=timezone.utc).timestamp())
    for profile, cls, options in PROFILES:
        body = '\\ExplSyntaxOn\n' + probe + r'\iow_term:e{PRIMITIVE-BEFORE=\the\year-\the\month-\the\day}' + '\n'
        for index, stamp in enumerate(TIMESTAMPS):
            body += '\\__hit_engine_today_parse:n{' + stamp + '}\\DateProbe{' + str(index) + '}\n'
        for index, stamp in enumerate(('not-a-date', 'D:20261301000000Z', 'D:20260230000000Z', 'D:00000101000000Z')):
            body += '\\int_gset:Nn\\g__hit_engine_today_year_int{2001}\\int_gset:Nn\\g__hit_engine_today_month_int{1}\\int_gset:Nn\\g__hit_engine_today_day_int{1}\n'
            body += '\\__hit_engine_today_parse:n{' + stamp + '}\\DateProbe{invalid-' + str(index) + '}\n'
        body += r'\iow_term:e{PRIMITIVE-AFTER=\the\year-\the\month-\the\day}' + '\n\\ExplSyntaxOff\n\\begin{document}Calendar probe.\\end{document}'
        _, log = compile_case(profile + '-calendar', cls, options, body, epoch)
        values = dict(re.findall(r'DATE:([^=\n]+)=(\d+-\d+-\d+)', log))
        for index, stamp in enumerate(TIMESTAMPS):
            actual = datetime.strptime(values[str(index)], '%Y-%m-%d').strftime('%Y-%m-%d')
            assert actual == expected(stamp), (profile, stamp, actual, expected(stamp))
        assert all(values['invalid-' + str(index)] == '2001-1-1' for index in range(4)), values
        assert re.search(r'PRIMITIVE-BEFORE=([^\n]+)', log)[1] == re.search(r'PRIMITIVE-AFTER=([^\n]+)', log)[1]
        results.append({'case': profile + '-calendar', 'timestamps': len(TIMESTAMPS), 'invalid': 4, 'status': 'PASS'})
        for tz in ('UTC', 'Asia/Shanghai', 'America/Los_Angeles'):
            body = (r'\hitsetup{cdate={2000-02-03}}' + '\n\\ExplSyntaxOn\n' + probe + r'\DateProbe{actual}' +
                    '\n\\ExplSyntaxOff\n' + r'''\begin{document}
DEFAULT:\today\par
\CJKtoday[2]BIG:\today\par
\CJKtoday[1]ARABIC:\today\par
MANUAL:\ExplSyntaxOn\__hit_date_use:nV{zh}\g__hit_info_cdate_tl\ExplSyntaxOff\par
\ExplSyntaxOn\cs_if_exist:NT\g__hit_info_edate_tl{EDATE:\__hit_date_use:nV{en}\g__hit_info_edate_tl\par}\ExplSyntaxOff
BASEORIGINAL:\ExplSyntaxOn\use:c{CJK@todaysave}\ExplSyntaxOff\par
\CJKtoday[0]ORIGINAL:\today\par
\end{document}''')
            folder, log = compile_case(profile + '-' + tz.replace('/', '-'), cls, options, body, epoch, tz)
            assert 'DATE:actual=2026-1-1' in log, (profile, tz, log)
            with pdfium.PdfDocument(folder / 'main.pdf') as pdf:
                page = pdf[0]
                text_page = page.get_textpage()
                text = ''.join(text_page.get_text_range().split())
                text_page.close()
                page.close()
            for value in ('DEFAULT:2026年1月1日', 'BIG:二〇二六年一月一日',
                          'ARABIC:2026年1月1日', 'MANUAL:2000年2月3日'):
                assert value in text, (profile, tz, value, text)
            if cls == 'hithesisbook':
                assert 'EDATE:January,2026' in text, (profile, tz, text)
            original = text.split('BASEORIGINAL:', 1)[1].split('ORIGINAL:', 1)
            assert original[1].startswith(original[0]), (profile, tz, 'Original date fallback changed', text)
            results.append({'case': profile + '-' + tz, 'expected': '2026-01-01', 'status': 'PASS'})
    (args.work / 'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print('Beijing dates: 60 boundary timestamps, 16 invalid controls and 12 timezone/render cases PASS')


if __name__ == '__main__':
    main()
