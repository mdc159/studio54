#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

SIM_ROOT="${SIM_ROOT:-$(mktemp -d -t studio54-vps-sim.XXXXXX)}"
ARTIFACT_DIR="${ARTIFACT_DIR:-$ROOT/.artifacts/vps-simulation}"
mkdir -p "$ARTIFACT_DIR" "$SIM_ROOT"

SIM_ENV="$SIM_ROOT/sim.env"
cat > "$SIM_ENV" <<EOF
PAPERCLIP_HOME_HOST_PATH=$SIM_ROOT/paperclip
PAPERCLIP_INSTANCE_ID=default
PAPERCLIP_USER_UID=$(id -u)
PAPERCLIP_USER_GID=$(id -g)
HONCHO_BASE_URL=http://127.0.0.1:18000
HERMES_MODEL_DEFAULT=google/gemini-2.5-flash
HERMES_MODEL_PROVIDER=openrouter
HERMES_MODEL_BASE_URL=https://openrouter.ai/api/v1
EOF

run_prepare() {
  local company_id="$1"
  local agent_id="$2"
  python3 stack/prototype-local/scripts/prepare_paperclip_hermes_home.py \
    --source "$SIM_ENV" \
    --paperclip-home "$SIM_ROOT/paperclip" \
    --instance-id default \
    --company-id "$company_id" \
    --agent-id "$agent_id" \
    --owner-uid "$(id -u)" \
    --owner-gid "$(id -g)" \
    | tee "$ARTIFACT_DIR/${company_id}-prepare.log"
}

run_prepare company-a agent-a
run_prepare company-b agent-b

python3 scripts/verify-simulated-vps-bootstrap.py \
  --root "$SIM_ROOT" \
  --output "$ARTIFACT_DIR/simulated-vps-bootstrap-report.json"

echo "simulation root: $SIM_ROOT" | tee "$ARTIFACT_DIR/simulation-root.txt"
echo "simulate-vps-bootstrap result: PASS"
