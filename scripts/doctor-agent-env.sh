#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

missing=0
check_cmd() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf 'PASS command %-12s %s\n' "$name" "$(command -v "$name")"
  else
    printf 'FAIL command %-12s missing\n' "$name"
    missing=1
  fi
}

echo "== toolchain =="
check_cmd git
check_cmd gh
check_cmd uv
check_cmd python3
check_cmd docker

if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    echo "PASS docker_daemon reachable"
  else
    echo "WARN docker_daemon not reachable; compose smoke gates will skip or fail in CI depending on job"
  fi
fi

echo "== github auth =="
if command -v gh >/dev/null 2>&1; then
  if gh auth status >/tmp/studio54-gh-status 2>&1; then
    sed -E 's/(Token: ).*/\1[REDACTED]/; s/(oauth_token: ).*/\1[REDACTED]/' /tmp/studio54-gh-status
  else
    echo "WARN gh is installed but not authenticated; local PR operations may be blocked"
  fi
fi

echo "== repo =="
git remote -v || true
git status --short --branch

echo "== secret hygiene =="
for f in .env stack/prototype-local/.env; do
  if [[ -f "$f" ]]; then
    echo "INFO ignored local env present: $f (not printed)"
  else
    echo "PASS no local env at: $f"
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo "doctor result: missing required commands"
  exit 1
fi

echo "doctor result: ready enough for cloud-agent validation"
