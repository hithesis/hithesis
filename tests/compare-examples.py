"""Compile the unmodified master examples and compare complete maintenance PDFs."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compatibility', ROOT / 'tests/compatibility.py')
compatibility = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compatibility)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    args = parser.parse_args()
    results = []
    for family, job in (('hitbook/chinese', 'thesis'), ('hitbook/english', 'thesis'),
                       ('hitart/reports', 'report'), ('hitart/reportplus', 'report')):
        phase = 'baseline'
        result = dict(case=family)
        old = args.baseline / 'examples' / family
        new = ROOT / 'examples' / family
        try:
            with (old / 'regression-build.log').open('w') as output:
                subprocess.run(['latexmk', '-xelatex', '-interaction=nonstopmode',
                    '-halt-on-error', job + '.tex'], cwd=old, stdout=output,
                    stderr=subprocess.STDOUT, check=True, timeout=180)
            phase = 'candidate'
            assert (new / (job + '.pdf')).exists(), 'Run make compile-examples first'
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
                baseline_unresolved_links=sum(link[4] == 'UNRESOLVED' for link in before[1]))
        except Exception as error:
            result.update(status='BLOCKED_BASELINE' if phase == 'baseline' else 'FAIL',
                phase=phase, error=str(error))
        results.append(result)
        print(result, flush=True)
    destination = ROOT / 'build/example-regression.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    raise SystemExit(any(r['status'] != 'PASS' for r in results))


if __name__ == '__main__':
    main()
