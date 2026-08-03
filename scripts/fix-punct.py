#!/usr/bin/env python3
"""把中文语境里的半角标点和引号统一成中文标点。

默认只报告不改，确认无误再加 --fix。

只在标点紧邻中日韩字符时才动它，英文句子里的半角标点保持原样。即便如此仍有大量
不能碰的地方，脚本会跳过：

- markdown 的围栏代码块与行内代码
- HTML 标签内部（``alt="知识共享许可协议"`` 这种属性值）
- URL
- dtx 里的非注释行，以及注释里的 verbatim 类命令（``\\file{}``、``\\texttt{}`` 等）
- dtx 的 shell/bibtex 示例环境

Python 和 shell 脚本整个不处理：里面的引号基本都是字符串定界符，换掉就坏。

用法::

    scripts/fix-punct.py                    # 扫 *.md 与 hithesis-doc.dtx，只报告
    scripts/fix-punct.py --fix              # 确认后实际修改
    scripts/fix-punct.py --quotes corner    # 引号改用「」，默认 curly（“”）
    scripts/fix-punct.py --changed          # 只看相对 HEAD 有改动的文件
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CJK = "\u4e00-\u9fff\u3000-\u303f\uff00-\uffef"
HALF_TO_FULL = {",": "，", ";": "；", "?": "？", "!": "！", ":": "："}

# 这些区间一律不碰，记下来后用占位符挡住
SKIP_PATTERNS = [
    re.compile(r"^```.*?^```", re.S | re.M),      # markdown 围栏代码块
    re.compile(r"`[^`\n]+`"),                     # markdown 行内代码
    re.compile(r"<[^>\n]+>"),                     # HTML 标签
    re.compile(r"https?://\S+"),                  # URL
    re.compile(r"\\(?:file|texttt|pkg|cs|verb|url|href)\{[^}\n]*\}"),
    re.compile(r"\\begin\{(latex|shell|verbatim|lstlisting)\}.*?\\end\{\1\}", re.S),
]


def mask(text: str) -> tuple[str, list[str]]:
    """把不该处理的片段换成占位符，返回替换后的文本和原片段。"""
    saved: list[str] = []

    def keep(m: re.Match) -> str:
        saved.append(m.group(0))
        return f"\x00{len(saved) - 1}\x00"

    for pat in SKIP_PATTERNS:
        text = pat.sub(keep, text)
    return text, saved


def unmask(text: str, saved: list[str]) -> str:
    # 遮罩会嵌套（URL 先被挡住，外层的 \href{...} 又把它连同占位符一起挡住），
    # 所以要反复展开到不再有占位符为止。
    for _ in range(len(saved) + 1):
        new = re.sub(r"\x00(\d+)\x00", lambda m: saved[int(m.group(1))], text)
        if new == text:
            return text
        text = new
    return text


def convert(text: str, quote_style: str) -> str:
    # 半角标点：前后任意一侧是中日韩字符才算中文语境
    for half, full in HALF_TO_FULL.items():
        h = re.escape(half)
        # 全角标点自带间距，后面跟的空格要一并吃掉
        text = re.sub(rf"(?<=[{CJK}]){h}[ \t]*(?=[{CJK}])", full, text, flags=re.M)
        text = re.sub(rf"(?<=[{CJK}]){h}(?=$)", full, text, flags=re.M)

    left, right = ("「", "」") if quote_style == "corner" else ("\u201c", "\u201d")
    # 成对的直引号，且内容含中日韩字符
    text = re.sub(rf'"([^"\n]*[{CJK}][^"\n]*)"', rf"{left}\1{right}", text)
    if quote_style == "corner":
        text = re.sub(rf"\u201c([^\u201d\n]*[{CJK}][^\u201d\n]*)\u201d", rf"{left}\1{right}", text)
    return text


def default_targets() -> list[Path]:
    files = sorted(ROOT.glob("*.md")) + sorted(ROOT.glob("*/*.md"))
    doc = ROOT / "src" / "hithesis-doc.dtx"
    if doc.exists():
        files.append(doc)
    # RELEASE_NOTES.md 是 make changes 生成的，改了下次就被覆盖
    generated = {"RELEASE_NOTES.md"}
    return [f for f in files
            if "node_modules" not in f.parts and "target" not in f.parts
            and f.name not in generated]


def changed_files() -> list[Path]:
    out = subprocess.run(["git", "diff", "--name-only", "HEAD"],
                         cwd=ROOT, capture_output=True, text=True).stdout.split()
    return [ROOT / f for f in out if f.endswith((".md", ".dtx")) and (ROOT / f).exists()]


def process(path: Path, quote_style: str, apply: bool) -> list[tuple[int, str, str]]:
    original = path.read_text(encoding="utf-8")
    masked, saved = mask(original)
    result = unmask(convert(masked, quote_style), saved)
    if result == original:
        return []
    diffs = [(i, a, b) for i, (a, b) in
             enumerate(zip(original.splitlines(), result.splitlines()), 1) if a != b]
    if apply:
        path.write_text(result, encoding="utf-8")
    return diffs


def main() -> int:
    parser = argparse.ArgumentParser(description="统一中文语境下的标点与引号")
    parser.add_argument("files", nargs="*", help="指定文件；默认 *.md 与 hithesis-doc.dtx")
    parser.add_argument("--fix", action="store_true", help="实际写回，默认只报告")
    parser.add_argument("--quotes", choices=["curly", "corner"], default="curly",
                        help="引号风格：curly 用 “”（默认，大陆通行），corner 用 「」")
    parser.add_argument("--changed", action="store_true", help="只处理相对 HEAD 有改动的文件")
    args = parser.parse_args()

    if args.files:
        targets = [Path(f) for f in args.files]
    elif args.changed:
        targets = changed_files()
    else:
        targets = default_targets()

    total = 0
    for path in targets:
        if not path.exists():
            print(f"跳过不存在的 {path}")
            continue
        diffs = process(path, args.quotes, args.fix)
        if not diffs:
            continue
        total += len(diffs)
        print(f"\n{path.relative_to(ROOT) if path.is_absolute() else path}（{len(diffs)} 行）")
        for lineno, before, after in diffs[:10]:
            print(f"  L{lineno}")
            print(f"    - {before.strip()[:88]}")
            print(f"    + {after.strip()[:88]}")
        if len(diffs) > 10:
            print(f"  …… 另有 {len(diffs) - 10} 行")

    if total == 0:
        print("没有需要修改的地方。")
    elif args.fix:
        print(f"\n已修改 {total} 行。")
    else:
        print(f"\n共 {total} 行可改。确认无误后加 --fix 写回。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
