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

跑法：make cls 之后 python3 scripts/check-unused-const.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# \use:c 按 \@captype 之类拼出来的，正则查不到，逐条列明
CONSTRUCTED = {
    "figure-prefix-en", "table-prefix-en",
    "listfigurename", "listtablename", "listequationname",
    "equationname", "figurename", "tablename",
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
        for p in [ROOT / "src" / "hit-doc.dtx", *sorted((ROOT / "examples").rglob("*.tex"))]
    )
    total = 0
    for name in ("hit-thesis.cls", "hit-report.cls"):
        path = ROOT / name
        if not path.exists():
            print(f"{name} 还没生成，先跑 make cls")
            return 2
        src = path.read_text(encoding="utf-8")
        keys = declared(src)
        dead = [k for k, kind in keys.items() if not used(k, kind, src, elsewhere)]
        other = ROOT / ("hit-report.cls" if name == "hit-thesis.cls" else "hit-thesis.cls")
        osrc = other.read_text(encoding="utf-8")
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
