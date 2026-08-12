#!/usr/bin/env python3
"""校验两个类骨架里的装配表与 install 守卫一致。

src/hit-thesis.dtx 与 src/hit-report.dtx 开头各有一张装配表，列出这个类由
哪些文件按什么顺序拼出来。它是给开发者用的路标：想知道“章节标题在哪处理”，
打开叫 hit-thesis 的那个文件就能看到，不必去翻 install 守卫里那 101 条 \\from。

权威清单只有 install 守卫一份，装配表是副本。副本会陈旧，所以这里比对：
两边的“文件 + 守卫名”序列必须逐条相同。

用法：
    scripts/check-map.py          有出入时逐条列出并退出码 1
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DTX = ROOT / "src" / "hithesis.dtx"
PAIRS = [("src/hit-thesis.dtx", "hit-thesis.cls"),
         ("src/hit-report.dtx", "hit-report.cls")]


def locations() -> dict[str, str]:
    """dtx 文件名 -> 它在 src/ 下的相对路径。"""
    return {p.name: str(p.relative_to(ROOT / "src")) for p in (ROOT / "src").rglob("*.dtx")}


def from_install(cls: str) -> list[tuple[str, str]]:
    """install 守卫里这个输出的（路径，守卫名）序列。"""
    text = DTX.read_text(encoding="utf-8")
    blk = text[text.index("%<*install>"):text.rindex("%</install>")]
    start = blk.index("\\file{" + cls + "}{")
    end = blk.index("\n    }", start)
    loc = locations()
    out = []
    for f, g in re.findall(r"\\from\{([^}]*)\}\{([^}]*)\}", blk[start:end]):
        f = f.replace("\\jobname", "hithesis")
        out.append((loc.get(f, f), g))
    return out


def from_map(dtx: str) -> list[tuple[str, str]]:
    """骨架文件里装配表的（路径，守卫名）序列。"""
    out = []
    for line in (ROOT / dtx).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^% \^\^A\s+\d+\s+(\S+)\s+(\S+)", line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def main() -> int:
    problems = []
    for dtx, cls in PAIRS:
        want, got = from_install(cls), from_map(dtx)
        if not got:
            problems.append(dtx + " 里没找到装配表")
            continue
        if len(want) != len(got):
            problems.append("%s 的装配表 %d 条，install 守卫 %d 条" % (dtx, len(got), len(want)))
        for i, (w, g) in enumerate(zip(want, got), 1):
            if w != g:
                problems.append("%s 第 %d 条：装配表写的是 %s{%s}，install 守卫是 %s{%s}"
                                % (dtx, i, g[0], g[1], w[0], w[1]))
    if problems:
        print("装配表与 install 守卫对不上：\n")
        for p in problems:
            print("  - " + p)
        print("\n权威的是 src/hithesis.dtx 的 install 守卫，改完那边把装配表跟上。")
        return 1
    print("两张装配表与 install 守卫一致（%d + %d 条）"
          % (len(from_install("hit-thesis.cls")), len(from_install("hit-report.cls"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
