#!/usr/bin/env python3
"""把中文语境里的半角标点和引号统一成中文标点。

默认只报告不改，确认无误再加 --fix。

只在标点紧邻中日韩字符时才动它，英文句子里的半角标点保持原样。即便如此仍有大量
不能碰的地方，脚本会跳过：

- markdown 的围栏代码块与行内代码
- HTML 标签内部（``alt="知识共享许可协议"`` 这种属性值）
- URL
- LaTeX 源码（.dtx .lvt .ins .cls .sty）里的非注释行，以及注释里的 verbatim
  类命令（``\\file{}``、``\\texttt{}`` 等）
- dtx 的 shell/bibtex 示例环境

代码文件（.py .sh .lua .yml .lvt Makefile）里的注释也扫，但只改半角标点和引号
风格，不把 "..." 换成中文引号。那里的 " 是字符串定界符，换掉就坏。

用法::

    scripts/fix-punct.py                    # 扫仓库里所有带中文的散文与注释，只报告
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


def convert(text: str, quote_style: str, straight_quotes: bool = True) -> str:
    # 半角标点：前后任意一侧是中日韩字符才算中文语境
    for half, full in HALF_TO_FULL.items():
        h = re.escape(half)
        # 全角标点自带间距，后面跟的空格要一并吃掉
        text = re.sub(rf"(?<=[{CJK}]){h}[ \t]*(?=[{CJK}])", full, text, flags=re.M)
        text = re.sub(rf"(?<=[{CJK}]){h}(?=$)", full, text, flags=re.M)

    left, right = ("「", "」") if quote_style == "corner" else ("\u201c", "\u201d")
    # 成对的直引号，且内容含中日韩字符。代码文件里 " 是字符串定界符，不能动
    if straight_quotes:
        text = re.sub(rf'"([^"\n]*[{CJK}][^"\n]*)"', rf"{left}\1{right}", text)
    # \u5df2\u7ecf\u662f\u4e2d\u6587\u5f15\u53f7\u4f46\u98ce\u683c\u4e0d\u662f\u9009\u5b9a\u90a3\u79cd\u7684\uff0c\u4e5f\u4e00\u5e76\u7edf\u4e00\uff0c\u4e24\u79cd\u98ce\u683c\u4e92\u8f6c
    other_l, other_r = ("\u201c", "\u201d") if quote_style == "corner" else ("\u300c", "\u300d")
    text = re.sub(rf"{other_l}([^{other_r}\n]*){other_r}", rf"{left}\1{right}", text)
    return text


# 这些后缀的文件里，" 是字符串定界符或代码语法，只统一半角标点与引号风格，
# 不把 "..." 换成中文引号
CODE_SUFFIXES = {".lua", ".sh", ".py", ".yml", ".yaml", ".mk"}
CODE_NAMES = {"Makefile"}

# LaTeX 源码：只处理 % 开头的注释行。正文里的逗号常常是语法而非标点，
# 比如 \hitsetup{ckeywords={甲,乙,丙}} 的逗号是 \@for 的分隔符，换成全角
# 三个关键词就并成一个了。
LATEX_SUFFIXES = {".dtx", ".lvt", ".ins", ".cls", ".sty"}


def is_code(path: Path) -> bool:
    return path.suffix in CODE_SUFFIXES or path.name in CODE_NAMES


def convert_latex_comments(text: str, quote_style: str) -> str:
    """LaTeX 源码逐行处理，只动注释行。

    遮罩必须先在全文上做：示例环境是跨行的，逐行看根本认不出
    ``\\begin{bibtex}`` 到 ``\\end{bibtex}`` 是一整块。
    """
    masked, saved = mask(text)
    out = []
    for line in masked.split("\n"):
        if line.lstrip().startswith("%"):
            line = convert(line, quote_style)
        out.append(line)
    return unmask("\n".join(out), saved)


def default_targets() -> list[Path]:
    """散文与注释里带中文的文件，全都要过一遍。

    只列具体路径而不是无差别递归：examples/ 下是用户论文正文，
    标点风格由作者自己定；target/ 是构建产物。
    """
    globs = [
        "*.md", "*/*.md",
        "src/manual/hit-manual.dtx",
        "build.lua", "Makefile",
        ".github/workflows/*.yml",
        "scripts/*.py", "scripts/*.sh",
        "tools/*.sh",
        "testfiles/*.lvt",
    ]
    files: list[Path] = []
    for g in globs:
        files.extend(sorted(ROOT.glob(g)))
    # RELEASE_NOTES.md 是 make changes 生成的，改了下次就被覆盖；
    # 本脚本自身要同时保留两种引号的字面量，改了 --quotes corner 就失效
    generated = {"RELEASE_NOTES.md", "fix-punct.py"}
    seen: set[Path] = set()
    out = []
    for f in files:
        if f in seen or not f.is_file():
            continue
        seen.add(f)
        if "node_modules" in f.parts or "target" in f.parts or f.name in generated:
            continue
        out.append(f)
    return out


def changed_files() -> list[Path]:
    out = subprocess.run(["git", "diff", "--name-only", "HEAD"],
                         cwd=ROOT, capture_output=True, text=True).stdout.split()
    return [ROOT / f for f in out if f.endswith((".md", ".dtx")) and (ROOT / f).exists()]


def process(path: Path, quote_style: str, apply: bool) -> list[tuple[int, str, str]]:
    original = path.read_text(encoding="utf-8")
    if path.suffix in LATEX_SUFFIXES:
        result = convert_latex_comments(original, quote_style)
    else:
        masked, saved = mask(original)
        result = unmask(convert(masked, quote_style, straight_quotes=not is_code(path)), saved)
    if result == original:
        return []
    diffs = [(i, a, b) for i, (a, b) in
             enumerate(zip(original.splitlines(), result.splitlines()), 1) if a != b]
    if apply:
        path.write_text(result, encoding="utf-8")
    return diffs


def main() -> int:
    parser = argparse.ArgumentParser(description="统一中文语境下的标点与引号")
    parser.add_argument("files", nargs="*", help="指定文件；默认扫仓库里带中文的散文与注释")
    parser.add_argument("--fix", action="store_true", help="实际写回，默认只报告")
    parser.add_argument("--quotes", choices=["curly", "corner"], default="curly",
                        help="引号风格：curly 用 “”（默认，大陆通行），corner 用 「」")
    parser.add_argument("--changed", action="store_true", help="只处理相对 HEAD 有改动的文件")
    parser.add_argument("--check", action="store_true",
                        help="有可改之处就以退出码 1 结束，CI 当门禁用")
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
    elif args.check:
        print(f"\n共 {total} 行标点不合约定，跑 make punct-fix 修。")
        return 1
    else:
        print(f"\n共 {total} 行可改。确认无误后加 --fix 写回。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
