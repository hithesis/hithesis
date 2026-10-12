"""Preserve original unknown-key errors and invalid-boolean warnings/state."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    args.work.mkdir(parents=True, exist_ok=False)
    (args.work / 'empty-texmf').mkdir()
    cases = [
        ('book-unknown-key', 'hithesisbook', 'type=master,campus=harbin', 'unexpectedkey=1', 'unexpectedkey'),
        ('art-unknown-key', 'hithesisart', 'type=master,campus=harbin,stage=opening', 'unexpectedkey=1', 'unexpectedkey'),
        ('artplus-unknown-key', 'hithesisartplus', 'type=doctor,campus=shenzhen,stage=midterm', 'unexpectedkey=1', 'unexpectedkey'),
        ('book-invalid-bool', 'hithesisbook', 'type=master,campus=harbin', 'newtxmath=invalid', 'newtxmath'),
        ('art-invalid-bool', 'hithesisart', 'type=master,campus=harbin,stage=opening', 'newtxmath=invalid', 'newtxmath'),
    ]
    results = []
    for name, cls, options, setting, expected in cases:
        result = dict(case=name)
        try:
            for phase, source in (('baseline', args.baseline), ('candidate', ROOT)):
                folder = args.work / name / phase
                folder.mkdir(parents=True)
                for filename in (cls + '.cls', 'hithesisbook.cfg', 'hithesisart.cfg'):
                    shutil.copy2(source / filename, folder / filename)
                (folder / 'main.tex').write_text(
                    '\\documentclass[fontset=fandol,' + options + ']{' + cls + '}\n'
                    '\\hitsetup{' + setting + '}\n' +
                    ('\\makeatletter\\typeout{HIT-BOOL-STATE:\\ifhit@newtxmath true\\else false\\fi}\\makeatother\n'
                        if 'invalid-bool' in name else '') +
                    '\\begin{document}Test.\\end{document}\n')
                with (folder / 'compile.log').open('w') as output:
                    status = subprocess.run(['xelatex', '-interaction=nonstopmode',
                        '-halt-on-error', 'main.tex'], cwd=folder,
                        env=os.environ | dict(TEXINPUTS='.:', TEXMFHOME=str(args.work / 'empty-texmf')),
                        stdout=output, stderr=subprocess.STDOUT, timeout=120).returncode
                log = (folder / 'main.log').read_text()
                if 'invalid-bool' in name:
                    assert status == 0 and 'Warning' in log and 'invalid' in log and expected in log, (
                        'Invalid boolean must warn rather than fail', phase)
                    assert 'HIT-BOOL-STATE:true' in log, ('Invalid boolean changed the default', phase)
                else:
                    assert status != 0 and expected in log, ('Unknown key was not diagnosed', phase)
                if phase == 'candidate' and setting.startswith('unexpectedkey'):
                    assert 'hit/unexpectedkey' in log, 'Unknown-key diagnostic names the wrong key'
            result['status'] = 'PASS'
        except Exception as error:
            result.update(status='FAIL', error=str(error))
        print(result, flush=True)
        results.append(result)
    (args.work / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    raise SystemExit(any(result['status'] != 'PASS' for result in results))


if __name__ == '__main__':
    main()
