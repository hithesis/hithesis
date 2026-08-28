#!/usr/bin/env python3
"""常量取值的构建期检查。

排版代码写 ``\\hit@titlepage@supervisor@zh``，取到的值由三处合起来决定：
声明表（哪些键存在）、两份 ``.cfg``（哪些键在这个类里有取值）、查表（按当前
上下文把最具体的那一档绑到不带档位的名字上）。三处任何一处漏了，那个宏就是
未定义的：``nonstopmode`` 下页面上留一格空白，编译照样以 0 退出，只有翻日志
才看得见。

这个脚本把三处对起来：对每个类，算出“哪些常量宏在这个类里确实会有值”，
再扫这个类要装配的源文件，找出引用了却永远拿不到值的那些。

用法：
    scripts/check-const.py          有问题退出码 1
"""

from __future__ import annotations

import itertools
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

# 轴表，与 src/setup/hit-key-engine.dtx 里那张一致
AXES = [
    ("kind", ["thesis", "proposal", "interim"]),
    ("campus", ["harbin", "shenzhen", "weihai"]),
    ("degree", ["bachelor", "master", "doctor", "postdoc"]),
    ("degree-type", ["academic", "professional"]),
    ("lang", ["zh", "en"]),
]
ORDER = [a for a, _ in AXES]
VAL2AX = {v: a for a, vs in AXES for v in vs}


def braced(text: str, start: int) -> tuple[str, int]:
    """读 start 处那一对花括号里的内容，返回（内容，右括号之后的位置）。"""
    depth, i = 1, start
    while depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[start:i - 1], i


def declared() -> set[str]:
    """声明表里的常量名。三种声明各扫一遍，@as 与 @ctex 那两批不走 \\hit@ 存法，
    它们的值写进同名命令或转给 ctex，这里不算。"""
    s = (ROOT / "src/setup/hit-keylist.dtx").read_text(encoding="utf-8")
    out: set[str] = set()
    for m in re.finditer(r"\\hit@declare@constant\s*\{", s):
        body, _ = braced(s, m.end())
        for t in body.replace("\n", " ").split(","):
            t = t.strip()
            if re.fullmatch(r"[a-z0-9*-]+", t):
                out.add(t)
    return out


def info_fields() -> set[str]:
    """元信息字段名。它们与常量共用 \\hit@ 这一个名字空间，判“没声明的档位”时
    要认得出来，否则 \\hit@degree@type@zh 这种会被当成常量的档位报出来。"""
    s = (ROOT / "src/setup/hit-keylist.dtx").read_text(encoding="utf-8")
    out: set[str] = set()
    for pat in (r"\\hit@define@term\{([a-z0-9-]+)\}",
                r"\\hit@define@term@alias\{([a-z0-9-]+)\}",
                r"\\hit@define@date@term\{([a-z0-9-]+)\}",
                r"\\hit@parse@keywords\{([a-z0-9-]+)\}"):
        out |= set(re.findall(pat, s))
    for m in re.finditer(r"\\hit@declare@info@field\s*\{", s):
        body, _ = braced(s, m.end())
        for t in body.replace("\n", " ").split(","):
            t = t.strip()
            if re.fullmatch(r"[a-z0-9-]+", t):
                out.add(t)
    return out


def valued(cfg: pathlib.Path) -> set[str]:
    """某一份 cfg 里真给了取值的键。"""
    s = cfg.read_text(encoding="utf-8")
    out: set[str] = set()
    for m in re.finditer(r"\\hit@presetup\s*(\[[^\]]*\])?\s*\{", s):
        body, _ = braced(s, m.end())
        cm = re.search(r"\bconst\s*=\s*\{", body)
        if not cm:
            continue
        inner, _ = braced(body, cm.end())
        depth, buf = 0, ""
        for ch in inner:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            if depth == 0:
                if ch == "=":
                    n = buf.strip().split(",")[-1].strip()
                    if re.fullmatch(r"[a-z0-9*-]+", n):
                        out.add(n)
                    buf = ""
                elif ch == ",":
                    buf = ""
                else:
                    buf += ch
    return out


def parse_key(key: str) -> tuple[str, dict[str, str]]:
    """键名拆成“词条名 + 各轴取值”。取值一律在后面，轴序严格递减。"""
    parts, spec = key.split("-"), {}
    while parts:
        v = parts[-1]
        if v not in VAL2AX:
            break
        ax = VAL2AX[v]
        if ax in spec:
            break
        if spec and ORDER.index(ax) >= min(ORDER.index(x) for x in spec):
            break
        spec[ax] = v
        parts = parts[:-1]
    return "-".join(parts), spec


