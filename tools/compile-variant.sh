#!/bin/bash
# Compile a single test variant and render to PNG.
# Usage: compile-variant.sh <variant-name>
#
# 认这几个环境变量：
#   SRC_ROOT    去哪棵树取 example 目录，默认仓库根目录。回归测试比历史版本时
#               指向解压出来的 release 目录
#   WORK_DIR    编译工作目录，默认 <repo>/tests/work/<variant>
#   PNG_DIR     PNG 输出目录，默认 <repo>/tests/current
#   RENDER_PNG  设成 0 就只编译不渲染 PNG，CI 只看能不能编过时用
set -e

variant=$1
[ -z "$variant" ] && { echo "Usage: $0 <variant-name>"; exit 2; }

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

SRC_ROOT=${SRC_ROOT:-$ROOT}
WORK=${WORK_DIR:-$ROOT/tests/work/$variant}
PNG_DIR=${PNG_DIR:-$ROOT/tests/current}
RENDER_PNG=${RENDER_PNG:-1}

# 封面日期取的是 \today，不钉死的话每天编出来的 PDF 都不一样，没法比。
# FORCE_SOURCE_DATE 会让引擎按 SOURCE_DATE_EPOCH 去初始化 \year/\month/\day，
# 不加就只改 PDF 元数据。
: "${SOURCE_DATE_EPOCH:=1700000000}"
: "${FORCE_SOURCE_DATE:=1}"
export SOURCE_DATE_EPOCH FORCE_SOURCE_DATE

CONF="tests/variants/$variant.conf"
[ -f "$CONF" ] || { echo "No such variant: $variant"; exit 2; }

# Source variant config: BASE, OPTIONS, CLS, ENTRY (default thesis.tex)
. "$CONF"
ENTRY=${ENTRY:-thesis.tex}

SRC_DIR="$SRC_ROOT/$BASE"
[ -d "$SRC_DIR" ] || { echo "  no such source dir: $SRC_DIR"; exit 3; }

rm -rf "$WORK"
mkdir -p "$WORK"
cp -r "$SRC_DIR"/* "$WORK"/

# Rewrite the first \documentclass line in $ENTRY
python3 - "$WORK/$ENTRY" "$OPTIONS" "$CLS" <<'PYEOF'
import sys, re
path, options, cls = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
new_line = f"\\documentclass[{options}]{{{cls}}}"
text, n = re.subn(r'^\\documentclass\[[^\]]*\]\{[^}]+\}',
                  lambda m: new_line, text, count=1, flags=re.MULTILINE)
if n != 1:
    print("Could not substitute \\documentclass line", file=sys.stderr)
    sys.exit(1)
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
PYEOF

# Use latexmk if a .latexmkrc is present in the example dir;
# it handles bibtex/splitindex automatically and is deterministic.
cd "$WORK"
if [ -f latexmkrc ] || [ -f .latexmkrc ]; then
  if ! latexmk -xelatex -interaction=nonstopmode -halt-on-error "$ENTRY" > "compile.log" 2>&1; then
    echo "  latexmk failed:"
    tail -40 "compile.log"
    exit 1
  fi
else
  # Fallback: xelatex thrice (no bibliography support)
  for i in 1 2 3; do
    if ! xelatex -interaction=nonstopmode -halt-on-error "$ENTRY" > "compile-$i.log" 2>&1; then
      echo "  xelatex pass $i failed:"
      tail -30 "compile-$i.log"
      exit 1
    fi
  done
fi

PDF="${ENTRY%.tex}.pdf"
[ -f "$PDF" ] || { echo "  PDF not produced"; exit 1; }

if [ "$RENDER_PNG" = "0" ]; then
  exit 0
fi

# Render to PNG at 200 DPI
mkdir -p "$PNG_DIR"
rm -f "$PNG_DIR/${variant}-p"*.png
gs -dNOPAUSE -dBATCH -dSAFER -sDEVICE=png16m -r200 \
   -sOutputFile="$PNG_DIR/${variant}-p%03d.png" \
   "$PDF" > /dev/null 2>&1
