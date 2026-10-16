"""Run all nine Lua macro cases and verify they actually executed."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def load_cases(root):
    cases = [line.split('#', 1)[0].strip()
             for line in (root / 'tests/lua-cases.txt').read_text(encoding='utf-8').splitlines()]
    cases = [name for name in cases if name]
    if len(cases) != 9 or len(set(cases)) != 9:
        raise ValueError('tests/lua-cases.txt 必须列出九项不同的测试')
    if not (root / 'config-lua.lua').is_file():
        raise ValueError('缺少 config-lua.lua')
    for name in cases:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]*', name):
            raise ValueError(f'无效测试名：{name}')
        for suffix in ('.lvt', '.luatex.tlg'):
            if not (root / 'testfiles' / (name + suffix)).is_file():
                raise ValueError(f'缺少 testfiles/{name}{suffix}')
    return sorted(cases)


def run_checks(root=ROOT):
    root = Path(root).resolve()
    build = root / 'build'
    build.mkdir(exist_ok=True)
    work = build / 'test-config-lua'
    command = ['l3build', 'check', '-c', 'config-lua', '-e', 'luatex']
    errors, cases, checks = [], [], []
    output, returncode = '', None
    try:
        cases = load_cases(root)
        # checkinit normally clears these. Remove only the known generated logs
        # first, so a skipped/failed invocation cannot reuse a previous success.
        for name in cases:
            for suffix in ('.log', '.luatex.log', '.luatex.diff'):
                (work / (name + suffix)).unlink(missing_ok=True)
        completed = subprocess.run(command, cwd=root, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace', timeout=900)
        output, returncode = completed.stdout, completed.returncode
    except subprocess.TimeoutExpired as error:
        output = error.stdout or ''
        if isinstance(output, bytes):
            output = output.decode('utf-8', errors='replace')
        errors.append('l3build 超过 900 秒未完成')
    except (OSError, ValueError) as error:
        errors.append(str(error))
    (build / 'lua-check.log').write_text(output + ''.join(error + '\n' for error in errors), encoding='utf-8')
    print(output, end='')
    progress = re.findall(r'^\s+(\S+) \((\d+)/(\d+)\)\s*$', output, re.MULTILINE)
    expected = [(name, str(index), str(len(cases))) for index, name in enumerate(cases, 1)]
    if returncode != 0:
        errors.append(f'l3build 未成功完成（退出码 {returncode}）')
    if 'Skipping unknown engine' in output or 'No applicable engine requested' in output:
        errors.append('l3build 跳过了请求的引擎')
    if not cases or progress != expected:
        errors.append(f'实际测试清单/计数不符：期望九项，收到 {len(progress)} 项')
    if not re.search(r'^\s*All checks passed\s*$', output, re.MULTILINE):
        errors.append('缺少 l3build 的完成标记')
    for name in cases:
        issues = []
        try:
            raw = (work / (name + '.log')).read_text(encoding='utf-8', errors='replace')
            if not re.match(r'This is Lua(?:HB)?TeX\b', raw):
                issues.append('原始日志不是 LuaTeX/LuaHBTeX')
            actual = (work / (name + '.luatex.log')).read_text(encoding='utf-8')
            reference = (root / 'testfiles' / (name + '.luatex.tlg')).read_text(encoding='utf-8')
            if actual != reference:
                issues.append('完整标准化日志与 Lua 专用基线不同')
        except (OSError, UnicodeError) as error:
            issues.append(str(error))
        checks.append({'name': name, 'passed': not issues, 'errors': issues})
        errors.extend(f'{name}: {issue}' for issue in issues)
    report = {'command': command, 'engine': 'luatex', 'expected_tests': cases,
        'executed_tests': [row[0] for row in progress], 'executed_count': len(progress),
        'l3build_exit_code': returncode, 'tests': checks, 'success': not errors, 'errors': errors}
    (build / 'lua-checks.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if errors:
        for error in errors:
            print('Lua 专项失败：' + error, file=sys.stderr)
        return 1
    print('Lua 专项：9/9 实际执行，Lua 引擎及全部专用基线核对通过。')
    return 0


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    return run_checks()


if __name__ == '__main__':
    sys.exit(main())
