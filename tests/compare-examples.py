"""Compare complete example PDFs and reject new or more frequent diagnostics."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compatibility', ROOT / 'tests/compatibility.py')
compatibility = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compatibility)


DIAGNOSTIC = re.compile(r'^(?:LaTeX(?: Font)? Warning:|(?:Package|Class) \S+ Warning:|'
    r'Missing character:|(?:Over|Under)full \\[hv]box)')


def warning_counts(path):
    """Keep message contents/counts; normalize only wrapping and source line numbers."""
    lines = path.read_text(errors='replace').splitlines()
    result = Counter()
    position = 0
    while position < len(lines):
        line = lines[position]
        position += 1
        if not DIAGNOSTIC.match(line):
            continue
        message = [line.strip()]
        if line.startswith('Missing character:'):
            while not message[-1].endswith('!') and position < len(lines):
                if not lines[position].strip() or DIAGNOSTIC.match(lines[position]):
                    break
                message.append(lines[position].strip())
                position += 1
        elif not line.startswith(('Overfull ', 'Underfull ')):
            while position < len(lines) and lines[position].strip():
                if DIAGNOSTIC.match(lines[position]):
                    break
                message.append(lines[position].strip())
                position += 1
        text = ' '.join(message)
        text = re.sub(r'\b((?:input )?line) \d+\b', r'\1 <line>', text)
        text = re.sub(r'\blines \d+--\d+\b', 'lines <range>', text)
        result[text] += 1
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    args = parser.parse_args()
    results = []
    work = Path(tempfile.mkdtemp(prefix='example-regression-', dir=ROOT / 'build'))
    # Docker creates it as root; the artifact uploader runs as the host user.
    work.chmod(0o755)
    for family, job in (('hitbook/chinese', 'thesis'), ('hitbook/english', 'thesis'),
                       ('hitart/reports', 'report'), ('hitart/reportplus', 'report')):
        phase = 'baseline'
        result = dict(case=family)
        old = args.baseline / 'examples' / family
        current = ROOT / 'examples' / family
        new = work / family
        try:
            with (old / 'regression-build.log').open('w') as output:
                subprocess.run(['latexmk', '-g', '-xelatex', '-interaction=nonstopmode',
                    '-halt-on-error', job + '.tex'], cwd=old, stdout=output,
                    stderr=subprocess.STDOUT, check=True, timeout=180)
            phase = 'candidate'
            assert (current / (job + '.pdf')).exists(), 'Run make compile-examples first'
            # Compare the same old document with both runtimes. New examples
            # are compiled separately and may contain newly added commands.
            shutil.copytree(old, new, ignore=shutil.ignore_patterns(
                '*.aux', '*.log', '*.fls', '*.fdb_latexmk', '*.synctex.gz'))
            for pattern in ('*.cls', '*.cfg', '*.sty', '*.bst', '*.ist', '*.eps'):
                for path in ROOT.glob(pattern):
                    shutil.copy2(path, new / path.name)
            with (new / 'regression-build.log').open('w') as output:
                subprocess.run(['latexmk', '-g', '-xelatex', '-interaction=nonstopmode',
                    '-halt-on-error', job + '.tex'], cwd=new, stdout=output,
                    stderr=subprocess.STDOUT, check=True, timeout=180)
            old_warnings = warning_counts(old / (job + '.log'))
            new_warnings = warning_counts(new / (job + '.log'))
            introduced = new_warnings - old_warnings
            result.update(baseline_warnings=dict(old_warnings),
                candidate_warnings=dict(new_warnings), new_warnings=dict(introduced))
            assert not introduced, ('New or more frequent diagnostics', dict(introduced))
            before = compatibility.signature(old / (job + '.pdf'), require_targets=False)
            after = compatibility.signature(new / (job + '.pdf'), require_targets=False)
            assert len(before[0]) == len(after[0]), ('Page count changed', len(before[0]), len(after[0]))
            different = [i + 1 for i, (a, b) in enumerate(zip(before[0], after[0])) if a != b]
            if different:
                page = different[0] - 1
                a, b = before[0][page], after[0][page]
                index = next((i for i, (x, y) in enumerate(zip(a[0], b[0])) if x != y), min(len(a[0]), len(b[0])))
                print('First page difference:', dict(page=page + 1,
                    baseline_text=a[0][max(0, index - 100):index + 300],
                    candidate_text=b[0][max(0, index - 100):index + 300]), flush=True)
            assert not different, ('Changed text/character boxes on pages', different)
            assert before[1] == after[1], 'Links or destinations changed'
            result.update(status='PASS', pages=len(after[0]), links=len(after[1]),
                candidate_document=str(new / (job + '.pdf')),
                current_examples_pages=len(compatibility.signature(current / (job + '.pdf'), require_targets=False)[0]),
                baseline_unresolved_links=sum(link[4] == 'UNRESOLVED' for link in before[1]))
        except Exception as error:
            result.update(status='BLOCKED_BASELINE' if phase == 'baseline' else 'FAIL',
                phase=phase, error=str(error))
        results.append(result)
        print({key: value for key, value in result.items()
            if key not in ('baseline_warnings', 'candidate_warnings')}, flush=True)
    destination = ROOT / 'build/example-regression.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    raise SystemExit(any(r['status'] != 'PASS' for r in results))


if __name__ == '__main__':
    main()