def bound(keys: set[str], contexts: list[dict[str, str]]) -> set[str]:
    """算出所有上下文下查表会绑出来的名字，连同字面键本身。"""
    out = set(keys)
    for ctx in contexts:
        best: dict[str, tuple[int, str]] = {}
        doc: dict[str, tuple[int, str]] = {}
        for k in keys:
            term, spec = parse_key(k)
            lang = spec.pop("lang", "")
            if not all(ctx.get(a) == v for a, v in spec.items()):
                continue
            n = len(spec)
            name = term + ("-" + lang if lang else "")
            if name not in best or n > best[name][0]:
                best[name] = (n, k)
            if lang and lang == ctx.get("lang"):
                if term not in doc or n > doc[term][0]:
                    doc[term] = (n, k)
        out |= set(best)
        out |= {t for t in doc if t not in best}
    return out


def assembly(dtx: str) -> list[tuple[str, list[str]]]:
    """某个类的装配表：一行一个（源文件，守卫名单）。"""
    s = (ROOT / dtx).read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"^% \^\^A\s+\d+\s+(\S+\.dtx)\s+(\S+)", s, re.M):
        out.append((m.group(1), m.group(2).split(",")))
    return out


def code_lines(path: pathlib.Path, guards: list[str]) -> str:
    """只取这几个守卫圈住的代码行。dtx 里以 % 开头的是注释，不是代码；
    守卫之外的块属于别的类，也不算。"""
    keep, on = [], None
    for l in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"%<\*([\w,-]+)>", l)
        if m:
            on = m.group(1).split(",")
            continue
        if re.match(r"%</[\w,-]+>", l):
            on = None
            continue
        if l.startswith("%"):
            continue
        if on is None or any(g in guards for g in on):
            keep.append(l)
    return "\n".join(keep)


CONTEXTS = {
    "hit-thesis": [
        dict(kind="thesis", campus=c, degree=d, lang=l)
        for c, d, l in itertools.product(
            ["harbin", "shenzhen", "weihai"],
            ["bachelor", "master", "doctor", "postdoc"],
            ["zh", "en"])
    ],
    "hit-report": [
        dict(kind=k, campus=c, degree=d, lang=l)
        for k, c, d, l in itertools.product(
            ["proposal", "interim"],
            ["harbin", "shenzhen", "weihai"],
            ["bachelor", "master", "doctor"],
            ["zh", "en"])
    ],
}


def main() -> int:
    decl = declared()
    bad: list[tuple[str, str, str]] = []
    for cls, skel in (("hit-thesis", "src/hit-thesis.dtx"),
                      ("hit-report", "src/hit-report.dtx")):
        cfg = ROOT / f"{cls}.cfg"
        if not cfg.exists():
            print(f"没有 {cfg.name}，先跑 make cls")
            return 1
        have = bound(valued(cfg), CONTEXTS[cls])
        # 声明了却在这个类里没取到值的，引用它就是空的
        missing = {k for k in decl if k not in have}
        macros = {"\\hit@" + k.replace("-", "@").replace("*", ""): k for k in missing}
        for rel, guards in assembly(skel):
            p = ROOT / "src" / rel
            if not p.exists():
                continue
            for m in re.finditer(r"\\hit@[a-zA-Z@]+", code_lines(p, guards)):
                if m.group(0) in macros:
                    bad.append((cls, macros[m.group(0)], rel))
    # 第二关：引用了一个没声明的键，而同一个词条的别的档位是声明过的。
    # 改名时消费端改了、键名忘了改，就落在这里；上一次是
    # \hit@titlepage@major@postdoc@zh，六个博后变体直接编不出来。
    terms = {parse_key(k)[0] for k in decl}
    skip = decl | info_fields()
    declm = {"\\hit@" + k.replace("-", "@").replace("*", "") for k in skip}
    typo: list[tuple[str, str, str]] = []
    for cls, skel in (("hit-thesis", "src/hit-thesis.dtx"),
                      ("hit-report", "src/hit-report.dtx")):
        for rel, guards in assembly(skel):
            p = ROOT / "src" / rel
            if not p.exists():
                continue
            for m in re.finditer(r"\\hit@[a-zA-Z@]+", code_lines(p, guards)):
                name = m.group(0)
                if name in declm:
                    continue
                key = name[len("\\hit@"):].replace("@", "-")
                term, spec = parse_key(key)
                if spec and term in terms:
                    typo.append((cls, key, rel))

    if bad or typo:
        if bad:
            print("常量引用不到取值：\n")
            for cls, key, rel in sorted(set(bad)):
                print(f"  {cls}：{rel} 引用了 {key}，这个类里没有它的取值")
            print("\n要么在对应那份 cfg 里给它取值，要么消费端改用别的键。\n")
        if typo:
            print("引用了没声明的档位：\n")
            for cls, key, rel in sorted(set(typo)):
                t = parse_key(key)[0]
                print(f"  {cls}：{rel} 引用了 {key}，词条 {t} 有别的档位，"
                      f"这一档没声明")
            print("\n多半是改名时消费端改了、声明表与取值忘了跟。")
        return 1
    print(f"常量取值一致（声明 {len(decl)} 个，两个类各自都取得到）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
