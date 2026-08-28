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
    """元信息字段名。它们与词条各占一段前缀，这里只用来判“拼串的宏名少了前缀”。"""
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
    # \hit@define@title 现造的那一组零参名字
    for lang in ("zh", "en"):
        for suf in ("", "-flat", "-cover", "-subtitle",
                    "-line-one", "-line-two", "-first", "-second"):
            out.add(f"title{suf}-{lang}")
    return out


def expand_loops(s: str) -> str:
    """把 \\clist_map_inline:nn {表} {体} 按表里的项展开一遍。

    ``after-*-number`` 那十二条是循环生成的，不展开就会被当成“声明了没取值”。
    只处理 ``#1`` 这一层，够用：cfg 里的循环只有这一种。
    """
    out = [s]
    for m in re.finditer(r"\\clist_map_inline:nn\s*\{", s):
        items, i = braced(s, m.end())
        while i < len(s) and s[i] in " \n":
            i += 1
        if i >= len(s) or s[i] != "{":
            continue
        body, _ = braced(s, i + 1)
        if "#1" not in body:
            continue
        for t in items.replace("\n", " ").split(","):
            t = t.strip()
            if t:
                out.append(body.replace("#1", t))
    return "\n".join(out)


def valued(*files: pathlib.Path) -> set[str]:
    """这些文件里真给了取值的键。

    取值不止在 ``.cfg`` 里：``after-*-number`` 那十二条由 ``shared-defaults``
    的循环显式设成空值，那一段编进类文件，所以 ``.cls`` 也要一起读。
    """
    s = expand_loops("\n".join(f.read_text(encoding="utf-8") for f in files))
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


def buckets() -> list[str]:
    """页桶名单，与 src/setup/hit-key-engine.dtx 里那张一致。"""
    s = (ROOT / "src/setup/hit-key-engine.dtx").read_text(encoding="utf-8")
    m = re.search(r"\\clist_const:Nn \\c__hit_bucket_clist\s*\{(.*?)\}", s, re.S)
    return [x.strip() for x in m.group(1).replace("\n", " ").split(",") if x.strip()]


def with_fallback(names: set[str]) -> set[str]:
    """各页桶取不到的名字指向 base 里的同名词条，所以 base 有什么，各桶就有什么。"""
    out = set(names)
    for n in names:
        if n.startswith("base-"):
            rest = n[len("base-"):]
            out |= {b + "-" + rest for b in buckets() if b != "base"}
    return out


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
        | {"degree-type": t}
        for c, d, t, l in itertools.product(
            ["harbin", "shenzhen", "weihai"],
            ["bachelor", "master", "doctor", "postdoc"],
            ["academic", "professional"],
            ["zh", "en"])
    ],
    "hit-report": [
        dict(kind=k, campus=c, degree=d, lang=l)
        | {"degree-type": t}
        for k, c, d, t, l in itertools.product(
            ["proposal", "interim"],
            ["harbin", "shenzhen", "weihai"],
            ["bachelor", "master", "doctor"],
            ["academic", "professional"],
            ["zh", "en"])
    ],
}


