#!/usr/bin/env python3
"""同步版本号与发布日期。

版本号散在三类地方，改一处漏两处是常事：

1. ``src/hithesis.dtx`` 的 ``\\ProvidesFile``，这是唯一的版本源，Makefile 靠它
   取版本命名发布包，手册封面的 ``\\date{v\\fileversion (\\filedate)}`` 也读它；
2. 同一文件里五条 ``\\ProvidesExplClass`` / ``\\ProvidesExplFile``，写进生成的
   ``.cls`` 与 ``.cfg``，用户 ``\\listfiles`` 看到的就是这个；
3. 四个示例文件开头 ASCII 横幅里的 ``hithesis vX.Y``。横幅是等宽画，改字要按原
   宽度重新居中，否则右边的图形会错位。手册用 ``\\lstinputlisting`` 把示例源码贴
   进正文，所以这一处同时也是手册里的展示，示例改完跑 ``make doc`` 即可。

``\\changes`` 条目里的版本号与正文里「v3.2a 起……」这类叙述不在同步范围内：前者
是历史记录，后者说的是某项改动发生在哪一版，都不该跟着走。

用法::

    scripts/version.py              # 列出各处版本，不一致时退出码 1
    scripts/version.py --check      # 同上，只是不打印明细，CI 用
    scripts/version.py --set 3.2b   # 全部改成 3.2b
    scripts/version.py --set 3.2b --date 2026/08/07

发版顺序建议：先 ``--set`` 定版本，再 ``scripts/changes.py --stamp`` 填 changes
的日期，最后打 tag。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "src" / "hithesis.dtx"
EXAMPLES = [
    ROOT / "examples" / "hitbook" / "chinese" / "thesis.tex",
    ROOT / "examples" / "hitbook" / "english" / "thesis.tex",
    ROOT / "examples" / "hitart" / "reports" / "report.tex",
    ROOT / "examples" / "hitart" / "reportplus" / "report.tex",
]

# \ProvidesFile{hithesis.dtx}[0000/00/00 3.2a Harbin ...]
RE_PROVIDESFILE = re.compile(
    r"(\\ProvidesFile\{hithesis\.dtx\}\[)(\S+)( )(\S+)( )"
)
# %<guard>\ProvidesExplClass{名}{日期}{版本}{描述}
RE_PROVIDESEXPL = re.compile(
    r"(\\ProvidesExpl(?:Class|File)\{[^}]*\}\{)([^}]*)(\}\{)([^}]*)(\})"
)
# 横幅里的 hithesis vX.Y
RE_BANNER = re.compile(r"hithesis v[0-9][0-9A-Za-z.]*")


def read(path: Path) -> tuple[bytes, str]:
    """读文件，返回原始字节与解码后的文本。行尾按字节处理，避免 CRLF 被改写。"""
    raw = path.read_bytes()
    return raw, raw.decode("utf-8")


def collect() -> dict[str, list[tuple[str, str]]]:
    """收集各处的版本号，返回 {版本: [(文件, 出处)]}。"""
    found: dict[str, list[tuple[str, str]]] = {}

    def note(ver: str, where: str) -> None:
        found.setdefault(ver, []).append(where)

    _, text = read(MAIN)
    m = RE_PROVIDESFILE.search(text)
    if m:
        note(m.group(4), (str(MAIN.relative_to(ROOT)), "ProvidesFile"))
    for m in RE_PROVIDESEXPL.finditer(text):
        note(m.group(4), (str(MAIN.relative_to(ROOT)), "ProvidesExpl*"))
    for p in EXAMPLES:
        if not p.exists():
            continue
        _, t = read(p)
        for m in RE_BANNER.finditer(t):
            note(m.group(0).split("v", 1)[1], (str(p.relative_to(ROOT)), "横幅"))
    return found


def recentre(line: str, old: str, new: str) -> str:
    """把 line 里的 old 换成 new，吃掉两侧空白后按原宽度重新居中。"""
    i = line.find(old)
    if i < 0:
        return line
    a = i
    while a > 0 and line[a - 1] == " ":
        a -= 1
    b = i + len(old)
    while b < len(line) and line[b] == " ":
        b += 1
    width = b - a
    if len(new) > width:
        raise SystemExit(f"横幅放不下 {new!r}，原区间只有 {width} 列：{line!r}")
    left = (width - len(new)) // 2
    return line[:a] + " " * left + new + " " * (width - len(new) - left) + line[b:]


def set_version(version: str, date: str | None) -> int:
    changed = 0

    raw, text = read(MAIN)
    def sub_file(m: re.Match[str]) -> str:
        d = date if date else m.group(2)
        return f"{m.group(1)}{d}{m.group(3)}{version}{m.group(5)}"
    new_text, n1 = RE_PROVIDESFILE.subn(sub_file, text)

    def sub_expl(m: re.Match[str]) -> str:
        d = date if date else m.group(2)
        return f"{m.group(1)}{d}{m.group(3)}{version}{m.group(5)}"
    new_text, n2 = RE_PROVIDESEXPL.subn(sub_expl, new_text)

    if new_text != text:
        MAIN.write_bytes(new_text.encode("utf-8"))
        changed += n1 + n2
        print(f"  {MAIN.relative_to(ROOT)}：ProvidesFile {n1} 处，ProvidesExpl* {n2} 处")

    for p in EXAMPLES:
        if not p.exists():
            continue
        raw, text = read(p)
        lines = text.split("\n")
        hit = 0
        for k, line in enumerate(lines):
            m = RE_BANNER.search(line)
            if not m:
                continue
            lines[k] = recentre(line, m.group(0), f"hithesis v{version}")
            hit += 1
        if hit:
            out = "\n".join(lines)
            p.write_bytes(out.encode("utf-8"))
            changed += hit
            print(f"  {p.relative_to(ROOT)}：横幅 {hit} 处")
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", metavar="VER", help="把所有地方改成这个版本号，如 3.2b")
    ap.add_argument("--date", metavar="YYYY/MM/DD",
                    help="同时写发布日期，不给就保持原样")
    ap.add_argument("--check", action="store_true", help="只检查一致性，不打印明细")
    args = ap.parse_args()

    if args.set:
        if not re.fullmatch(r"[0-9]+\.[0-9]+[a-z0-9.]*", args.set):
            print(f"版本号格式看着不对：{args.set}", file=sys.stderr)
            return 2
        if args.date and not re.fullmatch(r"\d{4}/\d{2}/\d{2}", args.date):
            print(f"日期格式应为 YYYY/MM/DD：{args.date}", file=sys.stderr)
            return 2
        print(f"版本号统一为 {args.set}" + (f"，日期 {args.date}" if args.date else ""))
        n = set_version(args.set, args.date)
        print(f"共改动 {n} 处。手册里的展示由 \\lstinputlisting 引自示例，跑 make doc 即可跟上。")
        return 0

    found = collect()
    if not args.check:
        for ver in sorted(found):
            print(f"v{ver}")
            for f, where in found[ver]:
                print(f"    {f}（{where}）")
    if len(found) > 1:
        print("版本号不一致，跑 scripts/version.py --set <版本> 同步。", file=sys.stderr)
        return 1
    if not args.check:
        print("各处版本号一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
