#!/usr/bin/env python3
"""Compile the docstrip-extracted TikZ figures, or check the shipped PDFs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src/assets/hit-example-figures.dtx"
RECORD = ROOT / "tools/example-figures.json"
NAMES = ("aerostatic", "aerodynamic", "hybrid", "squeeze-film")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def state():
    return {"source": digest(SOURCE),
            "pdf": {name: digest(ROOT / "assets" / (name + ".pdf")) for name in NAMES}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    recorded = json.loads(RECORD.read_text()) if RECORD.exists() else None
    current = state()
    valid = all(current["pdf"].values()) and recorded == current
    if args.check:
        if not valid:
            print("示例图缺失或与源码不一致，请运行 make figures", file=sys.stderr)
        return 0 if valid else 1
    if valid and not args.force:
        return 0
    missing = [name for name in NAMES if not (ROOT / (name + ".tex")).exists()]
    if missing:
        print("缺少提取的 TikZ 源文件，请运行 make cls", file=sys.stderr)
        return 1
    work = ROOT / "build/example-figures"
    work.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, SOURCE_DATE_EPOCH="946684800", FORCE_SOURCE_DATE="1")
    for name in NAMES:
        log = work / (name + "-build.log")
        with log.open("w") as stream:
            result = subprocess.run(
                ["xelatex", "-halt-on-error", "-interaction=nonstopmode",
                 "-output-directory=" + str(work), str(ROOT / (name + ".tex"))],
                cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            print(f"{name} 编译失败：{log}", file=sys.stderr)
            return result.returncode
    # 全部编译成功后再发布，避免失败时留下混合版本。
    for name in NAMES:
        shutil.copyfile(work / (name + ".pdf"), ROOT / "assets" / (name + ".pdf"))
    RECORD.write_text(json.dumps(state(), indent=2) + "\n")
    print("已生成四张 TikZ 矢量示例图")
    return 0


if __name__ == "__main__":
    sys.exit(main())
