#!/usr/bin/env bash
# Idempotent Studio54 VM rehearsal bootstrap.
#
# Run on a disposable Ubuntu VM to converge it toward the same local/private
# node shape proven on the VPS, while keeping resets cheap via VM snapshots.
#
# Defaults are deliberately conservative: prepare the host, clone/update the
# repo, project runtime files, and run `./bin/1215 doctor`. Use --with-up and
# --with-smoke when you want to bring containers up during a rehearsal pass.

set -Eeuo pipefail

usage() {
  cat <<'USAGE'
Usage: studio54-vm-startup.sh [options]

Options:
  --repo URL          Git repo to clone (default: https://github.com/mdc159/studio54.git)
  --branch NAME      Branch/ref to checkout (default: main)
  --dir PATH         Deploy checkout path (default: /opt/studio54-bootstrap)
  --node-name NAME   NODE_NAME written to root .env (default: hostname -s)
  --with-up          Run ./bin/1215 up --target prototype-local after doctor
  --with-smoke       Run ./bin/1215 smoke --skip-gate after up/status
  --reset-stack      Run ./bin/1215 down --volumes before up (destructive)
  --no-apt           Skip apt package installation
  --skip-network-check
                     Skip outbound internet preflight
  --help             Show this help

Environment overrides mirror the flags:
  STUDIO54_REPO, STUDIO54_BRANCH, STUDIO54_DIR, STUDIO54_NODE_NAME,
  STUDIO54_WITH_UP=1, STUDIO54_WITH_SMOKE=1, STUDIO54_RESET_STACK=1,
  STUDIO54_NO_APT=1, STUDIO54_SKIP_NETWORK_CHECK=1
USAGE
}

repo="${STUDIO54_REPO:-https://github.com/mdc159/studio54.git}"
branch="${STUDIO54_BRANCH:-main}"
deploy_dir="${STUDIO54_DIR:-/opt/studio54-bootstrap}"
node_name="${STUDIO54_NODE_NAME:-$(hostname -s)}"
with_up="${STUDIO54_WITH_UP:-0}"
with_smoke="${STUDIO54_WITH_SMOKE:-0}"
reset_stack="${STUDIO54_RESET_STACK:-0}"
no_apt="${STUDIO54_NO_APT:-0}"
skip_network_check="${STUDIO54_SKIP_NETWORK_CHECK:-0}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) repo="$2"; shift 2 ;;
    --branch) branch="$2"; shift 2 ;;
    --dir) deploy_dir="$2"; shift 2 ;;
    --node-name) node_name="$2"; shift 2 ;;
    --with-up) with_up=1; shift ;;
    --with-smoke) with_smoke=1; with_up=1; shift ;;
    --reset-stack) reset_stack=1; with_up=1; shift ;;
    --no-apt) no_apt=1; shift ;;
    --skip-network-check) skip_network_check=1; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "error: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ "${EUID}" -ne 0 ]]; then
  if ! command -v sudo >/dev/null 2>&1; then
    echo "error: must run as root or have sudo available" >&2
    exit 1
  fi
  exec sudo -E bash "$0" \
    --repo "$repo" \
    --branch "$branch" \
    --dir "$deploy_dir" \
    --node-name "$node_name" \
    $([[ "$with_up" == 1 ]] && printf '%s' '--with-up') \
    $([[ "$with_smoke" == 1 ]] && printf '%s' '--with-smoke') \
    $([[ "$reset_stack" == 1 ]] && printf '%s' '--reset-stack') \
    $([[ "$no_apt" == 1 ]] && printf '%s' '--no-apt') \
    $([[ "$skip_network_check" == 1 ]] && printf '%s' '--skip-network-check')
fi

log() { printf '\n==> %s\n' "$*"; }
run() { printf '+ %q' "$1"; shift; printf ' %q' "$@"; printf '\n'; "$@"; }

network_preflight() {
  if [[ "$skip_network_check" == 1 ]]; then
    log "Skipping outbound network preflight"
    return
  fi

  log "Checking outbound internet from VM"
  if command -v curl >/dev/null 2>&1; then
    if curl -fsSIL --max-time 8 https://pypi.org/simple/setuptools/ >/dev/null; then
      return
    fi
  else
    # Fall back to bash's TCP client when curl has not been installed yet.
    if timeout 8 bash -lc '</dev/tcp/pypi.org/443' >/dev/null 2>&1; then
      return
    fi
  fi

  cat >&2 <<'EOF'
error: outbound internet check failed from the VM.

Studio54 bootstrap needs egress for apt, git, uv/PyPI, and Docker image pulls.
This usually means the VM NAT/bridge is broken even if SSH from the host works.
Fix networking, revert/reset the VM snapshot if needed, then rerun this script.
Use --skip-network-check only when all required dependencies are already cached.
EOF
  exit 10
}

