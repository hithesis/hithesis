"""Keep legacy contracts while checking the explicitly added caption interface."""
import argparse
from collections import Counter
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def code(path):
    source = path.read_text()
    start = source.index(r'%<bookcls|artcls|artpluscls>\NeedsTeXFormat')
    end = source.index('%</hithesis-style>')
    return '\n'.join(line.split('%', 1)[0] for line in source[start:end].splitlines()
        if not line.lstrip().startswith('%'))


def public_declarations(text):
    """Normalize 2e and expl3 declarations without comparing implementation bodies."""
    text = '\n'.join(line.split('%', 1)[0] for line in text.splitlines())
    # Hyperref executes these replacements only in its PDF-string conversion
    # group. They are not definitions of document commands.
    encoding = re.compile(r'\\pdfstringdefDisableCommands\s*\{')
    while match := encoding.search(text):
        at, depth = match.end(), 1
        while depth:
            if text[at] == '\\':
                at += 2
                continue
            depth += (text[at] == '{') - (text[at] == '}')
            at += 1
        text = text[:match.start()] + text[at:]
    declarations = Counter()
    contracts = {}

    def record(name, args):
        name = name.lstrip('\\')
        contracts[name] = args
        if '@' not in name and '_' not in name and name not in ('hitsetup', 'equcaption', 'csname', 'arraystretch'):
            declarations[(name, args)] += 1

    legacy = re.compile(r'\\(newcommand|renewcommand|providecommand|DeclareRobustCommand|'
        r'newenvironment|renewenvironment)\s*\*?\s*\{?\\?([A-Za-z@]+)\}?\s*'
        r'(?:\[(\d+)\])?\s*(?:\[([^]]*)\])?')
    for match in legacy.finditer(text):
        verb, name, nargs, default = match.groups()
        nargs = int(nargs or 0)
        args = (('O', default),) + ('m',) * (nargs - 1) if default is not None else ('m',) * nargs
        record(name, args)
        if verb.endswith('environment'):
            record('end' + name, ())
    primitive = re.compile(r'\\(?:[egx]?def)\s*\\([A-Za-z@]+)((?:\s*#+\d)*)\s*\{')
    for name, params in primitive.findall(text):
        record(name, ('m',) * len(re.findall(r'#+\d', params)))
    native = re.compile(r'\\cs_(?:new|set|gset)(?:_protected)?(?:_nopar)?:Np[ne]\s*'
        r'\\([A-Za-z@_:]+)((?:\s*#+\d)*)\s*\{')
    for name, params in native.findall(text):
        record(name, ('m',) * len(re.findall(r'#+\d', params)))
    def braced(value, at):
        assert value[at] == '{'
        start, depth = at + 1, 1
        while depth:
            at += 1
            if value[at] == '{':
                depth += 1
            elif value[at] == '}':
                depth -= 1
        return value[start:at], at + 1

    document = re.compile(r'\\(?:New|Renew|Declare)Document(Command|Environment)\s*'
        r'\{?\\?([A-Za-z@]+)\}?\s*(?=\{)')
    for match in document.finditer(text):
        kind, name = match.groups()
        spec, _ = braced(text, match.end())
        args, at = [], 0
        while at < len(spec):
            char = spec[at]
            at += 1
            if char in ' ~\n':
                continue
            if char == 'O':
                default, at = braced(spec, at)
                args.append(('O', default))
            else:
                args.append(char)
        record(name, tuple(args))
        if kind == 'Environment':
            record('end' + name, ())
    # Resolve both old let aliases and new native aliases through definitions
    # present in the source, so forwarding does not weaken argument checking.
    aliases = re.findall(r'\\(?:let|cs_(?:new|set|gset)_eq:NN)\s*'
        r'\\([A-Za-z@_:]+)\s*=?\s*\\([A-Za-z@_:]+)', text)
    pending = aliases
    while pending:
        unresolved = []
        for name, target in pending:
            if target in contracts:
                record(name, contracts[target])
            else:
                unresolved.append((name, target))
        if len(unresolved) == len(pending):
            break
        pending = unresolved
    return declarations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    args = parser.parse_args()
    old = code(args.baseline / 'hithesis.dtx')
    new = code(ROOT / 'hithesis.dtx')
    old_keys = re.findall(r'\\define@key\{hit\}\{([^}]+)\}', old) or re.findall(
        r'\\__hit_key_define:nnn\s*\{hit\}\s*\{([^}]+)\}', old)
    new_keys = re.findall(r'\\__hit_key_define:nnn\s*\{hit\}\s*\{([^}]+)\}', new)
    assert sorted(key for key in old_keys if key != '#1') == sorted(new_keys)
    old_bools = re.findall(r'\\DeclareBoolOption\[([^]]+)\]\{([^}]+)\}', old) or re.findall(
        r'\\__hit_bool_option:nn\s*\{([^}]+)\}\s*\{([^}]+)\}', old)
    new_bools = re.findall(r'\\__hit_bool_option:nn\s*\{([^}]+)\}\s*\{([^}]+)\}', new)
    assert old_bools == new_bools, 'Boolean names/default declarations changed'
    assert (re.findall(r'\\hit@def@term\{([^}]+)\}', old) or re.findall(
        r'\\__hit_info_declare:n\s*\{([^}]+)\}', old)) == re.findall(
        r'\\__hit_info_declare:n\s*\{([^}]+)\}', new), 'Metadata keys changed'
    assert (re.findall(r'\\hit@parse@keywords\{([^}]+)\}', old) or re.findall(
        r'\\__hit_keywords_declare:n\s*\{([^}]+)\}', old)) == re.findall(
        r'\\__hit_keywords_declare:n\s*\{([^}]+)\}', new), 'Keyword keys changed'
    assert (re.findall(r'\\DeclareStringOption\{([^}]+)\}', old) or re.findall(
        r'\\__hit_string_option_declare:n\s*\{([^}]+)\}', old)) == re.findall(
        r'\\__hit_string_option_declare:n\s*\{([^}]+)\}', new)
    for filename in ('hithesisbook.cls', 'hithesisart.cls', 'hithesisartplus.cls',
            'hithesisbook.cfg', 'hithesisart.cfg', 'hithesis.sty'):
        old_path = args.baseline / filename
        if filename == 'hithesis.sty' and not old_path.exists():
            old_path = args.baseline / 'examples/hitbook/chinese/hithesis.sty'
        old_public = public_declarations(old_path.read_text())
        new_public = public_declarations((ROOT / filename).read_text())
        if filename.endswith('.cls'):
            added_captions = Counter({
                ('caption', ('s', 'o', '+', 'm', 'o')): 1,
                ('bicaption', ('o', '+', 'm', '+', 'm', '+', 'm', '+', 'm')): 1,
            })
            actual = Counter({key: count for key, count in new_public.items()
                if key[0] in ('caption', 'bicaption')})
            assert actual == added_captions, (filename, 'Unexpected caption wrapper contract', actual)
            old_public = Counter({key: count for key, count in old_public.items()
                if key[0] not in ('caption', 'bicaption')})
            new_public -= added_captions
        assert old_public == new_public, (filename, 'Public argument contracts changed',
            'missing', old_public - new_public, 'extra', new_public - old_public)
    print('Legacy declared keys/defaults, metadata and public declarations preserved; added caption contracts checked: PASS')


if __name__ == '__main__':
    main()