def main() -> int:
    decl = declared()
    bad: list[tuple[str, str, str]] = []
    skipped: list[str] = []
    for cls, skel in (("hit-thesis", "src/hit-thesis.dtx"),
                      ("hit-report", "src/hit-report.dtx")):
        cfg = ROOT / f"{cls}.cfg"
        if not cfg.exists() or not (ROOT / f"{cls}.cls").exists():
            skipped.append(cls)
            continue
        have = with_fallback(bound(valued(cfg, ROOT / f"{cls}.cls"), CONTEXTS[cls]))
        # 声明了却在这个类里没取到值的，引用它就是空的
        missing = {k for k in decl if k not in have}
        macros = {"\\hit@term@" + k.replace("-", "@").replace("*", ""): k for k in missing}
        for rel, guards in assembly(skel):
            p = ROOT / "src" / rel
            if not p.exists():
                continue
            for m in re.finditer(r"\\hit@term@[a-zA-Z@]+", code_lines(p, guards)):
                if m.group(0) in macros:
                    bad.append((cls, macros[m.group(0)], rel))
    # 第二关：引用了一个没声明的键，而同一个词条的别的档位是声明过的。
    # 改名时消费端改了、键名忘了改，就落在这里；上一次是
    # \hit@titlepage@major@postdoc@zh，六个博后变体直接编不出来。
    terms = {parse_key(k)[0] for k in decl}
    # 查表把最具体的那一条绑到“词条名[-语言]”上，那个名字不在声明表里，
    # 排版代码却正是写它。
    resolved = set(decl)
    for k in decl:
        term, spec = parse_key(k)
        lang = spec.get("lang", "")
        resolved.add(term + ("-" + lang if lang else ""))
        resolved.add(term)
    declm = {"\\hit@term@" + k.replace("-", "@").replace("*", "")
             for k in with_fallback(resolved)}
    typo: list[tuple[str, str, str]] = []
    for cls, skel in (("hit-thesis", "src/hit-thesis.dtx"),
                      ("hit-report", "src/hit-report.dtx")):
        if cls in skipped:
            continue
        for rel, guards in assembly(skel):
            p = ROOT / "src" / rel
            if not p.exists():
                continue
            for m in re.finditer(r"\\hit@term@[a-zA-Z@]+", code_lines(p, guards)):
                name = m.group(0)
                if name in declm:
                    continue
                key = name[len("\\hit@term@"):].replace("@", "-")
                typo.append((cls, key, rel))

    # 第三关：拿字符串拼出来的宏名。\use:c { hit@keywords@zh@plain } 这种
    # 改名脚本扫不到（它只认 \hit@ 开头的记号），漏了就是取到一个未定义的宏。
    # 已经踩过三次：\hit@parse@keywords 的分隔符、题注前缀的 \@captype、
    # 以及 pdfkeywords 这一处。
    names = {k.replace("-", "@").replace("*", "") for k in decl | info_fields()}
    names |= {n + "@raw" for n in names} | {n + "@plain" for n in names}
    built: list[tuple[str, str]] = []
    for p2 in sorted(ROOT.glob("src/**/*.dtx")):
        for l in p2.read_text(encoding="utf-8").splitlines():
            if l.startswith("%"):
                continue
            for m in re.finditer(r"\{ *hit@([a-zA-Z@]+) *\}", l):
                if m.group(1) in names:
                    built.append((str(p2.relative_to(ROOT)), "hit@" + m.group(1)))

    if bad or typo or built:
        if bad:
            print("常量引用不到取值：\n")
            for cls, key, rel in sorted(set(bad)):
                print(f"  {cls}：{rel} 引用了 {key}，这个类里没有它的取值")
            print("\n要么在对应那份 cfg 里给它取值，要么消费端改用别的键。\n")
        if typo:
            print("引用了没声明的词条：\n")
            for cls, key, rel in sorted(set(typo)):
                print(f"  {cls}：{rel} 引用了 {key}，声明表里没有这个键")
            print("\n多半是改名时消费端改了、声明表与取值忘了跟。\n")
        if built:
            print("拿字符串拼的宏名指向词条或元信息，少了 term@／info@ 这一段：\n")
            for rel, name in sorted(set(built)):
                print(f"  {rel}：{{ {name} }}")
            print("\n改名脚本只认 \\hit@ 开头的记号，拼串的地方扫不到，得手工跟。")
        return 1
    if len(skipped) == 2:
        print("两个类都没生成，先跑 make cls")
        return 1
    if skipped:
        print(f"常量取值一致（声明 {len(decl)} 个；{skipped[0]} 没生成，只查了另一个）")
    else:
        print(f"常量取值一致（声明 {len(decl)} 个，两个类各自都取得到）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
