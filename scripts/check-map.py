#!/usr/bin/env python3
"""生成并校验两个类骨架里的装配表。

src/hit-thesis.dtx 与 src/hit-report.dtx 开头各有一张装配表，列出这个类由
哪些文件按什么顺序拼出来。它是给开发者用的路标：想知道“章节标题在哪处理”，
打开叫 hit-thesis 的那个文件就能看到，不必去翻 install 守卫里那 101 条 \\from。

权威清单只有 src/hithesis.dtx 的 install 守卫一份，装配表是它的产物，
别手改。改完 install 守卫跑一次 --fix 重新生成。

守卫名到一句话说明的对照写在下面的 DESC 里。新加的守卫这里没有条目的话，
说明栏留空，--check 会点名，补一条就是。

用法：
    scripts/check-map.py            两边比对，有出入时逐条列出并退出码 1
    scripts/check-map.py --fix      按 install 守卫重新生成两张表
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DTX = ROOT / "src" / "hithesis.dtx"
PAIRS = [("src/hit-thesis.dtx", "hit-thesis.cls", "学位论文类 hit-thesis"),
         ("src/hit-report.dtx", "hit-report.cls", "开题中期报告类 hit-report")]

OPEN = "% ^^A ---8<--- 装配表由 scripts/check-map.py --fix 生成，别手改 ---8<---"
CLOSE = "% ^^A ---8<--- 装配表到此 ---8<---"

DESC = {
    "thesiscls": "类文件头：\\NeedsTeXFormat、\\ProvidesExplClass",
    "reportcls": "类文件头：\\NeedsTeXFormat、\\ProvidesExplClass",
    "shared-defaults": "常量默认值，只记进队列不执行",
    "shared-messages": "面向用户的提示文案",
    "shared-lang": "支持哪几种语言",
    "shared-fonts": "字号命令与字体族",
    "shared-math": "数学与定理环境",
    "shared-table": "长表格字号",
    "shared-footnote": "脚注格式",
    "shared-list": "列表间距与 publist 环境",
    "shared-hyperlink": "超链接基础设施",
    "shared-title": "题目的分行与副标题",
    "shared-spread": "定宽拉伸排字",
    "shared-date": "中文日期格式",
    "shared-msword": "Word 页面设置换算成版面参数",
    "shared-format": "元素格式：字体、行距、间距、缩进",
    "shared-caption": "题注与双语题注",
    "shared-subfigure": "子图",
    "shared-key-engine": "键怎么造、怎么存、旧名怎么兼容",
    "shared-option-engine": "类选项怎么声明、标志位怎么读",
    "shared-bibstyle": "参考文献样式的开关",
    "shared-structure": "struct 族的部件与分段",
    "shared-keylist": "有哪些信息字段与常量",
    "thesis-options": "文档类选项：声明、默认值、\\ProcessKeyOptions 之后的后处理",
    "report-options": "同上",
    "thesiscls-load": "★ \\LoadClass{ctexbook}，分水岭",
    "reportcls-load": "★ \\LoadClass{ctexart}，分水岭",
    "thesis-fonts": "正文字号与主字体",
    "report-fonts": "正文字号与主字体",
    "thesis-pagestyle": "页眉页脚",
    "report-pagestyle": "页眉页脚",
    "thesis-cover": "封面",
    "report-cover": "封面（内含目录）",
    "thesis-abstract": "摘要",
    "thesis-toc-lists": "图表目录",
    "thesis-chapter": "章节标题",
    "report-chapter": "章节标题",
    "thesis-bib": "参考文献版式",
    "report-bib": "参考文献版式",
    "thesis-appendix": "附录",
    "thesis-backmatter": "成果、索引、简历",
    "thesis-statement": "原创性声明",
    "thesis-resolution": "答辩决议",
    "thesis-deps": "多模块共用的第三方宏包",
    "report-deps": "多模块共用的第三方宏包",
    "thesis-hyperlink": "hyperref 配置，排在所有包之后",
    "report-hyperlink": "hyperref 配置，排在所有包之后",
    "thesis-geometry": "版心，提前定下来",
    "report-geometry": "版心，提前定下来",
    "thesis-glossary": "术语与符号表",
    "report-subfig": "子图兼容层",
    "thesis-mainmatter": "骨架宏与前后文切换",
    "report-matter": "骨架宏",
    "thesis-paragraph": "段落",
    "thesis-footnote": "脚注",
    "thesis-math": "公式断行",
    "thesis-floats": "浮动体",
    "report-floats": "浮动体",
    "thesis-toc": "目录版式",
    "report-toc": "目录版式",
    "thesiscls-tail": "★ \\AtEndOfClass 钩子",
    "reportcls-tail": "★ \\AtEndOfClass 钩子",
    "thesiscfg": "★ 回放配置队列 \\hit@apply@presetup",
    "reportcfg": "★ 回放配置队列 \\hit@apply@presetup",
}


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


def render(cls: str, title: str) -> list[str]:
    """按 install 守卫排出装配表的全部行。"""
    bar = "% ^^A " + "=" * 70
    lines = [OPEN, bar, "% ^^A " + title + " 的装配表", "% ^^A",
             "% ^^A 这个类由下面这些文件按这个顺序拼出来。权威清单在 src/hithesis.dtx",
             "% ^^A 的 install 守卫里，这张表是它的产物，改完那边跑 make mapfix。",
             "% ^^A \\from 的书写顺序就是各块在 cls 里出现的顺序，与守卫在各 dtx 里的",
             "% ^^A 位置无关。★ 标的几块在本文件里，其余在 setup/ utils/ flow/ pages/ 下。",
             bar]
    for n, (path, guard) in enumerate(from_install(cls), 1):
        lines.append("%% ^^A %2d  %-32s %-24s %s"
                     % (n, path, guard, DESC.get(guard.split(",")[0], "")))
    lines += [bar, CLOSE]
    return [l.replace("%%", "%", 1) if l.startswith("%%") else l for l in lines]


def current(dtx: str) -> tuple[list[str], int, int] | None:
    """骨架里现有的装配表与它的行号范围。"""
    lines = (ROOT / dtx).read_text(encoding="utf-8").splitlines()
    try:
        a = lines.index(OPEN)
        b = lines.index(CLOSE)
    except ValueError:
        return None
    return lines[a:b + 1], a, b


def fix() -> int:
    for dtx, cls, title in PAIRS:
        p = ROOT / dtx
        lines = p.read_text(encoding="utf-8").splitlines()
        want = render(cls, title)
        got = current(dtx)
        if got is None:
            # 还没有表，插在文件头注释之后、第一个守卫之前
            k = next(i for i, l in enumerate(lines)
                     if l.startswith("%<*") or l.startswith("%    \\begin{macrocode}"))
            while k > 0 and lines[k - 1].strip() in ("%", ""):
                k -= 1
            lines[k:k] = want + ["%"]
        else:
            _, a, b = got
            lines[a:b + 1] = want
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("  %s 的装配表已重新生成（%d 条）" % (dtx, len(from_install(cls))))
    return 0


def check() -> int:
    problems = []
    for dtx, cls, title in PAIRS:
        got = current(dtx)
        if got is None:
            problems.append(dtx + " 里没找到装配表，跑 make mapfix")
            continue
        if got[0] != render(cls, title):
            problems.append(dtx + " 的装配表与 install 守卫不一致，跑 make mapfix")
        for _, guard in from_install(cls):
            if guard.split(",")[0] not in DESC:
                problems.append("守卫 %s 在 scripts/check-map.py 的 DESC 里没有说明，补一条"
                                % guard)
    if problems:
        print("装配表对不上：\n")
        for p in problems:
            print("  - " + p)
        return 1
    print("两张装配表与 install 守卫一致（%d + %d 条）"
          % (len(from_install("hit-thesis.cls")), len(from_install("hit-report.cls"))))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="生成并校验类骨架里的装配表")
    parser.add_argument("--fix", action="store_true", help="按 install 守卫重新生成")
    args = parser.parse_args()
    return fix() if args.fix else check()


if __name__ == "__main__":
    sys.exit(main())
