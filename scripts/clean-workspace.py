#!/usr/bin/env python3
"""清理已忽略的编译辅助文件和临时构建目录。"""
import argparse
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
CACHES = (
    "build/test", "build/unpacked", "build/local", "build/result",
    "build/distrib", "build/doc", "build/example-figures", "build/typst-compare",
    "target", "tests/work", "tests/current", "tests/diff", "tests/feature/work",
    "tests/doc-current", "tests/doc-diff", "scripts/__pycache__",
)
PROTECTED = (".claude", ".vscode", "assets", "tests/reference",
             "tests/baseline", "tests/doc-baseline", "build/figure-comparison")
AUX_SUFFIXES = (
    ".aux", ".log", ".toc", ".toe", ".lof", ".lot", ".loe", ".loeq",
    ".out", ".bbl", ".blg", ".glo", ".gls", ".glg", ".idx", ".ind",
    ".ilg", ".hd", ".xdv", ".dvi", ".fls", ".fdb_latexmk", ".synctex.gz",
    ".thm", ".vrb", ".bcf", ".run.xml",
)
OBSOLETE = {
    ".changes.raw", "hithesis-ctan.zip", "hitszthesis.bst",
    "hit-logo.eps", "hit-bachelor-report-bottommark.eps",
    "hit-weihai-bachelor-title.eps", "zfb-eps-converted-to.pdf",
}


def under(name, directory):
    return name == directory or name.startswith(directory + "/")


def git_files(*options):
    data = subprocess.check_output(["git", "ls-files", "-z", *options], cwd=ROOT)
    return {name.decode("utf-8") for name in data.split(b"\0") if name}


def candidates():
    tracked = git_files()
    ignored = git_files("--others", "--ignored", "--exclude-standard")
    paths = []
    for name in CACHES:
        path = ROOT / name
        if not path.is_symlink() and not path.resolve().is_relative_to(ROOT):
            continue
        if path.exists() and not any(under(item, name) for item in tracked):
            if subprocess.run(["git", "check-ignore", "-q", name], cwd=ROOT).returncode == 0:
                paths.append(name)
    for name in sorted(ignored):
        if any(under(name, directory) for directory in (*PROTECTED, *paths)):
            continue
        path = ROOT / name
        if not path.is_symlink() and not path.resolve().is_relative_to(ROOT):
            continue
        if not (path.is_file() or path.is_symlink()):
            continue
        in_build_area = "/" not in name or name.startswith(("examples/demo/", "tests/", "src/"))
        if (path.name == ".DS_Store" or name in OBSOLETE
                or (in_build_area and (name.endswith(AUX_SUFFIXES) or path.name.endswith("-BSTcontrol.bib")))):
            paths.append(name)
    return sorted(paths)


def size(path):
    if path.is_symlink():
        return path.lstat().st_size
    if path.is_file():
        return path.stat().st_size
    return sum(p.lstat().st_size for p in path.rglob("*") if p.is_file() or p.is_symlink())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="执行清理；省略时只列出文件")
    args = parser.parse_args()
    paths = candidates()
    total = sum(size(ROOT / name) for name in paths)
    for name in paths:
        print(name)
        if args.apply:
            path = ROOT / name
            if path.is_symlink() or path.is_file():
                path.unlink()
            else:
                shutil.rmtree(path)
    print(f"{'已清理' if args.apply else '可清理'} {len(paths)} 项，{total / 1024**2:.1f} MiB")


if __name__ == "__main__":
    main()
