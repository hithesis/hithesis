#!/bin/bash
set -eu
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
python3 - "$0" <<'PY'
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import uuid

folder = Path(sys.argv[1]).resolve().parent
repo = Path("__HITHESIS_ROOT__")
tool = repo / "scripts/word-continuations.py"
if not tool.is_file():
    raise SystemExit("找不到更新工具，请检查 .command 中的 hithesis 路径。")
sources = sorted(folder.glob("*-源稿.docx"))
if not sources:
    raise SystemExit("此目录没有 *-源稿.docx。")
stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
destination = folder / "更新结果" / stamp
for source in sources:
    name = source.name.removesuffix("-源稿.docx")
    print("正在更新：", source.name, flush=True)
    subprocess.run([sys.executable, str(tool), "update", "--input", str(source),
                    "--output", str(destination / name)], check=True)
print("更新完成：", destination, flush=True)
PY
