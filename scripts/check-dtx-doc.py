#!/usr/bin/env python3
"""检查 dtx 注释里的文档宏用法。

注释里写错宏名不影响 .cls 的生成，只在 make doc 时才暴露，而 make doc 要跑一分多钟。
这个脚本几秒钟出结果，用来在提交前先挡一道。

两类检查：

1. 硬错误。已经踩过的写法，直接判失败：
   - \\opt{}      本项目没有这个宏，应为 \\option{}
   - \\cs{} 的参数里有未转义的下划线，ltxdoc 下 _ 是数学下标，要写 \\_

2. 新出现的命令。注释里用到的命令与 .github/dtx-doc-macros.txt 比对，多出来的
   列出来让人确认。确认没问题就用 --update 把它写进基线。

用法::

    scripts/check-dtx-doc.py            # 检查，有问题返回非零
    scripts/check-dtx-doc.py --update   # 把当前用到的命令写回基线
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / ".github" / "dtx-doc-macros.txt"

# 已知写错的宏：错误写法 -> 正确写法。
# 只收录确认过的，别凭印象加：\cls 看着像不存在，其实是 dtx-style.sty 用
# \DeclareDocumentCommand 定义的，加进来就成了误报。
BAD_MACROS = {
    "opt": "option",
}


def comment_lines(path: Path):
    """产出 (行号，注释正文)。跳过 docstrip 守卫与 ^^A 内部注记。"""
    for i, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = ln.strip()
        if not s.startswith("%") or s.startswith("%<"):
            continue
        body = s.lstrip("%").strip()
        if body.startswith("^^A"):
            continue
        yield i, body


def scan(paths):
    errors = []
    used = set()
    for p in paths:
        for lineno, body in comment_lines(p):
            for m in re.finditer(r"\\([a-zA-Z@]+)", body):
                used.add(m.group(1))
                if m.group(1) in BAD_MACROS:
                    errors.append(
                        (p, lineno, f"\\{m.group(1)}{{}} 本项目没有，应为 "
                                    f"\\{BAD_MACROS[m.group(1)]}{{}}"))
            for m in re.finditer(r"\\cs\{([^}]*)\}", body):
                if re.search(r"(?<!\\)_", m.group(1)):
                    errors.append(
                        (p, lineno, f"\\cs{{{m.group(1)}}} 里的下划线要转义成 \\_，"
                                    "ltxdoc 下 _ 是数学下标"))
    return errors, used


def main() -> int:
    ap = argparse.ArgumentParser(description="检查 dtx 注释里的文档宏用法")
    ap.add_argument("files", nargs="*", help="指定文件，默认 src/*.dtx")
    ap.add_argument("--update", action="store_true", help="把当前用到的命令写回基线")
    args = ap.parse_args()

    paths = [Path(f) for f in args.files] if args.files else sorted(ROOT.glob("src/*.dtx"))
    errors, used = scan(paths)

    if args.update:
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(
            "# dtx 注释里用到的命令清单，由 scripts/check-dtx-doc.py --update 生成。\n"
            "# 新增命令时脚本会提示，确认 make doc 能过之后再更新本文件。\n"
            + "\n".join(sorted(used)) + "\n", encoding="utf-8")
        print(f"基线已更新，收录 {len(used)} 个命令")
        return 0

    known = set()
    if BASELINE.exists():
        known = {l.strip() for l in BASELINE.read_text(encoding="utf-8").splitlines()
                 if l.strip() and not l.startswith("#")}

    for p, ln, msg in errors:
        print(f"{p.relative_to(ROOT)}:{ln}: {msg}")

    new = sorted(used - known) if known else []
    if new:
        print(f"\n注释里出现了 {len(new)} 个基线里没有的命令：")
        print("  " + "  ".join("\\" + n for n in new))
        print("跑一遍 make doc 确认能编过，然后 scripts/check-dtx-doc.py --update 收进基线。")

    if errors:
        print(f"\n共 {len(errors)} 处硬错误。")
        return 1
    if new:
        return 1
    print(f"dtx 注释检查通过（{len(paths)} 个文件，{len(used)} 个命令）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
