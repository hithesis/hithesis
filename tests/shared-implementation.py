"""Compare the explicitly shared expl3 definitions with a local dev source tree.

This checks implementation identity, not Git ancestry or whole-branch equality.
The maintained source is monolithic; dev assembles the same definitions from
modules. Whitespace and comments are ignored inside these ExplSyntaxOn bodies;
explicit space tokens (~), parameter texts and protected/expandable status remain.
"""
import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
MODULES = {
    '__hit_info_export:n': 'src/engine/hit-key-engine.dtx',
    '__hit_info_set:nn': 'src/engine/hit-key-engine.dtx',
    '__hit_info_define:nn': 'src/engine/hit-key-engine.dtx',
    '__hit_keywords_join:NNnnn': 'src/engine/hit-key-engine.dtx',
    '__hit_month_name:n': 'src/engine/hit-date.dtx',
    '__hit_caption_separator:nn': 'src/engine/hit-caption.dtx',
    '__hit_keywords_typeset:NNnnn': 'src/pages/hit-final-abstract.dtx',
    '__hit_clear_empty_double_page:N': 'src/flow/hit-final-matter.dtx',
}


def definition(source, name):
    source = re.sub(r'(?<!\\)%[^\n]*', '', source)
    pattern = re.compile(r'\\cs_new(?:_protected)?:Npn\s*\\' +
        re.escape(name) + r'(?![A-Za-z@_:])[^{}]*\{')
    matches = list(pattern.finditer(source))
    assert len(matches) == 1, (name, 'Expected exactly one definition', len(matches))
    match = matches[0]
    position, depth = match.end(), 1
    while depth:
        assert position < len(source), (name, 'Unclosed definition')
        char = source[position]
        if char == '\\':
            position += 2
            continue
        depth += (char == '{') - (char == '}')
        position += 1
    return re.sub(r'\s+', '', source[match.start():position])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dev', type=Path, required=True)
    parser.add_argument('--baseline-ref', default='v3.2a')
    args = parser.parse_args()
    if (ROOT / 'hithesis.dtx').exists():
        maintained = (ROOT / 'hithesis.dtx').read_text()
    else:
        maintained = subprocess.check_output(['git', '-c', f'safe.directory={ROOT}',
            'show', args.baseline_ref + ':hithesis.dtx'], cwd=ROOT).decode('utf-8')
    for name, module in MODULES.items():
        developed = (args.dev / module).read_text()
        assert definition(maintained, name) == definition(developed, name), (
            name, 'Shared implementation differs', module)
        print(name, module, 'PASS')
    print('Eight shared definitions match; branch-specific callers require separate regressions.')


if __name__ == '__main__':
    main()
