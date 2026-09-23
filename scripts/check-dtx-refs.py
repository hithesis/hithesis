#!/usr/bin/env python3
"""校验 dtx 注释里的 \\file{src/...} 交叉引用指向真实存在的文件。

正文注释里常写“这套机制在 \\file{src/docxlike/docxlike-format.dtx}”这样的路标。文件
改名或合并之后这些引用不会自动跟着走，也没有任何东西会报错——它只是注释。
2026-09-13 扫出 11 处悬空，分别指向 hit-meta.dtx 与 hit-publist.dtx，两个文件
在 v3.2a 中途就并掉了，机制分别进了 engine/hit-key-engine.dtx 与 engine/hit-list.dtx。

只认 \\file{src/...} 这一种形态。\\file{hithesis.cfg} 这类产物名、changes 条目里
提到的历史文件名（“原先在 hithesisartplus.cls 里”）都不在此列——前者不是源码
路径，后者本来就该是历史。带 \\* 的通配写法（\\file{src/flow/hit-*-deps.dtx}，指
“两个类各自那一份”）按通配匹配，能匹到至少一个就算数。

跑法：python3 scripts/check-dtx-refs.py    有悬空退出码 1
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REF = re.compile(r"\\file\{(src/[^}]+)\}")


def main() -> int:
    bad: list[tuple[str, int, str]] = []
    total = 0
    for f in sorted(ROOT.glob("src/**/*.dtx")):
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for m in REF.finditer(line):
                ref = m.group(1)
                total += 1
                if "*" in ref:
                    if not list(ROOT.glob(ref)):
                        bad.append((str(f.relative_to(ROOT)), n, ref))
                    continue
                if not (ROOT / ref).exists():
                    bad.append((str(f.relative_to(ROOT)), n, ref))
    if bad:
        print(f"{len(bad)} 处交叉引用指向不存在的文件：")
        for f, n, ref in bad:
            print(f"  {f}:{n}  {ref}")
        print()
        print("文件改名或合并时把引用一起改掉；机制搬家了就指向它现在的落点。")
        return 1
    print(f"dtx 交叉引用全部有效（共 {total} 处）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
