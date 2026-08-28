#!/usr/bin/env python3
"""列出各个类里声明了却没人取用的常量键。

取用方式有五种，只认第一种就会误报一大片：

1. \\hit@term@<键名>       普通声明，连字符换成 @。v3.2a 把常量、元信息、函数
                          分成三个命名空间，取常量一律带 term@ 这一段
2. \\<键名>                \\hit@declare@constant@as 声明的，驱动同名命令；
                          用在类里、手册里或示例里都算
3. \\ctexset               \\hit@declare@constant@ctex 声明的，转发给 ctex，
                          类里根本不会出现这个名字，一律算用了
4. <键名>                  别的常量的取值里引用它，设值时才展开。取值现在住在
                          两份 .cfg 里，不在 .cls 里
5. {<键名的 @ 形式>}       宏名当参数传，靠 \\use:c 拼：
                          \\hit@parse@keywords{keywords-zh}{abstract@keywords@separator@zh}

声明的名字与代码里取的名字不是一回事，中间隔着查表，这里照 scripts/check-const.py
那套还原（轴表、页桶表、拆键都直接用它那一份）：

* 键名末尾的档位值是查表时按上下文挑的，代码里取的是剥掉档位的名字。声明
  titlepage-student-bachelor，本科档下绑出来的是 \\hit@term@titlepage@student
* 语言是分区不是档位，查表时把 -zh／-en 接在词条名后头
* 页桶取不到的词条落到 base 的同名条，所以 base 里的键由各页桶的引用点算取用

另外检查语言后缀的对称性。v3.2a 把“固定中文”那批常量的 -zh 后缀去掉之后，
带 -zh 的键一律意味着“这个词分语言”，所以必须有 -en 兄弟，无一例外。
反过来不成立：有几个 -en 没有 -zh 对应，都在 EN_ONLY 里列明。

跑法：make cls 之后 python3 scripts/check-unused-const.py
"""
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 只有 -en 没有 -zh 的，分两类，都不是遗漏
EN_ONLY = {
    # 双语题注英文那行的前缀，是缩写形（Fig. / Table），跟 figurename / tablename
    # 不是一个词：中文档 figurename=图，英文档 figurename=Figure，而这里是 Fig.，
    # 三个值不是两个。中文那行的前缀直接用 figurename，所以没有 -zh 对应。
    "caption-figure-prefix", "caption-table-prefix",
    # 英文版目录、图索引、表索引上方那一行栏头（Figure / Table / Page）。
    # 中文版的三张表都没有这一行，所以没有 -zh 对应。
    "table-of-contents-figure", "table-of-contents-table", "table-of-contents-page",
}

# \use:c 按 \@captype 之类拼出来的，正则查不到，逐条列明
CONSTRUCTED = {
    "caption-figure-prefix-en", "caption-table-prefix-en",
    "listfigurename", "listtablename", "listequationname",
    "equationname", "figurename", "tablename",
    # \hit@after@number:nnn{层级}{语言}{兜底} 现拼 hit@term@after@<层级>@number@<语言>
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


# 轴表、页桶表、键名拆解都用 scripts/check-const.py 那一份，抄第二份必然走样。
_spec = importlib.util.spec_from_file_location(
    "check_const", ROOT / "scripts" / "check-const.py")
CC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CC)


TERM = re.compile(r"\\hit@term@[a-zA-Z@]+")


def term_refs(text: str) -> set:
    """排版代码里所有词条引用，还原成键名。

    v3.2a 之前取一条常量写的是 \\hit@<键名>，现在是 \\hit@term@<键名>：常量、
    元信息、函数分了三个命名空间。只认旧写法的话每个键都查不到，180 个全报死键。
    """
    return {m.group()[len("\\hit@term@"):].replace("@", "-") for m in TERM.finditer(text)}


