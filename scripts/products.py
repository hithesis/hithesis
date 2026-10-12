#!/usr/bin/env python3
"""产物清单的解析与交叉校验。

权威清单是 src/hithesis.dtx 的 install 守卫里那批 \\file{}：那里写了什么，
docstrip 就生成什么。围着它还有三份派生清单，从前各写各的，加一个产物要
改四处，漏一处没有任何东西会说：

  tools/distfiles.txt   拷进 examples/demo 的那些
  build.lua 的 installfiles   装进 TEXMF 的那些
  install 守卫末尾的 \\Msg 横幅  告诉手工安装的用户要搬哪些文件

这个脚本让前两份都从 tools/distfiles.txt 读（--dist / --figures），
再把四份两两对上（--check）。

用法：
    scripts/products.py --dist        分发清单，空格分隔，Makefile 用
    scripts/products.py --figures     其中要放进 figures/ 的
    scripts/products.py --check       四份清单交叉校验，有问题退出码 1
"""

from __future__ import annotations

import argparse
import re
import sys
import pathlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIST = ROOT / "tools" / "distfiles.txt"
DTX = ROOT / "src" / "hithesis.dtx"
BUILD = ROOT / "build.lua"
ASSETS = ROOT / "assets"


def parse_list() -> tuple[list[str], list[tuple[str, str]], dict[str, str]]:
    """读 tools/distfiles.txt，返回（平铺分发的、带子目录的、排除的）。

    行首 ``@`` 表示“只随示例发，不装进 tex 树”：示例与手册用的图属于这一类，
    它们不是模板资源，不该出现在用户装完模板的 tex/latex/hithesis/ 里。
    这类文件照样拷进示例目录，只是不参与 build.lua 的 installfiles 那道核对。
    """
    plain: list[str] = []
    subdir: list[tuple[str, str]] = []
    skipped: dict[str, str] = {}
    for raw in LIST.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("!"):
            name, _, why = line[1:].partition(" ")
            skipped[name] = why.strip()
            continue
        line = line.removeprefix("@")
        if "->" in line:
            name, _, dest = line.partition("->")
            subdir.append((name.strip(), dest.strip()))
        else:
            plain.append(line)
    return plain, subdir, skipped


def example_only() -> set[str]:
    """只随示例发、不装进 tex 树的那批，行首写 @。"""
    names = set()
    for raw in LIST.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith("@"):
            names.add(pathlib.Path(line[1:].partition("->")[0].strip()).name)
    return names


def generated() -> list[str]:
    """install 守卫里 \\file{} 生成的全部文件。"""
    text = DTX.read_text(encoding="utf-8")
    start = text.index("%<*install>")
    end = text.rindex("%</install>")
    names = re.findall(r"\\file\{([^}]*)\}", text[start:end])
    return [n.replace("\\jobname", "hithesis").replace(" ", "") for n in names]


def install_files() -> list[str]:
    """build.lua 的 installfiles，通配的原样留着。"""
    text = BUILD.read_text(encoding="utf-8")
    m = re.search(r"installfiles\s*=\s*\{(.*?)\}", text, re.S)
    return re.findall(r'"([^"]+)"', m.group(1)) if m else []


def banner_files() -> list[str]:
    """install 守卫末尾 \\Msg 横幅里列的文件名。"""
    text = DTX.read_text(encoding="utf-8")
    return re.findall(r"\\Msg\{\* \\space\\space (\S+)\}", text)


def check_assets(problems: list[str]) -> None:
    """检查 TikZ 源码与已分发 PDF 的哈希。"""
    import subprocess

    if subprocess.run([sys.executable, str(ROOT / "scripts/example-figures.py"),
                       "--check"], cwd=ROOT).returncode:
        problems.append("示例图需要重新生成，跑 make figures")


def matches(name: str, patterns: list[str]) -> bool:
    for p in patterns:
        if p == name:
            return True
        if p.startswith("*") and name.endswith(p[1:]):
            return True
    return False


def check() -> int:
    plain, subdir, skipped = parse_list()
    dist = plain + [n for n, _ in subdir]
    gen = generated()
    problems: list[str] = []

    check_assets(problems)

    for f in gen:
        if f not in dist and f not in skipped:
            problems.append(
                f"{f} 由 install 守卫生成，却既没列进 tools/distfiles.txt，"
                f"也没写进那里的排除表")
    for f in dist:
        if f.startswith("assets/"):
            if not (ROOT / f).exists():
                problems.append(f"tools/distfiles.txt 里的 {f} 不存在，跑 make figures")
        elif f not in gen:
            problems.append(f"tools/distfiles.txt 里的 {f} 不在 install 守卫的生成清单里")
    for f in skipped:
        if f not in gen:
            problems.append(f"tools/distfiles.txt 排除了 {f}，但它根本不是生成物")

    inst = install_files()
    exonly = example_only()
    for f in (Path(x).name for x in dist):
        if f in exonly:
            if matches(f, inst):
                problems.append(
                    f"{f} 在 tools/distfiles.txt 里标了只随示例发，"
                    f"却又列进了 build.lua 的 installfiles")
            continue
        if not matches(f, inst):
            problems.append(f"{f} 要分发到示例目录，却不在 build.lua 的 installfiles 里")

    banner = banner_files()
    for f in (Path(x).name for x in dist):
        if f in exonly:
            continue
        if f not in banner:
            problems.append(
                f"{f} 要分发，却不在 install 守卫末尾的 \\Msg 横幅里；"
                f"手工安装的用户会漏掉它")
    for f in banner:
        if f not in gen:
            problems.append(f"\\Msg 横幅里的 {f} 不是生成物")

    if problems:
        print("产物清单对不上：\n")
        for p in problems:
            print("  - " + p)
        print("\n权威清单是 src/hithesis.dtx 的 install 守卫，先改那里，再把三份派生清单跟上。")
        return 1
    print(f"产物清单一致（生成 {len(gen)} 个，分发 {len(dist)} 个，不分发 {len(skipped)} 个）")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="产物清单的解析与交叉校验")
    parser.add_argument("--dist", action="store_true", help="平铺分发的文件名，空格分隔")
    parser.add_argument("--figures", action="store_true", help="要放进 figures/ 的文件名")
    parser.add_argument("--check", action="store_true", help="四份清单交叉校验")
    args = parser.parse_args()

    plain, subdir, _ = parse_list()
    if args.dist:
        print(" ".join(plain))
        return 0
    if args.figures:
        print(" ".join(n for n, d in subdir if d == "figures"))
        return 0
    if args.check:
        return check()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
