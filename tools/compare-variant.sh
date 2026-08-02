#!/bin/bash
# Compare current PNGs against baseline for a single variant.
# Exit 0 on match, 1 on any mismatch.
set -e

variant=$1
[ -z "$variant" ] && { echo "Usage: $0 <variant-name>"; exit 2; }

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

MISMATCH=0
BASELINE_COUNT=$(ls tests/baseline/${variant}-p*.png 2>/dev/null | wc -l | tr -d ' ')
CURRENT_COUNT=$(ls tests/current/${variant}-p*.png 2>/dev/null | wc -l | tr -d ' ')

if [ "$BASELINE_COUNT" = "0" ]; then
  echo "  no baseline for $variant"
  exit 1
fi

if [ "$BASELINE_COUNT" != "$CURRENT_COUNT" ]; then
  echo "  page count differs: baseline=$BASELINE_COUNT current=$CURRENT_COUNT"
  MISMATCH=1
fi

for current in tests/current/${variant}-p*.png; do
  page=$(basename "$current")
  baseline="tests/baseline/$page"
  if [ ! -f "$baseline" ]; then
    echo "  NO BASELINE: $page"
    MISMATCH=1
    continue
  fi
  if ! cmp -s "$current" "$baseline"; then
    echo "  DIFFERS: $page"
    MISMATCH=1
    # Save visual diff if ImageMagick is available
    if command -v compare > /dev/null 2>&1; then
      mkdir -p tests/diff
      compare "$baseline" "$current" "tests/diff/$page" 2>/dev/null || true
    fi
  fi
done

[ "$MISMATCH" -eq 0 ]
