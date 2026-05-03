#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

python3 --version
git --version
uv --version
node --version || true
pnpm --version || true

echo "== Studio54 agent workbench doctor =="
bash scripts/doctor-agent-env.sh || true

echo "Workbench ready. Run: bash scripts/validate-repo.sh"
