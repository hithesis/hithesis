#!/bin/bash
# 编译定理专项测试。用法：bash tools/compile-theorem.sh [输出目录]
# 认 LANG_OPT 环境变量，例如 LANG_OPT=lang=en
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT=${1:-$ROOT/tests/work/theorem}
mkdir -p "$OUT"
cp "$ROOT"/hithesisbook.cls "$ROOT"/hithesis.ist "$ROOT"/*.bst "$ROOT"/*.eps "$OUT/" 2>/dev/null || true
if [ -n "$LANG_OPT" ]; then
  sed "s/campus=harbin\]/campus=harbin,$LANG_OPT]/" "$ROOT/tests/theorem/theorem.tex" > "$OUT/theorem.tex"
else
  cp "$ROOT/tests/theorem/theorem.tex" "$OUT/theorem.tex"
fi
cd "$OUT"
export SOURCE_DATE_EPOCH=1600000000 FORCE_SOURCE_DATE=1
for i in 1 2; do xelatex -interaction=nonstopmode theorem.tex >/dev/null 2>&1 || true; done
[ -f theorem.pdf ] && echo "编出来了：$OUT/theorem.pdf" || { echo "编译失败"; grep -m3 "^! " theorem.log; exit 1; }
