#!/usr/bin/env python3
"""扫编译日志，把“编得过但有毛病”的那几类挡在门外。

CI 现在只看示例文档编不编得过。v3.2a 排查出来的一批问题全是编得过的：
题注短标题接错参数（\\ref 悬空）、□ 整个字排丢（Missing character）、
TikZ 多写分号（nullfont）、封面表格顶出版心（Overfull）、版心声明与实排
不符（Over-specification）、花体字号偏大（size substituted）。痕迹一直在
日志里，只是没人看。

FATAL 那几类现在是 0，一条都不许再出现。
Underfull 不同：中文按字断行，遇上 \\verb 或长西文串只能把一行拉稀，是内容
特性不是缺陷，所以只钉总数，变多才报。

跑法：先 make baseline 或 make smoke 把变体编出来，再 make logcheck。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / ".github" / "log-underfull.txt"

FATAL = [
    ("Overfull", r"^Overfull \\[hv]box"),
    ("缺字", r"^Missing character:"),
    ("字号代用", r"size <[\d.]+> substituted"),
    ("PDF 字符串里的非法记号", r"Token not allowed in a PDF string"),
    ("版心过度指定", r"Over-specification in"),
    ("悬空引用", r"There were undefined references"),
    ("浮动体位置被改写", r"float specifier changed"),
    ("重复标签", r"There were multiply-defined labels"),
]


def logs():
    """变体的日志与示例目录里的日志都收。

    只看 TeX 自己写的 .log。compile.log 与退化路径写的 compile-1.log 这些是
    latexmk/xelatex 的完整输出，里面含中间轮次：第一遍必然报未定义引用，后面几遍
    才解决，扫它会全是假警报。
    CI 不跑全部变体，只编示例，所以两处都要认。

    一个目录里可能不止一份日志（示例目录下 thesis、opening、midterm 各一份），
    调用方按变体名累加，不要覆盖，否则排序靠后的那份会把真正要看的那份顶掉。"""
    out = []
    for pat in ("tests/work/*/*.log", "examples/*/*.log"):
        out += [p for p in ROOT.glob(pat) if not p.name.startswith("compile")]
    return sorted(set(out))


def name_of(path):
    """变体用目录名，示例用相对路径，两边不会撞名"""
    rel = path.relative_to(ROOT)
    return rel.parent.name if rel.parts[0] == "tests" else str(rel.parent)


def scan(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    hits = {}
    for name, pat in FATAL:
        n = len(re.findall(pat, text, re.M))
        if n:
            hits[name] = n
    under = len(re.findall(r"^Underfull \\hbox", text, re.M))
    return hits, under


def main() -> int:
    files = logs()
    if not files:
        print("tests/work/ 下没有日志。先跑 make baseline 或 tools/compile-variant.sh")
        return 2

    bad = 0
    under = {}
    for f in files:
        hits, u = scan(f)
        variant = name_of(f)
        under[variant] = under.get(variant, 0) + u
        for name, n in hits.items():
            print(f"{variant}: {name} {n} 条")
            bad += n

    base = {}
    if BASELINE.exists():
        for line in BASELINE.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                k, v = line.rsplit(None, 1)
                base[k.strip()] = int(v)

    grew = [(k, base.get(k), v) for k, v in sorted(under.items())
            if k in base and v > base[k]]
    for k, was, now in grew:
        print(f"{k}: Underfull 从 {was} 涨到 {now}")

    if bad:
        print(f"\n共 {bad} 条不该出现的告警。这几类在 v3.2a 已清零，"
              f"新出现的说明改坏了什么。")
    if grew:
        print(f"\n{len(grew)} 个变体的 Underfull 变多了。确认是内容变化还是版面变差，"
              f"确认无误后跑 scripts/check-logs.py --update 更新基线。")
    return 1 if (bad or grew) else 0


def update() -> int:
    files = logs()
    if not files:
        print("没有日志可采")
        return 2
    lines = ["# 各变体的 Underfull 条数基线，由 scripts/check-logs.py --update 生成。",
             "# 中文按字断行，遇上 \\verb 或长西文串只能把一行拉稀，是内容特性。",
             "# 只在变多时报警；确认过版面没变差再更新这里。"]
    under = {}
    for f in files:
        _, u = scan(f)
        under[name_of(f)] = under.get(name_of(f), 0) + u
    lines += [f"{k} {v}" for k, v in sorted(under.items())]
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"基线已更新，收录 {len(under)} 个变体（{len(files)} 份日志）")
    return 0


if __name__ == "__main__":
    sys.exit(update() if "--update" in sys.argv else main())
