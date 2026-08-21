#!/usr/bin/env python3
"""查每个第三方宏包是不是在该在的地方。

宏包按三条规矩分家：

    \\RequirePackage 之后类自己不调，纯粹替用户预装  → src/hit-sty.dtx（出 hithesis.sty）
    类自己调，两个以上模块调                          → deps
    类自己调，只有一个模块调                          → 就在那个模块里 \\RequirePackage

哪个包归哪儿、为什么，一条不落地写在 tools/deps-policy.txt。本脚本不猜，只比对：
代码里 \\RequirePackage 了什么，策略表说该在哪，两边对不上就报出来。新加一个包却
没在策略表里交代，也报。

这样做而不是去扒宏包提供了哪些宏，是因为那条路走不通：\\includegraphics 定义在
graphics.sty 而不是 graphicx.sty，subcaption 的环境由 caption 的机制造出来，
hyperref 重定义了 \\label 与 \\ref。扒出来的名单假阴假阳都有，据此说「这个包没人用，
挪进 sty 吧」会把能编的类改坏。判断交给人，脚本只保证判断被写下来且没过期。

用法：
    scripts/check-deps.py           查，有出入逐条列出并退出码 1
    scripts/check-deps.py --list    按当前代码打印一份策略表骨架，加包时拿它起草
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DTX = ROOT / "src" / "hithesis.dtx"
POLICY = ROOT / "tools" / "deps-policy.txt"
STY = "src/hit-sty.dtx"
OUTPUTS = ["hit-thesis.cls", "hit-report.cls"]
DEPS = {"flow/hit-thesis-deps.dtx", "flow/hit-report-deps.dtx"}

REQ = re.compile(r"\\RequirePackage\s*(?:\[[^\]]*\])?\s*\{\s*([a-zA-Z0-9\-&]+)\s*\}")

# 归了 sty 的包，类里一处都不该引用。这条反向检查扒出宏包新造了哪些名字，
# 再回头扫类的代码。
#
# 只认 \new... 这一族：它们在名字已存在时会报错，所以出现即意味着这个名字是本包
# 造的。\def 与 \renewcommand 不认，那两个改的往往是别人的东西——listings 里就有
# 一句 \def\vskip{...}，认了它会说“listings 归了 sty 可类里在用 \vskip”。
DEF_NEW = re.compile(
    r"\\newcommand\s*\*?\s*\{?(\\[a-zA-Z@_:]+)"
    r"|\\(?:New|Provide)DocumentCommand\s*\{?\s*(\\[a-zA-Z@_:]+)"
    r"|\\new(?:length|dimen|skip|count|toks|savebox)\s*\{?(\\[a-zA-Z@_:]+)"
    r"|\\newenvironment\s*\*?\s*\{\s*([a-zA-Z@*]+)\s*\}"
    r"|\\(?:New|Provide)DocumentEnvironment\s*\{\s*([a-zA-Z@*]+)\s*\}"
)

# 排除用的这条要宽：内核与基类里 \@makecaption 这类是 \def 定义的，
# 认不出来就会把类里正常的重定义当成宏包泄漏报出去
DEF_ANY = re.compile(
    DEF_NEW.pattern
    + r"|\\(?:re)?newcommand\s*\*?\s*\{?(\\[a-zA-Z@_:]+)"
      r"|\\DeclareRobustCommand\s*\*?\s*\{?(\\[a-zA-Z@_:]+)"
      r"|\\(?:long\s*)?\\?def\s*(\\[a-zA-Z@_:]+)"
      r"|\\renewenvironment\s*\*?\s*\{\s*([a-zA-Z@*]+)\s*\}"
)

# 内核与基类早就有的名字，谁重定义都不算它提供
BASE_SOURCES = ["latex.ltx", "book.cls", "article.cls", "ctexbook.cls", "ctexart.cls",
                "ctex.sty", "ctexhook.sty", "xeCJK.sty"]


def install_map() -> dict[str, list[tuple[str, str]]]:
    """输出文件 -> [(dtx 相对 src 的路径，守卫名)]，顺序就是装配顺序。"""
    text = DTX.read_text(encoding="utf-8")
    blk = text[text.index("%<*install>"):text.rindex("%</install>")]
    loc = {p.name: str(p.relative_to(ROOT / "src")) for p in (ROOT / "src").rglob("*.dtx")}
    out = {}
    for cls in OUTPUTS:
        start = blk.index("\\file{" + cls + "}{")
        end = blk.index("\n    }", start)
        seq = []
        for f, guards in re.findall(r"\\from\{([^}]*)\}\{([^}]*)\}", blk[start:end]):
            f = f.replace("\\jobname", "hithesis")
            for g in guards.split(","):
                seq.append((loc.get(f, f), g.strip()))
        out[cls] = seq
    return out


def guard_code(path: str, guard: str) -> str:
    """一个 dtx 里某个守卫圈住的代码，注释行不算。"""
    keep, inside = [], False
    for line in (ROOT / "src" / path).read_text(encoding="utf-8").splitlines():
        if line.startswith("%<*" + guard + ">"):
            inside = True
        elif line.startswith("%</" + guard + ">"):
            inside = False
        elif inside and not line.startswith("%"):
            keep.append(line)
    return "\n".join(keep)


def actual() -> dict[str, set[str]]:
    """包名 -> 它实际在哪些位置被 \\RequirePackage。位置写成 deps / sty / 模块路径。"""
    out: dict[str, set[str]] = {}
    for _cls, seq in install_map().items():
        for path, guard in seq:
            spot = "deps" if path in DEPS else path
            for pkg in REQ.findall(guard_code(path, guard)):
                out.setdefault(pkg, set()).add(spot)
    for pkg in REQ.findall(guard_code("hit-sty.dtx", "hit-sty")):
        out.setdefault(pkg, set()).add("sty")
    return out


def sty_duplicates() -> list[str]:
    """hithesis.sty 里同一个包装了两回。"""
    seen: dict[str, int] = {}
    for pkg in REQ.findall(guard_code("hit-sty.dtx", "hit-sty")):
        seen[pkg] = seen.get(pkg, 0) + 1
    return sorted(p for p, n in seen.items() if n > 1)


def policy() -> dict[str, tuple[set[str], str]]:
    """策略表：包名 -> （该在哪些位置，理由）。"""
    if not POLICY.exists():
        return {}
    out: dict[str, tuple[set[str], str]] = {}
    last = None
    for raw in POLICY.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0].isspace():
            # 缩进行是上一条理由的续行
            if last:
                spots, why = out[last]
                out[last] = (spots, (why + " " + raw.strip()).strip())
            continue
        parts = raw.split(None, 2)
        pkg = parts[0]
        spots = set(parts[1].split("+")) if len(parts) > 1 else set()
        out[pkg] = (spots, parts[2].strip() if len(parts) > 2 else "")
        last = pkg
    return out


def names_in(path: Path, rx: re.Pattern) -> set[str]:
    """一个 sty/cls 定义了哪些宏名与环境名，环境名也按宏名存。"""
    out = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.split("%")[0]
        for m in rx.finditer(line):
            g = next(x for x in m.groups() if x)
            out.add(g if g.startswith("\\") else "\\" + g)
    # expl3 的内部名不算对外接口，长度太短的重名风险太大
    return {n for n in out if len(n) > 3 and "_" not in n and ":" not in n}


_base: set[str] | None = None


_no_kpse = False


def kpse(name: str) -> str:
    """kpsewhich 查一个文件。没装 TeX Live 就返回空串，不炸。

    “changes 日期约定”那个 CI job 只跑 python，不装 TeX Live，从前在这里
    直接 FileNotFoundError。策略表比对本身不需要 kpsewhich，只有下面查
    “归了 sty 却被类调用”那一道要读宏包源码，查不到就跳过并说一声。
    """
    global _no_kpse
    if _no_kpse:
        return ""
    try:
        r = subprocess.run(["kpsewhich", name], capture_output=True, text=True)
    except (FileNotFoundError, OSError):
        _no_kpse = True
        return ""
    return r.stdout.strip()


def base_names() -> set[str]:
    global _base
    if _base is None:
        _base = set()
        for f in BASE_SOURCES:
            found = kpse(f)
            if found:
                _base |= names_in(Path(found), DEF_ANY)
    return _base


def sty_leaks() -> list[str]:
    """归了 sty 的包，类里却在用它提供的东西。"""
    sty_pkgs = sorted(p for p, (spots, _w) in policy().items() if spots == {"sty"})
    blocks = [(p, g) for seq in install_map().values() for p, g in seq]
    code = {p: guard_code(p, g) for p, g in blocks}
    out = []
    for pkg in sty_pkgs:
        found = kpse(pkg + ".sty")
        if not found:
            continue
        for name in sorted(names_in(Path(found), DEF_NEW) - base_names()):
            # expl3 下写成 \begin { name }，中间有空格，两种都要认
            pat = re.compile(re.escape(name) + r"(?![a-zA-Z@])"
                             r"|\\begin\s*\{\s*" + re.escape(name[1:]) + r"\s*\}")
            for path, text in code.items():
                if "deps" in path:
                    continue
                if pat.search(text):
                    out.append("%s 归了 sty，可 %s 里在用它的 %s。"
                               "类要用就得由类加载" % (pkg, path, name))
                    break
    return out


def check() -> int:
    got, want = actual(), policy()
    problems = []

    for pkg in sorted(set(got) | set(want)):
        if pkg not in want:
            problems.append("%s 加进来了，但 tools/deps-policy.txt 里没交代。"
                            "按文件头那三条规矩想清它归哪儿，补一行" % pkg)
            continue
        if pkg not in got:
            problems.append("%s 在 tools/deps-policy.txt 里还留着，代码里已经没有了，删掉那行" % pkg)
            continue
        spots, why = want[pkg]
        if spots != got[pkg]:
            problems.append("%s 策略表说在 %s，实际在 %s"
                            % (pkg, "+".join(sorted(spots)), "+".join(sorted(got[pkg]))))
        if not why:
            problems.append("%s 在策略表里没写理由，补一句为什么放那儿" % pkg)
        if "sty" in got[pkg] and len(got[pkg]) > 1:
            problems.append("%s 类和 hithesis.sty 都装了。类要用就留类里，"
                            "用户才要用就只留 sty" % pkg)

    for pkg in sty_duplicates():
        problems.append("%s 在 src/hit-sty.dtx 里装了不止一次" % pkg)

    problems += sty_leaks()

    if problems:
        print("宏包归属对不上：\n")
        for p in problems:
            print("  - " + p)
        print("\n三条规矩见 scripts/check-deps.py 文件头，"
              "起草新条目跑 scripts/check-deps.py --list。")
        return 1
    print("%d 个宏包都在 tools/deps-policy.txt 说的位置" % len(want))
    if _no_kpse:
        print("（没找到 kpsewhich，"
              "“归了 sty 却被类调用”那一道跳过了）")
    return 0


def show() -> int:
    for pkg, spots in sorted(actual().items()):
        print("%-16s %-48s " % (pkg, "+".join(sorted(spots))))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="查宏包归属")
    ap.add_argument("--list", action="store_true", help="按当前代码打印策略表骨架")
    args = ap.parse_args()
    return show() if args.list else check()


if __name__ == "__main__":
    sys.exit(main())
