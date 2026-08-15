#!/bin/bash
# Smoke test: compare current dtx-generated PDFs against baseline.
# Parallel compile via NPROC=N (default 8).
set -e

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

NPROC=${NPROC:-8}

echo "[smoke] Regenerating cls files from dtx..."
make --no-print-directory cls > /tmp/hithesis-cls.log 2>&1 || {
  echo "FATAL: make cls failed; see /tmp/hithesis-cls.log"
  exit 1
}

rm -rf tests/current tests/diff tests/work
mkdir -p tests/current

# Only variants that have a baseline
VARIANTS=()
for conf in tests/variants/*.conf; do
  v=$(basename "$conf" .conf)
  if ls tests/baseline/${v}-p*.png >/dev/null 2>&1; then
    VARIANTS+=("$v")
  fi
done

if [ ${#VARIANTS[@]} -eq 0 ]; then
  echo "FATAL: no baseline available, run make-baseline.sh first"
  exit 1
fi

echo "[smoke] Compiling ${#VARIANTS[@]} variants in parallel (NPROC=$NPROC)..."
printf '%s\n' "${VARIANTS[@]}" | xargs -P "$NPROC" -I{} bash -c '
  v="{}"
  bash tools/compile-variant.sh "$v" > "/tmp/$v.log" 2>&1
'

PASS=0
FAIL=0
FAILED=()
for v in "${VARIANTS[@]}"; do
  if ! ls tests/current/${v}-p*.png >/dev/null 2>&1; then
    FAIL=$((FAIL + 1))
    FAILED+=("$v (compile)")
    printf "  %-44s COMPILE FAILED (see /tmp/%s.log)\n" "$v" "$v"
    continue
  fi

  if bash tools/compare-variant.sh "$v" > "/tmp/$v.cmp.log" 2>&1; then
    PASS=$((PASS + 1))
    printf "  %-44s MATCH\n" "$v"
  else
    FAIL=$((FAIL + 1))
    FAILED+=("$v (diff)")
    printf "  %-44s MISMATCH\n" "$v"
    cat "/tmp/$v.cmp.log"
  fi
done

echo ""
echo "[smoke] Summary: $PASS match, $FAIL fail"
if [ "$FAIL" -gt 0 ]; then
  echo "Failed variants:"
  for v in "${FAILED[@]}"; do echo "  - $v"; done
  exit 1
fi
echo "All variants match baseline. Safe to commit."
