#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Installed at /opt/hithesis-notify/notify.sh; never run code received via SSH.
if [[ ! -f "$ROOT/deploy/qq-notify/compose.yaml" ]]; then
  printf 'Install this wrapper at the repository root: /opt/hithesis-notify/notify.sh\n' >&2
  exit 1
fi
case "$*" in
  ""|--force|--dry-run|--publish) ;;
  *) printf 'Usage: notify.sh [--force|--dry-run|--publish]\n' >&2; exit 2 ;;
esac
exec docker compose --project-directory "$ROOT/deploy/qq-notify" run --rm --no-deps notifier "$@"