def used(key: str, kind: str, refs: set, values: str, cls: str, elsewhere: str) -> bool:
    if key in CONSTRUCTED or kind == "ctex":
        return True
    if kind == "as":
        pat = r"\\" + re.escape(key) + r"(?![a-zA-Z@])"
        return bool(re.search(pat, cls) or re.search(pat, elsewhere))
    # 语言是分区不是档位：查表时把 -zh／-en 接在词条名后头，所以声明成
    # titlepage-affiliation 的键，代码里取的是 \\hit@term@titlepage@affiliation@zh。
    # 键名里的档位值是查表时按上下文挑出来的，代码里取的是剥掉档位的那个名字：
    # 声明 titlepage-student-bachelor，本科档下绑成 \\hit@term@titlepage@student。
    bare, spec = CC.parse_key(key)
    stems = {bare}
    # 页桶取不到的词条落到 base 的同名条，所以 base 里的键由各桶的引用点算取用。
    if bare.startswith("base-"):
        rest = bare[len("base-"):]
        stems |= {b + "-" + rest for b in CC.buckets() if b != "base"}
    # 语言是分区不是档位：查表时把 -zh／-en 接在词条名后头。键名自己带了语言的，
    # 只认那一种——两种都认的话，\\hit@term@cover@degree@level@zh 这一处引用会同时
    # 算成 base-degree-level-en 有人用，另一半就永远查不出来。
    if "lang" in spec:
        names = {n + "-" + spec["lang"] for n in stems}
    else:
        names = {n + suf for n in stems for suf in ("", "-zh", "-en")}
    names.add(key)
    if names & refs:
        return True
    # 宏名当参数传：\\hit@parse@keywords{keywords-zh}{abstract@keywords@separator@zh}
    if any(re.search(r"\{\s*" + re.escape(n.replace("-", "@")) + r"\s*\}", cls)
           for n in names):
        return True
    if re.search(r"<\s*" + re.escape(key) + r"\s*>", values):      # 取值里引用
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
    # 取值现在住在两份 .cfg 里，不在 .cls 里：一条常量在别的取值里被 <键名> 引用，
    # 只看 .cls 是看不到的。
    def corpus(cls_name):
        cls = (ROOT / cls_name).read_text(encoding="utf-8")
        cfg = ROOT / cls_name.replace(".cls", ".cfg")
        values = cls + ("\n" + cfg.read_text(encoding="utf-8") if cfg.exists() else "")
        return cls, values

    total = 0
    present = [n for n in ("hit-thesis.cls", "hit-report.cls") if (ROOT / n).exists()]
    if not present:
        print("两个类都还没生成，先跑 make cls")
        return 2
    for name in present:
        src, values = corpus(name)
        keys = declared(src)
        refs = term_refs(src + "\n" + sty_src)
        dead = [k for k, kind in keys.items()
                if not used(k, kind, refs, values, src + "\n" + sty_src, elsewhere)]
        others = [n for n in present if n != name]
        theirs = []
        for o in others:
            osrc, ovalues = corpus(o)
            orefs = term_refs(osrc + "\n" + sty_src)
            theirs += [k for k in dead if k not in theirs
                       and used(k, keys[k], orefs, ovalues, osrc + "\n" + sty_src, elsewhere)]
        orphan = [k for k in dead if k not in theirs]
        print(f"{name}：常量 {len(keys)} 个，本类没取用 {len(dead)} 个"
              f"（其中 {len(theirs)} 个是另一个类在用的）")
        for k in orphan:
            print(f"  两个类都没用：{k}")
        total += len(orphan)
    if total:
        print(f"\n共 {total} 个常量两个类都没取用。确认是遗漏还是该删，"
              f"删的时候把为什么删写进 \\changes。")

    # 这里从前还有一条“声明在甲、只有乙在用”的正面检查，v3.2a 之后删了。
    # 有了轴表，一个类合法地会声明另一个类没有的档位变体（cover-thesis-title-bachelor
    # 只有学位论文类有，报告类用的是不带档位的 cover-thesis-title），而查表是
    # 按剥掉档位的名字绑的，两边一比必然互相指认。这条不变式现在由
    # scripts/check-const.py 的第二项管：一个类引用的词条必须在这个类里声明过。

    # 语言后缀的对称性
    both = set()
    for name in present:
        both |= set(declared((ROOT / name).read_text(encoding="utf-8")))
    # 比的是词条，不是整条键名。档位值是查表时按上下文挑的，一条词条的中文档
    # 在某个档位上另给一份、英文档没有，不算缺英文：英文那份由不带档位的通用值
    # 供着。titlepage-affiliation-bachelor-zh 就是这样，它的英文是
    # titlepage-affiliation-en。按整名死比会把这类全报出来，8 条里 8 条是假的。
    zh = {CC.parse_key(k)[0] for k in both if k.endswith("-zh")}
    en = {CC.parse_key(k)[0] for k in both if k.endswith("-en")}
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