install_packages() {
  if [[ "$no_apt" == 1 ]]; then
    log "Skipping apt package installation (--no-apt)"
    return
  fi

  export DEBIAN_FRONTEND=noninteractive
  log "Installing host prerequisites"
  apt-get update
  apt-get install -y \
    bash \
    ca-certificates \
    curl \
    git \
    jq \
    python3 \
    python3-venv \
    build-essential \
    ripgrep \
    docker.io \
    docker-compose-v2 \
    openssh-server

  systemctl enable --now docker
  systemctl enable --now ssh || true
}

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    log "uv already available: $(command -v uv)"
    return
  fi
  log "Installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="/root/.local/bin:${PATH}"
  if [[ -x /root/.local/bin/uv && ! -e /usr/local/bin/uv ]]; then
    ln -s /root/.local/bin/uv /usr/local/bin/uv
  fi
  command -v uv >/dev/null 2>&1
}

checkout_repo() {
  log "Checking out ${repo} (${branch}) into ${deploy_dir}"
  mkdir -p "$(dirname "$deploy_dir")"
  if [[ -d "${deploy_dir}/.git" ]]; then
    git -C "$deploy_dir" remote set-url origin "$repo"
    git -C "$deploy_dir" fetch origin --prune
  elif [[ -e "$deploy_dir" ]]; then
    echo "error: ${deploy_dir} exists but is not a git checkout" >&2
    echo "move it aside or choose --dir" >&2
    exit 1
  else
    git clone "$repo" "$deploy_dir"
    git -C "$deploy_dir" fetch origin --prune
  fi

  if git -C "$deploy_dir" rev-parse --verify --quiet "origin/${branch}" >/dev/null; then
    git -C "$deploy_dir" checkout -B "$branch" "origin/${branch}"
  else
    git -C "$deploy_dir" checkout "$branch"
  fi

  # Safe even when the repository currently has no submodules.
  git -C "$deploy_dir" submodule update --init --recursive
}

set_env_value() {
  local file="$1" key="$2" value="$3"
  python3 - "$file" "$key" "$value" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
lines = path.read_text().splitlines()
needle = key + "="
for idx, line in enumerate(lines):
    if line.startswith(needle):
        lines[idx] = f"{key}={value}"
        break
else:
    lines.append(f"{key}={value}")
path.write_text("\n".join(lines) + "\n")
PY
}

project_runtime_files() {
  log "Preparing root and stack runtime env files"
  cd "$deploy_dir"
  if [[ ! -f .env ]]; then
    cp .env.example .env
    chmod 600 .env
  fi

  set_env_value .env NODE_NAME "$node_name"
  set_env_value .env DEPLOY_ROOT "$deploy_dir"
  set_env_value .env STACK_ENV_PATH "$deploy_dir/stack/prototype-local/.env"
  set_env_value .env HERMES_HOME /root/.hermes
  set_env_value .env HERMES_CONFIG_PATH /root/.hermes/config.yaml
  set_env_value .env HERMES_ENV_PATH /root/.hermes/.env
  set_env_value .env HERMES_HONCHO_CONFIG_PATH /root/.hermes/honcho.json
  set_env_value .env PAPERCLIP_PUBLIC_URL http://127.0.0.1:3100
  set_env_value .env PAPERCLIP_API_URL http://127.0.0.1:3100
  set_env_value .env PAPERCLIP_BROWSER_ORIGIN http://127.0.0.1:3100
  set_env_value .env PAPERCLIP_ALLOWED_HOSTNAMES "localhost,127.0.0.1,${node_name}"

  python3 stack/prototype-local/scripts/project_root_env.py --force
  # project_root_env.py is the canonical repo-root -> stack-local projection
  # and intentionally creates stack/prototype-local/.env. init_env.py is kept
  # as a fallback for older branches where projection may be absent/incomplete;
  # do not run it unconditionally after projection or it will refuse to
  # overwrite the freshly projected file.
  if [[ ! -f stack/prototype-local/.env ]]; then
    python3 stack/prototype-local/scripts/init_env.py
  fi
  mkdir -p /root/.hermes
  python3 stack/prototype-local/scripts/project_hermes_runtime.py
}

run_cli_checks() {
  log "Running Studio54 doctor"
  cd "$deploy_dir"
  ./bin/1215 doctor

  if [[ "$reset_stack" == 1 ]]; then
    log "Resetting compose stack and volumes"
    ./bin/1215 down --target prototype-local --volumes || true
  fi

  if [[ "$with_up" == 1 ]]; then
    log "Starting prototype-local stack"
    ./bin/1215 up --target prototype-local
    ./bin/1215 status --target prototype-local
  fi

  if [[ "$with_smoke" == 1 ]]; then
    log "Running smoke checks (skip gate for fast VM rehearsal)"
    ./bin/1215 smoke --skip-gate
  fi
}

main() {
  log "Studio54 VM rehearsal bootstrap"
  echo "repo=${repo}"
  echo "branch=${branch}"
  echo "deploy_dir=${deploy_dir}"
  echo "node_name=${node_name}"
  echo "with_up=${with_up} with_smoke=${with_smoke} reset_stack=${reset_stack} no_apt=${no_apt} skip_network_check=${skip_network_check}"

  network_preflight
  install_packages
  ensure_uv
  checkout_repo
  project_runtime_files
  run_cli_checks

  log "Done"
  git -C "$deploy_dir" --no-pager log -1 --oneline
}

main "$@"
