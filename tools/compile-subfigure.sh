#!/bin/bash
# 编译子图专项测试。用法：bash tools/compile-subfigure.sh [输出目录]
# 认 OPT 环境变量，可以往 \documentclass 里再塞选项
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${1:-$ROOT/tests/work/subfigure}
mkdir -p "$OUT"
cp "$ROOT"/hithesisbook.cls "$ROOT"/hithesis.ist "$ROOT"/*.bst "$ROOT"/*.eps "$OUT/" 2>/dev/null || true
if [ -n "$OPT" ]; then
  sed "s/^\\\\documentclass\[\(.*\)\]{hithesisbook}/\\\\documentclass[\1,$OPT]{hithesisbook}/" "$ROOT/tests/subfigure/subfigure.tex" > "$OUT/subfigure.tex"
else
  cp "$ROOT/tests/subfigure/subfigure.tex" "$OUT/subfigure.tex"
fi
cd "$OUT"
export SOURCE_DATE_EPOCH=1600000000 FORCE_SOURCE_DATE=1
for i in 1 2; do xelatex -interaction=nonstopmode subfigure.tex >/dev/null 2>&1 || true; done
[ -f subfigure.pdf ] && echo "编出来了：$OUT/subfigure.pdf" || { echo "编译失败"; grep -m3 "^! " subfigure.log; exit 1; }
