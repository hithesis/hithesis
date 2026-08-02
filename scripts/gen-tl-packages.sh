#!/usr/bin/env bash
#
# 生成 .github/tl_packages 的候选内容。
#
# 做法是用 `-recorder` 编译几个代表性变体，把 *.fls 里的 INPUT 记录收集起来，去
# TeX Live 的包数据库（texlive.tlpdb）里反查这些文件属于哪个包，再把基础 collection
# 已经覆盖掉的减去，剩下的就是得单独声明的。
#
# 用法：
#   scripts/gen-tl-packages.sh                # 编代表性变体，然后生成
#   scripts/gen-tl-packages.sh --all          # 42 个变体全编，更全，约 15 分钟
#   scripts/gen-tl-packages.sh --reuse        # 拿 tests/work/ 里现成的 .fls 用，不重编
#
# 结果打到 stdout。别拿它直接覆盖 .github/tl_packages，要 diff 着合并：那个文件末尾
# 有一段手工补充项（latexmk 这种只给二进制、不给 TeX 输入文件的包），recorder 看不到。

set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

# 四个 example 目录都占上，harbin/shenzhen/weihai 三套封面也都过一遍
REPRESENTATIVE=(01-bachelor-harbin 03-bachelor-weihai 04-bachelor-harbin-en
                08-master-shenzhen 25-art-bachelor-harbin-opening
                42-artplus-doctor-shenzhen-midterm)

# 这几个 collection 在 tl_packages 里整体声明，里面的包不用再单独列
BASE_COLLECTIONS=(collection-latex collection-xetex collection-langchinese
                  collection-fontsrecommended collection-latexrecommended)

mode=representative
for arg in "$@"; do
  case $arg in
    --all)   mode=all ;;
    --reuse) mode=reuse ;;
    -h|--help) sed -n '3,15p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 1 ;;
  esac
done

if [[ $mode != reuse ]]; then
  echo "[gen-tl-packages] 生成 cls……" >&2
  latex hithesis.ins > /dev/null

  echo "[gen-tl-packages] 编译宏包文档（-recorder）……" >&2
  xelatex -recorder -interaction=nonstopmode hithesis.dtx > /dev/null 2>&1 || true

  if [[ $mode == all ]]; then
    variants=()
    for conf in tests/variants/*.conf; do variants+=("$(basename "$conf" .conf)"); done
  else
    variants=("${REPRESENTATIVE[@]}")
  fi

  echo "[gen-tl-packages] 编译 ${#variants[@]} 个变体……" >&2
  mkdir -p tests/work
  printf '%s\n' "${variants[@]}" | xargs -P "${NPROC:-8}" -I{} bash -c '
    v="{}"
    if bash tools/compile-variant.sh "$v" > "tests/work/$v.genlog" 2>&1; then
      printf "  %-44s OK\n" "$v" >&2
    else
      printf "  %-44s FAIL（这个变体不计入依赖）\n" "$v" >&2
    fi
  '
fi

fls_files=$(find tests/work -name '*.fls' 2>/dev/null || true)
[[ -f hithesis.fls ]] && fls_files=$(printf '%s\nhithesis.fls\n' "$fls_files")

if [[ -z ${fls_files//[[:space:]]/} ]]; then
  echo "error: 一个 .fls 都没有，先不带 --reuse 跑一次" >&2
  exit 1
fi

TEXMFROOT=$(kpsewhich -var-value=TEXMFROOT)
TLPDB="$TEXMFROOT/tlpkg/texlive.tlpdb"
[[ -f $TLPDB ]] || { echo "error: 找不到 $TLPDB" >&2; exit 1; }

FLS_LIST=$(mktemp)
trap 'rm -f "$FLS_LIST"' EXIT
printf '%s\n' "$fls_files" > "$FLS_LIST"

# python3 的程序体是从 stdin 读的（heredoc 占了），.fls 清单只能走参数
python3 - "$TLPDB" "$TEXMFROOT" "$FLS_LIST" "${BASE_COLLECTIONS[@]}" <<'PYEOF'
import os
import sys

tlpdb_path, texmfroot, fls_list_path = sys.argv[1], sys.argv[2], sys.argv[3]
base_collections = sys.argv[4:]

# ---- 1. 解析 texlive.tlpdb，拿到 文件路径 -> 包名，以及各 collection 的依赖 ----
file2pkg: dict[str, str] = {}
depends: dict[str, list[str]] = {}

name = None
section = None
with open(tlpdb_path, encoding="utf-8", errors="replace") as f:
    for line in f:
        line = line.rstrip("\n")
        if not line:
            name, section = None, None
            continue
        if line.startswith(" "):
            if name and section in ("runfiles", "binfiles"):
                # 长这样：" texmf-dist/tex/latex/base/article.cls"，也可能带 details= 后缀
                path = line.strip().split(" ", 1)[0]
                file2pkg.setdefault(path, name)
            continue
        key, _, value = line.partition(" ")
        if key == "name":
            name, section = value, None
        elif key.endswith("files"):
            section = key
        elif key == "depend" and name:
            depends.setdefault(name, []).append(value)
        else:
            section = None

# ---- 2. 扫 .fls，看用到了哪些包 ----
detected: set[str] = set()
unknown: set[str] = set()

with open(fls_list_path, encoding="utf-8") as f:
    fls_paths = f.read().split()

for fls in fls_paths:
    fls = fls.strip()
    if not fls or not os.path.exists(fls):
        continue
    with open(fls, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.startswith("INPUT "):
                continue
            path = os.path.realpath(line[6:].strip())
            if not path.startswith(texmfroot + os.sep):
                continue  # 工作目录里自己生成的，不算依赖
            rel = os.path.relpath(path, texmfroot)
            pkg = file2pkg.get(rel)
            if pkg:
                detected.add(pkg)
            else:
                unknown.add(rel)

# ---- 3. 把基础 collection 已经覆盖的减掉 ----
covered: set[str] = set()
for coll in base_collections:
    covered.add(coll)
    for dep in depends.get(coll, []):
        covered.add(dep)
        if dep.startswith("collection-"):
            covered.update(depends.get(dep, []))

extra = sorted(p for p in detected - covered if not p.startswith("collection-"))

# ---- 4. 输出 ----
print("# TeX Live 依赖清单，scripts/gen-tl-packages.sh 生成，再人工整理过。")
print("#")
print("# 给 .github/workflows/test.yml 的 setup-texlive-action 用，用户手工补装也照它：")
print("# tlmgr install $(grep -v '^#' .github/tl_packages)")
print()
print("scheme-minimal")
print()
for coll in base_collections:
    print(coll)
print()
print(f"# ----- 下面 {len(extra)} 个是 gen-tl-packages.sh 从 .fls 里查出来的 -----")
print()
for pkg in extra:
    print(pkg)

if unknown:
    print()
    print(f"# 有 {len(unknown)} 个输入文件在 tlpdb 里没查到归属，比如：",
          file=sys.stderr)
    for rel in sorted(unknown)[:15]:
        print(f"#   {rel}", file=sys.stderr)
PYEOF
