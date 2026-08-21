#!/usr/bin/env python3
"""核对公开面清单，新增的公开宏必须先登记。

LaTeX 没有模块作用域。类里定义的宏，名字不带 @ 也不带 _ : 的，用户在正文里就能
直接调用，等于公开接口。写一句 \\NewDocumentCommand 就把它交出去了，没有任何东西
拦一下问“这个是有意公开的吗”。

这个脚本做两件事：

1. 从生成的 cls 里扫出所有定义点，去掉 hit@ 与 __hit_ 前缀的，剩下的就是能被用户
   打出来的名字。
2. 跟 .github/public-api.txt 对一遍。清单里没有的，报错。

“新增”和“重定义”怎么分：装上 hithesis 用的同一套宏包但不装 hithesis，逐个
\\ifdefined 探一遍。上游已经有的是重定义（名字必须保持原样，改了上游就找不到），
上游没有的是 hithesis 新增（那才是真正的接口决策）。探测要跑 xelatex，慢，所以
结果缓存在清单文件里，只有 --probe 才重新探。

跑法：make cls 之后 python3 scripts/check-api.py
     加 --probe 重新探测上游（改了 \\RequirePackage 清单之后要跑一次）
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / ".github" / "public-api.txt"
CLASSES = ("hit-thesis.cls", "hit-report.cls")
# 示例宏包。它的名字也在公开面上，但不是类给的：用户不写 \usepackage{hithesis}
# 就没有。单列一节，免得跟类提供的混在一起。
STY = "hithesis.sty"
STY_SECTION = "示例宏包"

# 各种定义形式。\cs_new 与 \NewDocumentCommand 遇到已存在的名字会报错，
# \cs_set 与 \Renew… 不会，两类都要认：重定义上游命令同样落在公开面上。
DEFINE = re.compile(
    r"\\(?:cs_new(?:_protected)?(?:_nopar)?:(?:Npn|cpn)"
    r"|cs_set(?:_protected)?(?:_nopar)?:(?:Npn|cpn)"
    r"|New(?:Expandable)?DocumentCommand|RenewDocumentCommand|DeclareRobustCommand"
    r"|newcommand\*?|renewcommand\*?|def|gdef"
    r"|NewDocumentEnvironment|RenewDocumentEnvironment|newenvironment\*?|renewenvironment\*?"
    r"|newfloatlist|newfixedcaption)\s*\\?\{?\\([a-zA-Z]+)"
)

# 正则在 @ 处截断留下的残片，不是真名字
JUNK = {"CJK", "CTEX", "LT", "NAT", "ext", "make", "p", "tagform", "def", "bibstyle"}


def scan(name):
    """一个生成物里所有用户能打出来的定义名"""
    out = set()
    if True:
        path = ROOT / name
        if not path.exists():
            sys.exit(f"{name} 还没生成，先跑 make cls")
        for line in path.read_text(encoding="utf-8").split("\n"):
            if line.startswith("%"):
                continue
            for m in DEFINE.finditer(line):
                n = m.group(1)
                # hit@ 与 __hit_ 开头的用户打不出来，不算公开面。
                # 但 hitsetup 这类不带 @ 的仍旧是，别一起滤掉。
                if n.startswith("hit@") or n.startswith("__hit"):
                    continue
                if n not in JUNK:
                    out.add(n)
    return out


def defined_names():
    """两个类给的名字"""
    return set().union(*(scan(c) for c in CLASSES))


def listed():
    """清单里登记过的名字，连同它在哪一节"""
    out = {}
    section = None
    for line in LIST.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("["):
            section = line.split("]")[0][1:]
            continue
        out[line] = section
    return out


def probe(names):
    """装同一套宏包但不装 hithesis，看哪些名字上游已经有了"""
    # 两个类的宏包都要，条件加载的也算。花括号与方括号里可能有空格
    # （\RequirePackage [ xindy , order=letter ] { glossaries-extra }），
    # 正则不放行空格就会漏掉，漏掉的包会让它的命令被误判成 hithesis 新增。
    src = "\n".join((ROOT / c).read_text(encoding="utf-8") for c in CLASSES)
    pkgs = sorted({p.strip()
                   for m in re.finditer(r"\\RequirePackage\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}", src)
                   for p in m.group(1).split(",") if p.strip()})
    with tempfile.TemporaryDirectory() as d:
        tex = Path(d) / "probe.tex"
        body = [r"\documentclass[a4paper,openany,UTF8,zihao=-4,scheme=plain,fontset=fandol]{ctexbook}"]
        body += [r"\usepackage{%s}" % p for p in pkgs]
        body.append(r"\makeatletter\begin{document}")
        body += [r"\typeout{[P] %s \ifdefined\%s HAS\else NEW\fi}" % (n, n) for n in sorted(names)]
        body.append(r"\end{document}")
        tex.write_text("\n".join(body), encoding="utf-8")
        subprocess.run(["xelatex", "-interaction=nonstopmode", "probe.tex"],
                       cwd=d, capture_output=True)
        log = (Path(d) / "probe.log").read_text(encoding="utf-8", errors="replace")
    return {m.group(1): m.group(2)
            for m in re.finditer(r"\[P\] ([a-zA-Z]+) (HAS|NEW)", log)}


def main() -> int:
    names = defined_names()
    sty_names = scan(STY)
    reg = listed()
    cls_reg = {n for n, s in reg.items() if s != STY_SECTION}
    sty_reg = {n for n, s in reg.items() if s == STY_SECTION}
    missing = sorted((names - cls_reg) | (sty_names - sty_reg))
    stale = sorted((cls_reg - names) | (sty_reg - sty_names))
    misplaced = sorted((names & sty_reg) | (sty_names & cls_reg))

    if "--probe" in sys.argv:
        r = probe(names)
        print(f"探测了 {len(r)} 个：上游已有 {sum(1 for v in r.values() if v == 'HAS')}，"
              f"hithesis 新增 {sum(1 for v in r.values() if v == 'NEW')}")
        for n in missing:
            print(f"  {n} 未登记，探测结果 {r.get(n, '?')}")
        return 0

    for n in missing:
        print(f"{n} 定义在类里但不在公开面清单上。它是能被用户打出来的名字，"
              f"要么登记进 .github/public-api.txt，要么改名带上 hit@ 前缀")
    for n in stale:
        print(f"{n} 在清单上但生成物里已经没有了，从清单里删掉")
    for n in misplaced:
        where = "示例宏包" if n in sty_names else "类"
        print(f"{n} 现在由{where}提供，清单上的分节对不上，挪到对的那一节")
    todo = [n for n, s in reg.items() if s.startswith("公开-")]
    print(f"公开面：登记 {len(reg)} 个，其中还欠文档 {len(todo)} 个；"
          f"类里实有 {len(names)} 个，示例宏包 {len(sty_names)} 个")
    return 1 if (missing or stale or misplaced) else 0


if __name__ == "__main__":
    sys.exit(main())
