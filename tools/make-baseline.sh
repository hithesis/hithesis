#!/bin/bash
# Generate baseline PNGs for all variants.
# Parallel compile uses up to NPROC concurrent xelatex jobs.
set -e

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

NPROC=${NPROC:-8}

echo "[make-baseline] Regenerating cls files from dtx..."
make --no-print-directory cls > /tmp/hithesis-cls.log 2>&1 || {
  echo "FATAL: make cls failed; see /tmp/hithesis-cls.log"
  exit 1
}

echo "[make-baseline] Clearing previous baseline..."
rm -rf tests/baseline tests/current tests/diff tests/work
mkdir -p tests/baseline tests/current

# Build the work list
VARIANTS=()
for conf in tests/variants/*.conf; do
  VARIANTS+=("$(basename "$conf" .conf)")
done

echo "[make-baseline] Compiling ${#VARIANTS[@]} variants in parallel (NPROC=$NPROC)..."
printf '%s\n' "${VARIANTS[@]}" | xargs -P "$NPROC" -I{} bash -c '
  v="{}"
  if bash tools/compile-variant.sh "$v" > "/tmp/$v.log" 2>&1; then
    printf "  %-44s OK\n" "$v"
  else
    printf "  %-44s FAIL (see /tmp/%s.log)\n" "$v" "$v"
  fi
'

# Collect successful PNGs into baseline
for v in "${VARIANTS[@]}"; do
  if ls tests/current/${v}-p*.png >/dev/null 2>&1; then
    mv tests/current/${v}-p*.png tests/baseline/
  fi
done

PASS=$(ls tests/baseline/ 2>/dev/null | sed 's/-p[0-9]*\.png$//' | sort -u | wc -l | tr -d ' ')
echo ""
echo "[make-baseline] $PASS variants have baseline; saved to tests/baseline/"
