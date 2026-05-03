#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

ARTIFACT_DIR="${ARTIFACT_DIR:-$ROOT/.artifacts/agent-validation}"
mkdir -p "$ARTIFACT_DIR"

echo "== Python syntax for repo-owned scripts =="
python3 -m compileall -q stack/prototype-local/scripts scripts

echo "== control1215 tests =="
uv run --project stack/control --extra dev pytest stack/control/tests -q | tee "$ARTIFACT_DIR/control1215-pytest.log"

echo "== Hermes Langfuse probe tests =="
PYTHONPATH=modules/hermes-agent uv run --project stack/control --extra dev pytest modules/hermes-agent/tests/agent/test_langfuse_probe.py -o 'addopts=' -q | tee "$ARTIFACT_DIR/hermes-langfuse-pytest.log"

echo "== Paperclip package metadata smoke =="
if [[ -f modules/paperclip/server/package.json ]]; then
  node -e "const p=require('./modules/paperclip/server/package.json'); console.log(p.name || 'server package ok')" | tee "$ARTIFACT_DIR/paperclip-package.log"
fi

echo "== Compose config smoke =="
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  python3 stack/prototype-local/scripts/init_env.py --output "$ARTIFACT_DIR/prototype.env" --force >/tmp/studio54-init-env.log
  docker compose --env-file "$ARTIFACT_DIR/prototype.env" -f stack/prototype-local/docker-compose.substrate.yml config --quiet
  echo "PASS docker compose config" | tee "$ARTIFACT_DIR/compose-config.log"
else
  echo "SKIP docker compose unavailable" | tee "$ARTIFACT_DIR/compose-config.log"
fi

echo "validate-repo result: PASS"
