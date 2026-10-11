"""Verify that the refactor retains every original changes record in order."""
import argparse
from collections import Counter
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = 'b241065a8eb609e16c7004509facc9dda57901ef'


def group(source, position):
    while position < len(source) and source[position].isspace():
        position += 1
    assert source[position] == '{', ('Expected changes argument', position)
    start, depth = position + 1, 1
    position += 1
    while depth:
        assert position < len(source), 'Unclosed changes argument'
        char = source[position]
        if char == '\\':
            position += 2
            continue
        depth += (char == '{') - (char == '}')
        position += 1
    return source[start:position - 1], position


def records(source):
    # Multiline dtx comments prefix every line with %. Keep the actual TeX
    # contents, including nested command arguments and escaped braces.
    source = re.sub(r'(?m)^\s*% ?', '', source)
    result = []
    for match in re.finditer(r'\\changes\s*(?=\{)', source):
        position, values = match.end(), []
        for _ in range(3):
            value, position = group(source, position)
            values.append(' '.join(value.split()))
        result.append(tuple(values))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default=BASE)
    args = parser.parse_args()
    original = subprocess.check_output(['git', '-c', f'safe.directory={ROOT}',
        'show', args.baseline + ':hithesis.dtx'], cwd=ROOT).decode('utf-8')
    old = records(original)
    new = records((ROOT / 'hithesis.dtx').read_text())
    missing = Counter(old) - Counter(new)
    assert not missing, ('Missing or edited original changes records', list(missing.elements()))
    position = 0
    for record in new:
        if position < len(old) and record == old[position]:
            position += 1
    assert position == len(old), 'Original changes records were reordered'
    added = Counter(new) - Counter(old)
    print(f'Original changes: {len(old)}; retained in order: {position}; added: {sum(added.values())}')
    for record, count in added.items():
        print('Added:', record, 'count=' + str(count))


if __name__ == '__main__':
    main()
