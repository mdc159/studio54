#!/usr/bin/env bash
# Capture a single-shot snapshot of the live VPS into a JSON file.
# Usage: bash audit/dump_vps.sh <out-path>
# Requires: ssh alias `Studio54` reaching root@148.230.95.154.
#
# This script only runs the SSH capture and writes the raw section-marked
# text to a temp file. The temp file is then handed to audit/parse_dump.py
# to produce the structured JSON. Splitting capture from parsing keeps each
# piece unit-testable.
set -euo pipefail

OUT="${1:?missing <out-path>}"
SSH_HOST="${VPS_SSH_HOST:-Studio54}"
HERE="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$(dirname "$OUT")"
START="$(date -u +%FT%TZ)"

RAW_TMP="$(mktemp -t vps-dump-raw.XXXXXX)"
trap 'rm -f "$RAW_TMP"' EXIT

# Single SSH session; remote bash interprets the heredoc.
# Quoted 'REMOTE' prevents local interpolation of $variables.
ssh -o BatchMode=yes "$SSH_HOST" 'bash -s' >"$RAW_TMP" <<'REMOTE'
set -uo pipefail
echo "===docker_ps==="
docker ps -a --format '{{json .}}' || true
echo "===docker_inspect==="
for c in $(docker ps --format '{{.Names}}'); do
  docker inspect "$c" || true
  echo
done
echo "===systemctl_user==="
systemctl --user list-units --state=running --no-pager --plain || true
echo "===listening_ports==="
ss -tlnp || true
echo "===env_files==="
for f in /opt/1215-vps/stack/prototype-local/.env; do
  if [ -r "$f" ]; then
    echo "FILE:$f"
    cat "$f"
    echo "ENDFILE:$f"
  fi
done
echo "===bin_1215==="
cd /opt/1215-vps 2>/dev/null && {
  echo "DOCTOR:"
  ./bin/1215 doctor 2>&1 || true
  echo "SERVICES:"
  ./bin/1215 services 2>&1 || true
  echo "STATUS:"
  ./bin/1215 status 2>&1 || true
}
echo "===file_hashes==="
for f in /opt/1215-vps/stack/prototype-local/.env \
         /opt/1215-vps/stack/prototype-local/docker-compose.yml; do
  if [ -r "$f" ]; then
    sha256sum "$f"
  fi
done
echo "===done==="
REMOTE

FINISH="$(date -u +%FT%TZ)"

uv run "$HERE/parse_dump.py" \
    --raw "$RAW_TMP" \
    --out "$OUT" \
    --started-at "$START" \
    --finished-at "$FINISH"
