#!/usr/bin/env bash
set -euo pipefail

bump_tag_letter() {
  local tag=$1
  local base
  local suffix
  local next_ord

  if [[ $tag =~ ^(.+)([a-y])$ ]]; then
    base=${BASH_REMATCH[1]}
    suffix=${BASH_REMATCH[2]}
    next_ord=$(( $(printf '%d' "'$suffix") + 1 ))
    printf '%s%s\n' "$base" "$(printf "\\$(printf '%03o' "$next_ord")")"
  elif [[ $tag =~ z$ ]]; then
    echo "error: cannot bump tag ending in z: $tag" >&2
    exit 1
  else
    printf '%sa\n' "$tag"
  fi
}

copy_file() {
  local src=$1
  local dest=$2

  mkdir -p "$(dirname "$dest/$src")"
  cp -p "$src" "$dest/$src"
}

usage() {
  echo "usage: scripts/package.sh [-o|--output PATH] [-v|--version VERSION] [-a|--add-file FILE]..." >&2
}

orig_pwd=$PWD
repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

output=
version=
add_files=()

while [[ $# -gt 0 ]]; do
  case $1 in
    -o|--output)
      if [[ $# -lt 2 ]]; then
        usage
        exit 1
      fi
      output=$2
      shift 2
      ;;
    --output=*)
      output=${1#*=}
      shift
      ;;
    -v|--version)
      if [[ $# -lt 2 ]]; then
        usage
        exit 1
      fi
      version=$2
      shift 2
      ;;
    --version=*)
      version=${1#*=}
      shift
      ;;
    -a|--add-file)
      if [[ $# -lt 2 ]]; then
        usage
        exit 1
      fi
      add_files+=("$2")
      shift 2
      ;;
    --add-file=*)
      add_files+=("${1#*=}")
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 1
      ;;
  esac
done

add_names=()
# 这里不能用关联数组，macOS 自带的 bash 还停在 3.2，没有 declare -A
for add_file in "${add_files[@]:-}"; do
  [[ -n $add_file ]] || continue
  if [[ ! -e $add_file ]]; then
    echo "error: add-file does not exist: $add_file" >&2
    exit 1
  fi

  add_name=$(basename "$add_file")
  if [[ $add_name == README.md || $add_name == examples || $add_name == hithesis.pdf ]]; then
    echo "error: add-file conflicts with package entry: $add_name" >&2
    exit 1
  fi
  for seen in "${add_names[@]:-}"; do
    if [[ $seen == "$add_name" ]]; then
      echo "error: duplicate add-file basename: $add_name" >&2
      exit 1
    fi
  done

  add_names+=("$add_name")
done

if [[ -n $version ]]; then
  # 正式发布，版本号由 release workflow 给，包名跟 tag 对齐
  package_name="hithesis-${version}.zip"
else
  # 日常打包，在最近的 tag 上进一个字母，再带上分支和日期好区分
  latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -z $latest_tag ]]; then
    latest_tag=$(git tag --sort=-v:refname | sed -n '1p')
  fi
  if [[ -z $latest_tag ]]; then
    echo "error: no git tag found" >&2
    exit 1
  fi

  package_version=$(bump_tag_letter "$latest_tag")
  branch=$(git branch --show-current)
  if [[ -z $branch ]]; then
    branch=$(git rev-parse --short HEAD)
  fi
  branch_slug=$(printf '%s' "$branch" | sed 's#[^A-Za-z0-9._-]#-#g')
  today=$(date +%Y%m%d)

  package_name="hithesis-${package_version}-${branch_slug}.${today}.zip"
fi
if [[ -z $output ]]; then
  output="$repo_root/$package_name"
elif [[ $output != /* ]]; then
  # 打包是在临时目录里 cd 过去做的，相对路径会打歪，先按调用者的当前目录展开
  output="$orig_pwd/$output"
fi

echo "Generating package files..."
make cls
make manual

if [[ ! -f hithesis.pdf ]]; then
  echo "error: hithesis.pdf was not generated" >&2
  exit 1
fi

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

copy_file README.md "$stage"
copy_file hithesis.pdf "$stage"
cp -a examples "$stage/"
find "$stage/examples" -type f '(' -name '*.aux' -o -name '*.bbl' -o -name '*.blg' -o -name '*.fdb_latexmk' -o -name '*.fls' -o -name '*.idx' -o -name '*.ilg' -o -name '*.ind' -o -name '*.lof' -o -name '*.log' -o -name '*.lot' -o -name '*.out' -o -name '*.synctex.gz' -o -name '*.thm' -o -name '*.toc' -o -name '*.toe' -o -name '*.xdv' -o -name 'report.pdf' -o -name 'thesis.pdf' ')' -delete

zip_inputs=(README.md examples hithesis.pdf)
for ((i = 0; i < ${#add_names[@]}; i++)); do
  add_file=${add_files[$i]}
  add_name=${add_names[$i]}
  cp -a "$add_file" "$stage/$add_name"
  zip_inputs+=("$add_name")
done

mkdir -p "$(dirname "$output")"
rm -f "$output"
(
  cd "$stage"
  zip -qr "$output" "${zip_inputs[@]}"
)

echo "$output"
