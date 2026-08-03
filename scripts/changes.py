#!/usr/bin/env python3
"""从 hithesis.dtx 的 \\changes 条目生成 release notes。

原先这活儿在 Makefile 里用 awk 干，但用到了三参数 match()，那是 gawk 扩展：
macOS 自带的 awk 不认，会静默产出空文件；Windows 干脆没有 awk。改用 Python 之后
只要有 python3 就能跑，同时也不再依赖 cut / sort -V 这些 GNU 版本特有的行为。

用法::

    scripts/changes.py                 # 写出 RELEASE_NOTES.md
    scripts/changes.py --version       # 只打印最新版本号，如 v3.1e
    scripts/changes.py --stamp         # 把最新版本的 0000/00/00 填成今天
    scripts/changes.py --stamp --date 2026/08/03 --for v3.1e
    scripts/changes.py --check         # 校验日期约定，CI 用
    scripts/changes.py --fix           # 就地修正能自动修的部分

发版流程里 --stamp 要在打 tag **之前**执行，否则 tag 指向的源码里仍是占位符。
仓库既有约定是「同一版本的所有条目共用该版本的发布日期」（v3.1d 的 59 条全是
2025/03/03），--stamp 就是照这个约定来的。
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "RELEASE_NOTES.md"
PLACEHOLDER = "0000/00/00"


def dtx_files() -> list[Path]:
    r"""\changes 散落在 hithesis.dtx / -doc.dtx / -eps.dtx，全都要扫。"""
    return sorted(ROOT.glob("*.dtx"))

HEAD = re.compile(r"\\changes\{([^}]*)\}\{([^}]*)\}\{")


def balanced(text: str, start: int) -> tuple[str, int]:
    """从 start（左花括号之后）读到配对的右花括号，返回内容和结束位置。"""
    depth, out = 1, []
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return "".join(out), i
        out.append(ch)
    return "".join(out), len(text)


def collect_one(dtx: Path) -> list[tuple[str, str, str]]:
    """返回 (版本, 日期, 说明) 列表，版本已去掉前导 v。"""
    text = dtx.read_text(encoding="utf-8")
    items = []
    pos = 0
    while (m := HEAD.search(text, pos)) is not None:
        version, date = m.group(1), m.group(2)
        body, end = balanced(text, m.end())
        pos = end + 1
        if not version:
            continue
        # dtx 里的说明可能跨行，行首的 % 和缩进要去掉
        body = " ".join(part.lstrip("% ").strip() for part in body.splitlines()).strip()
        items.append((version.lstrip("v"), date, body))
    return items


def collect() -> list[tuple[str, str, str]]:
    return [item for f in dtx_files() for item in collect_one(f)]


def stamp(version: str, date: str) -> int:
    """把指定版本的占位日期就地填成 date，返回改动条数。"""
    old = f"\\changes{{{version}}}{{{PLACEHOLDER}}}"
    new = f"\\changes{{{version}}}{{{date}}}"
    total = 0
    for f in dtx_files():
        text = f.read_text(encoding="utf-8")
        n = text.count(old)
        if n:
            f.write_text(text.replace(old, new), encoding="utf-8")
            print(f"  {f.name}: {n} 条")
            total += n
    return total


DATE_RE = re.compile(r"^(\d{4})/(\d{1,2})/(\d{1,2})$")


def normalize(date: str) -> str:
    """2022/5/6 补成 2022/05/06；认不出来的原样返回。"""
    m = DATE_RE.match(date)
    return f"{m.group(1)}/{int(m.group(2)):02d}/{int(m.group(3)):02d}" if m else date


def audit(items: list[tuple[str, str, str]], latest: str) -> list[str]:
    """返回问题清单。三条规则都不需要 git 历史，是无状态的。

    刻意不查「同一版本共用一个日期」：早期版本本来就是一条一个日期
    （v3.0.0 有三个，v3.0.15 跨了一年），这个约定是 v3.1b 之后才固化的。
    """
    problems = []
    for version, date, body in items:
        where = f"v{version}"
        if version == latest and date != PLACEHOLDER:
            problems.append(
                f"{where} 是开发版，日期该写 {PLACEHOLDER}，实际是 {date}\n"
                f"    条目：{body[:50]}")
        elif version != latest and date == PLACEHOLDER:
            problems.append(
                f"{where} 已发布，却留着 {PLACEHOLDER} 没填\n"
                f"    条目：{body[:50]}")
        elif date != PLACEHOLDER and normalize(date) != date:
            problems.append(f"{where} 的日期 {date} 不是 YYYY/MM/DD，应为 {normalize(date)}")
    return problems


def fix(latest: str) -> int:
    """能自动修的就地修掉：补零，以及把开发版的实际日期打回占位符。"""
    changed = 0
    for f in dtx_files():
        text = original = f.read_text(encoding="utf-8")

        def repl(m: re.Match) -> str:
            version, date = m.group(1), m.group(2)
            if version.lstrip("v") == latest:
                date = PLACEHOLDER
            elif date != PLACEHOLDER:
                date = normalize(date)
            return f"\\changes{{{version}}}{{{date}}}{{"

        text = re.sub(r"\\changes\{(v?[^}]*)\}\{([^}]*)\}\{", repl, text)
        if text != original:
            n = sum(1 for a, b in zip(original.splitlines(), text.splitlines()) if a != b)
            f.write_text(text, encoding="utf-8")
            print(f"  {f.name}: {n} 行")
            changed += n
    return changed


def version_key(v: str) -> list:
    """v3.1e / v3.0.20 都要能排：数字段按数字比，字母段按字母比。"""
    return [int(p) if p.isdigit() else p for p in re.findall(r"\d+|[a-z]+", v)]


def main() -> int:
    parser = argparse.ArgumentParser(description="从 dtx 的 \\changes 生成 release notes")
    parser.add_argument("--version", action="store_true", help="只打印最新版本号")
    parser.add_argument("--stamp", action="store_true",
                        help="把占位日期 0000/00/00 就地填成发布日期")
    parser.add_argument("--date", metavar="YYYY/MM/DD",
                        help="配合 --stamp，默认今天")
    parser.add_argument("--for", dest="target", metavar="VER",
                        help="配合 --stamp，指定版本；默认最新版本")
    parser.add_argument("--check", action="store_true", help="校验日期约定，有问题时退出码 1")
    parser.add_argument("--fix", action="store_true", help="就地修正能自动修的部分")
    args = parser.parse_args()

    if not dtx_files():
        print("error: 找不到任何 .dtx", file=sys.stderr)
        return 1

    items = collect()
    if not items:
        print("error: 一条 \\changes 都没解析出来", file=sys.stderr)
        return 1

    latest = max({v for v, _, _ in items}, key=version_key)

    if args.version:
        print(f"v{latest}")
        return 0

    if args.check:
        problems = audit(items, latest)
        if not problems:
            print(f"\\changes 日期约定检查通过（开发版 v{latest}，共 {len(items)} 条）")
            return 0
        print(f"发现 {len(problems)} 处问题：")
        for msg in problems:
            print(f"  - {msg}")
        print("\n跑 scripts/changes.py --fix 可自动修正补零与开发版日期。")
        return 1

    if args.fix:
        print(f"修正中（开发版 v{latest}）：")
        n = fix(latest)
        print(f"共改 {n} 行" if n else "  无需改动")
        return 0

    if args.stamp:
        target = args.target or f"v{latest}"
        date = args.date or datetime.date.today().strftime("%Y/%m/%d")
        if not re.fullmatch(r"\d{4}/\d{2}/\d{2}", date):
            print(f"error: 日期要写成 YYYY/MM/DD，收到 {date}", file=sys.stderr)
            return 1
        print(f"把 {target} 的占位日期填成 {date}：")
        n = stamp(target, date)
        if n == 0:
            print(f"  {target} 没有待填的 {PLACEHOLDER}，无需改动")
        else:
            print(f"共填 {n} 条")
        return 0

    seen, lines = set(), []
    for version, date, body in sorted(items, key=lambda x: x[1]):
        if version != latest:
            continue
        entry = f"- {body} ({date})"
        if entry not in seen:
            seen.add(entry)
            lines.append(entry)

    OUTPUT.write_text(f"## v{latest}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    print(f"Release notes generated: {OUTPUT.name}（v{latest}，{len(lines)} 条）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
