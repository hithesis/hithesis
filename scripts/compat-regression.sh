#!/bin/bash
# 旧版面兼容回归：钉死 v3.1e。
#
# 测的是“老文档在新模板的兼容层（v2-layout）下，排出来还是不是老样子”。
# 旧版面要长期保留，所以这一轨是常设的，不随发版漂移。
#
# 同一份内容编两遍：
#   参照侧  v3.1e 的示例内容 + v3.1e 的类
#   当前侧  v3.1e 的示例内容 + 当前工作树的类 + v2-layout
# 逐页渲染 PNG 后比对。不能各编各的树——两版示例内容本身就不同。
#
# 用法：scripts/compat-regression.sh [变体名...]   不给就跑 tests/compat 下全部
# 退出码：0 全同；1 有差异；2 出错
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd); cd "$ROOT"
TAG=${COMPAT_TAG:-v3.1e}
WORK=${COMPAT_WORK:-$ROOT/tests/compat-work}
: "${SOURCE_DATE_EPOCH:=1700000000}"; : "${FORCE_SOURCE_DATE:=1}"
export SOURCE_DATE_EPOCH FORCE_SOURCE_DATE

git rev-parse --verify "$TAG" >/dev/null 2>&1 || { echo "找不到 tag $TAG"; exit 2; }

REF_TREE="$WORK/ref-tree"
if [ ! -d "$REF_TREE" ]; then
  echo "== 取出 $TAG 的源码树 =="
  mkdir -p "$REF_TREE"
  git archive "$TAG" | tar -x -C "$REF_TREE"
  echo "== 在 $TAG 的树里生成那一版的类 =="
  ( cd "$REF_TREE" && make cls >/dev/null 2>&1 ) || { echo "$TAG 的 make cls 失败"; exit 2; }
fi

confs=${*:-$(ls tests/compat/*.conf | xargs -n1 basename | sed 's/\.conf$//')}
rc=0
for name in $confs; do
  conf="tests/compat/$name.conf"
  [ -f "$conf" ] || { echo "没有 $conf"; rc=2; continue; }
  echo "########## $name ##########"
  for side in ref new; do
    tmp="$WORK/$name.$side.conf"
    if [ "$side" = ref ]; then
      grep -vE '^(OPTIONS_NEW|CLS_NEW)=' "$conf" > "$tmp"
      cls_root="$REF_TREE"
    else
      # 当前侧：把 OPTIONS_NEW/CLS_NEW 顶上去（没写就沿用参照侧那份）
      python3 - "$conf" "$tmp" <<'PY'
import sys
src, dst = sys.argv[1], sys.argv[2]
v = {}
for line in open(src, encoding='utf-8'):
    line = line.strip()
    if not line or line.startswith('#') or '=' not in line: continue
    k, _, val = line.partition('=')
    v[k.strip()] = val.strip()
v['OPTIONS'] = v.get('OPTIONS_NEW', v.get('OPTIONS', ''))
v['CLS'] = v.get('CLS_NEW', v.get('CLS', ''))
with open(dst, 'w', encoding='utf-8') as f:
    for k in ('BASE', 'ENTRY', 'OPTIONS', 'CLS'):
        if v.get(k): f.write(f'{k}={v[k]}\n')
PY
      cls_root="$ROOT"
    fi
    cp "$tmp" "tests/variants/__compat_$name.conf"
    SRC_ROOT="$REF_TREE" CLS_ROOT="$cls_root" \
      WORK_DIR="$WORK/$name-$side" PNG_DIR="$WORK/png-$side" \
      bash tools/compile-variant.sh "__compat_$name" > "$WORK/$name-$side.log" 2>&1
    st=$?
    rm -f "tests/variants/__compat_$name.conf"
    if [ $st -ne 0 ]; then
      echo "  $side 侧编译失败（见 $WORK/$name-$side.log）"; tail -5 "$WORK/$name-$side.log"; rc=2; continue 2
    fi
  done
  a=$(ls "$WORK/png-ref/__compat_$name"-p*.png 2>/dev/null | wc -l | tr -d ' ')
  b=$(ls "$WORK/png-new/__compat_$name"-p*.png 2>/dev/null | wc -l | tr -d ' ')
  if [ "$a" = 0 ] || [ "$b" = 0 ]; then echo "  没渲染出 PNG（ref=$a new=$b）"; rc=2; continue; fi
  if [ "$a" != "$b" ]; then echo "  页数不同：参照 $a 页，当前 $b 页"; rc=1; continue; fi
  diff_pages=0
  for f in "$WORK/png-ref/__compat_$name"-p*.png; do
    g="$WORK/png-new/$(basename "$f")"
    cmp -s "$f" "$g" || diff_pages=$((diff_pages+1))
  done
  if [ $diff_pages -eq 0 ]; then echo "  $a 页逐页相同"
  else echo "  $a 页中 $diff_pages 页不同"; rc=1; fi
done
exit $rc
