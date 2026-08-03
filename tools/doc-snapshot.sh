#!/bin/bash
# 给宏包手册（hithesis.pdf）做前后对照。
#
#   bash tools/doc-snapshot.sh save    改动前跑，把当前手册存成基线
#   bash tools/doc-snapshot.sh check   改动后跑，重编并与基线逐页比
#
# 为什么不并进 scripts/regression_test.py：那套比的是「相对 dev / 相对发布版」，
# 而手册在 modularity 上本来就跟 dev 不一样（多了模块说明一节）。手册要的是
# 「这次改动前后有没有变」，参照物是自己，不是别的分支。
set -e

mode=${1:-}
case "$mode" in
  save|check) ;;
  *) echo "用法: $0 save|check"; exit 2 ;;
esac

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

BASELINE="$ROOT/tests/doc-baseline"
CURRENT="$ROOT/tests/doc-current"
DIFF="$ROOT/tests/doc-diff"

# 手册封面/页脚同样会取当前日期，不钉死就没法比
: "${SOURCE_DATE_EPOCH:=1700000000}"
: "${FORCE_SOURCE_DATE:=1}"
export SOURCE_DATE_EPOCH FORCE_SOURCE_DATE

echo "[doc-snapshot] 重编手册……"
rm -f hithesis.pdf
make cls > /dev/null
if ! make doc > /tmp/doc-snapshot.log 2>&1; then
  echo "手册编译失败："
  tail -30 /tmp/doc-snapshot.log
  exit 1
fi
[ -f hithesis.pdf ] || { echo "没产出 hithesis.pdf"; exit 1; }

out=$([ "$mode" = save ] && echo "$BASELINE" || echo "$CURRENT")
rm -rf "$out"
mkdir -p "$out"
gs -dNOPAUSE -dBATCH -dSAFER -sDEVICE=png16m -r150 \
   -sOutputFile="$out/p%03d.png" hithesis.pdf > /dev/null 2>&1
pages=$(ls "$out" | wc -l | tr -d ' ')

if [ "$mode" = save ]; then
  echo "[doc-snapshot] 基线已存：$pages 页 → tests/doc-baseline/"
  exit 0
fi

if [ ! -d "$BASELINE" ]; then
  echo "没有基线，先跑一次 $0 save"
  exit 1
fi

base_pages=$(ls "$BASELINE" | wc -l | tr -d ' ')
mismatch=0
if [ "$pages" != "$base_pages" ]; then
  echo "  页数不同：基线 $base_pages，当前 $pages"
  mismatch=1
fi

rm -rf "$DIFF"
for cur in "$CURRENT"/p*.png; do
  page=$(basename "$cur")
  ref="$BASELINE/$page"
  if [ ! -f "$ref" ]; then
    echo "  新增页：$page"
    mismatch=1
    continue
  fi
  if ! cmp -s "$cur" "$ref"; then
    echo "  第 ${page} 页有差异"
    mismatch=1
    if command -v compare > /dev/null 2>&1; then
      mkdir -p "$DIFF"
      compare "$ref" "$cur" "$DIFF/$page" 2>/dev/null || true
    fi
  fi
done

if [ "$mismatch" -eq 0 ]; then
  echo "[doc-snapshot] 手册 $pages 页与基线完全一致。"
  exit 0
fi
echo "[doc-snapshot] 手册有变化，差异图见 tests/doc-diff/"
exit 1
