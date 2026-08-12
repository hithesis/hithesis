#!/usr/bin/env python3
"""列出各个类里声明了却没人取用的常量键。

常量有四种取用方式，只认第一种就会误报一大片：

1. \\hit@<键名>            普通声明，连字符换成 @
2. \\<键名>                \\hit@declare@constant@as 声明的，驱动同名命令；
                          用在类里、手册里或示例里都算
3. \\ctexset               \\hit@declare@constant@ctex 声明的，转发给 ctex，
                          类里根本不会出现这个名字，一律算用了
4. <键名>                  别的常量的取值里引用它，设值时才展开成 \\hit@<键名>

还有一种是把宏名当参数传，靠 \\use:c 拼：
    \\hit@parse@keywords{keywords-zh}{keywords@separator@zh}
名字以 {keywords@separator@zh} 的形式出现在源码里，也要认。

另外检查语言后缀的对称性。v3.2a 把“固定中文”那批常量的 -zh 后缀去掉之后，
带 -zh 的键一律意味着“这个词分语言”，所以必须有 -en 兄弟，无一例外。
反过来不成立：有 9 个 -en 没有 -zh 对应，分两类，都在 EN_ONLY 里列明。

跑法：make cls 之后 python3 scripts/check-unused-const.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 只有 -en 没有 -zh 的，分两类，都不是遗漏
EN_ONLY = {
    # 双语题注英文那行的前缀，是缩写形（Fig. / Table），跟 figurename / tablename
    # 不是一个词：中文档 figurename=图，英文档 figurename=Figure，而这里是 Fig.，
    # 三个值不是两个。中文那行的前缀直接用 figurename，所以没有 -zh 对应。
    "figure-prefix", "table-prefix",
}

# \use:c 按 \@captype 之类拼出来的，正则查不到，逐条列明
CONSTRUCTED = {
    "figure-prefix-en", "table-prefix-en",
    "listfigurename", "listtablename", "listequationname",
    "equationname", "figurename", "tablename",
    # \hit@student@type@text:n{语言} 现拼 hit@student@type@<学术|专业>@<语言>
    *(f"student-type-{kind}-{lang}"
      for kind in ("academic", "professional")
      for lang in ("zh", "en")),
    # \hit@after@number:nnn{层级}{语言}{兜底} 现拼 hit@after@<层级>@number@<语言>
    *(f"after-{lvl}-number-{lang}"
      for lvl in ("chapter", "section", "subsection", "subsubsection",
                  "figure-caption", "table-caption")
      for lang in ("zh", "en")),
}

DECLARE = re.compile(r"\\hit@declare@constant(@as|@ctex)?\s*\{(.*?)\n  \}", re.S)


def declared(src: str) -> dict:
    out = {}
    for m in DECLARE.finditer(src):
        kind = (m.group(1) or "")[1:] or "plain"
        for item in m.group(2).replace("\n", " ").split(","):
            key = item.strip().split("=")[0].strip()
            if key:
                out[key] = kind
    return out


def used(key: str, kind: str, cls: str, elsewhere: str) -> bool:
    if key in CONSTRUCTED or kind == "ctex":
        return True
    at = key.replace("-", "@")
    if kind == "as":
        pat = r"\\" + re.escape(key) + r"(?![a-zA-Z@])"
        return bool(re.search(pat, cls) or re.search(pat, elsewhere))
    if re.search(re.escape("\\hit@" + at) + r"(?![a-zA-Z@])", cls):
        return True
    if re.search(r"\{\s*" + re.escape(at) + r"\s*\}", cls):        # 宏名当参数传
        return True
    if re.search(r"<\s*" + re.escape(key) + r"\s*>", cls):          # 取值里引用
        return True
    return False


def main() -> int:
    elsewhere = "\n".join(
        p.read_text(encoding="utf-8")
        for p in [ROOT / "src" / "manual" / "hit-manual.dtx", *sorted((ROOT / "examples").rglob("*.tex"))]
    )
    # 示例宏包跟类一起发，也取类里的常量（\hit@algorithm@name@zh 就只在那里用）。
    # 把它接在类文件后面一起搜，不然那两个常量会被报成死键。手册与示例不能这么并：
    # 那两处的正文里会提到宏名，一并了就没法发现真死键。
    sty = ROOT / "hithesis.sty"
    sty_src = sty.read_text(encoding="utf-8") if sty.exists() else ""
    total = 0
    for name in ("hit-thesis.cls", "hit-report.cls"):
        path = ROOT / name
        if not path.exists():
            print(f"{name} 还没生成，先跑 make cls")
            return 2
        src = path.read_text(encoding="utf-8")
        keys = declared(src)
        dead = [k for k, kind in keys.items()
                if not used(k, kind, src + "\n" + sty_src, elsewhere)]
        other = ROOT / ("hit-report.cls" if name == "hit-thesis.cls" else "hit-thesis.cls")
        osrc = other.read_text(encoding="utf-8") + "\n" + sty_src
        theirs = [k for k in dead if used(k, keys[k], osrc, elsewhere)]
        orphan = [k for k in dead if k not in theirs]
        print(f"{name}：常量 {len(keys)} 个，本类没取用 {len(dead)} 个"
              f"（其中 {len(theirs)} 个是另一个类在用的）")
        for k in orphan:
            print(f"  两个类都没用：{k}")
        total += len(orphan)
    if total:
        print(f"\n共 {total} 个常量两个类都没取用。确认是遗漏还是该删，"
              f"删的时候把为什么删写进 \\changes。")

    # 上面那个“另一个类在用的就放过”有个盲区：声明在甲、只有乙在用，两边一凑看着
    # 有人用，实际甲白声明、乙那个宏根本没定义。inline-separator 就这么躺了很久。
    # 这里正面查一遍：每个类只能用自己声明过的常量。
    decl = {n: declared((ROOT / n).read_text(encoding="utf-8")) for n in ("hit-thesis.cls", "hit-report.cls")}
    crossed = []
    for k in sorted(set().union(*(set(d) for d in decl.values()))):
        # CONSTRUCTED 的名字是 \use:c 现拼的，正则在哪个类里都查不到，used() 对它们
        # 一律返回真。拿这个结果做跨类判断只会得到“每个类都在用”，全是误报，跳过。
        if k in CONSTRUCTED:
            continue
        kind = next(d[k] for d in decl.values() if k in d)
        for n in ("hit-thesis.cls", "hit-report.cls"):
            if k in decl[n]:
                continue
            if used(k, kind, (ROOT / n).read_text(encoding="utf-8") + "\n" + sty_src, elsewhere):
                crossed.append((k, n))
    for k, n in crossed:
        owner = [m for m in decl if k in decl[m]]
        print(f"{n} 用了常量 {k}，但它只声明在 {'、'.join(owner)}。"
              f"要么在 {n} 的 keylist 里也声明，要么把取用点挪走")
    total += len(crossed)

    # 语言后缀的对称性
    both = set()
    for name in ("hit-thesis.cls", "hit-report.cls"):
        both |= set(declared((ROOT / name).read_text(encoding="utf-8")))
    zh = {k[:-3] for k in both if k.endswith("-zh")}
    en = {k[:-3] for k in both if k.endswith("-en")}
    orphan_zh = sorted(zh - en)
    orphan_en = sorted(en - zh - EN_ONLY)
    for k in orphan_zh:
        print(f"{k}-zh 没有 -en 兄弟。带 -zh 就意味着分语言，"
              f"要么补上 -en，要么去掉后缀并入不分语言的那批")
    for k in orphan_en:
        print(f"{k}-en 没有 -zh 兄弟，也不在 EN_ONLY 名单里。"
              f"补上 -zh，或者写清为什么只有英文再加进名单")
    print(f"语言后缀：成对 {len(zh & en)} 对，只有 en 的 {len(en - zh)} 个（名单里 {len(EN_ONLY)} 个）")
    return 1 if (orphan_zh or orphan_en) else 0


if __name__ == "__main__":
    sys.exit(main())
