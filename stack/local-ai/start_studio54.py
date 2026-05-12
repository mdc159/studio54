#!/usr/bin/env python3
"""Local-AI-packaged-style Studio54 bootstrap.

This is intentionally boring: one root .env, one compose project, and host-side
Hermes projected from the same env. OpenRouter is the first-boot provider;
Codex/OpenAI OAuth is an operator/manual step after the stack is alive.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib import request

REPO_ROOT = Path(__file__).resolve().parents[2]
STACK_DIR = REPO_ROOT / "stack" / "local-ai"
ENV_EXAMPLE = STACK_DIR / ".env.example"
ROOT_ENV = REPO_ROOT / ".env"
COMPOSE_FILE = STACK_DIR / "docker-compose.yml"
PROJECT_HERMES_RUNTIME = REPO_ROOT / "stack" / "prototype-local" / "scripts" / "project_hermes_runtime.py"
INIT_ENV_DIR = REPO_ROOT / "stack" / "prototype-local" / "scripts"

DEFAULT_MODEL = "google/gemini-2.5-flash"
DEFAULT_HONCHO_URL = "http://127.0.0.1:18000"
DEFAULT_PAPERCLIP_URL = "http://127.0.0.1:3100/api/health"

# Reuse the existing secret-preserving renderer rather than inventing another
# .env generator. stack/local-ai/.env.example only uses keys it already knows how
# to generate or preserve.
sys.path.insert(0, str(INIT_ENV_DIR))
from init_env import parse_env_assignments, render_env  # noqa: E402


def run(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    print("$", " ".join(args))
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else str(REPO_ROOT),
        env=env,
        text=True,
        check=check,
        capture_output=capture_output,
    )


def render_root_env(force: bool) -> dict[str, str]:
    if not ENV_EXAMPLE.exists():
        raise SystemExit(f"missing env template: {ENV_EXAMPLE}")
    if ROOT_ENV.exists() and not force:
        values = parse_env_assignments(ROOT_ENV.read_text())
        print(f"Using existing env: {ROOT_ENV}")
        return values

    existing = parse_env_assignments(ROOT_ENV.read_text()) if ROOT_ENV.exists() else {}
    rendered = render_env(ENV_EXAMPLE.read_text(), existing)
    ROOT_ENV.write_text(rendered)
    os.chmod(ROOT_ENV, 0o600)
    print(f"Rendered env: {ROOT_ENV}")
    return parse_env_assignments(rendered)


def require_openrouter(values: dict[str, str], allow_missing: bool) -> None:
    if values.get("OPENROUTER_API_KEY", "").strip():
        return
    message = (
        "OPENROUTER_API_KEY is empty in .env. Set it before first boot so "
        "Honcho, Hermes, Paperclip, and optional Open WebUI share the same "
        "OpenRouter seed provider. Use --allow-missing-openrouter only for "
        "compose/config dry-runs."
    )
    if allow_missing:
        print(f"WARNING: {message}")
        return
    raise SystemExit(message)


def compose_base(profile: str | None) -> list[str]:
    project = os.environ.get("COMPOSE_PROJECT_NAME", "studio54")
    cmd = [
        "docker",
        "compose",
        "-p",
        project,
        "--env-file",
        str(ROOT_ENV),
        "-f",
        str(COMPOSE_FILE),
    ]
    if profile and profile != "none":
        cmd.extend(["--profile", profile])
    return cmd


def start_compose(profile: str | None, build: bool) -> None:
    cmd = compose_base(profile) + ["up", "-d"]
    if build:
        cmd.append("--build")
    run(cmd)


def stop_compose(profile: str | None) -> None:
    run(compose_base(profile) + ["down"])


def wait_http(url: str, timeout: int, label: str) -> None:
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        try:
            with request.urlopen(url, timeout=4) as response:
                if 200 <= response.status < 300:
                    print(f"{label} ready: {url}")
                    return
                last_error = f"HTTP {response.status}"
        except Exception as exc:  # noqa: BLE001 - operator-facing wait loop
            last_error = str(exc)
        time.sleep(2)
    raise SystemExit(f"timed out waiting for {label} at {url}: {last_error}")


def ensure_hermes(skip_install: bool) -> str:
    existing = shutil.which("hermes")
    if existing:
        print(f"Hermes already installed: {existing}")
        return existing
    if skip_install:
        raise SystemExit("Hermes is not on PATH and --skip-hermes-install was set")

    print("Installing Hermes on the host via upstream installer...")
    run(
        [
            "bash",
            "-lc",
            "curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash",
        ],
    )
    installed = shutil.which("hermes")
    if installed:
        return installed
    # Common installer path fallback for non-login shells.
    local_bin = Path.home() / ".local" / "bin" / "hermes"
    if local_bin.exists():
        return str(local_bin)
    raise SystemExit("Hermes install finished, but no hermes executable was found on PATH")


def project_hermes_runtime() -> None:
    if not PROJECT_HERMES_RUNTIME.exists():
        raise SystemExit(f"missing projection script: {PROJECT_HERMES_RUNTIME}")
    run([sys.executable, str(PROJECT_HERMES_RUNTIME), "--source", str(ROOT_ENV)])


def write_honcho_config(values: dict[str, str]) -> Path:
    raw_home = values.get("HERMES_HOME", "~/.hermes").strip() or "~/.hermes"
    hermes_home = Path(raw_home).expanduser()
    honcho_path = Path(
        values.get("HERMES_HONCHO_CONFIG_PATH", str(hermes_home / "honcho.json")).strip()
        or str(hermes_home / "honcho.json")
    ).expanduser()
    honcho_path.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "baseUrl": values.get("HONCHO_BASE_URL", DEFAULT_HONCHO_URL) or DEFAULT_HONCHO_URL,
        "workspace": values.get("HONCHO_WORKSPACE", "studio54-main") or "studio54-main",
        "peerName": values.get("HONCHO_OPERATOR_PEER", "mike") or "mike",
        "aiPeer": values.get("HONCHO_AI_PEER", "nikolai") or "nikolai",
        "enabled": True,
        "recallMode": "hybrid",
        "writeFrequency": "turn",
        "contextCadence": 1,
        "dialecticCadence": 1,
    }
    honcho_path.write_text(json.dumps(config, indent=2) + "\n")
    os.chmod(honcho_path, 0o600)
    print(f"Wrote Honcho config: {honcho_path}")
    return honcho_path


def configure_hermes(hermes_cmd: str, values: dict[str, str], smoke: bool) -> None:
    env = os.environ.copy()
    hermes_home = Path(values.get("HERMES_HOME", "~/.hermes") or "~/.hermes").expanduser()
    env["HERMES_HOME"] = str(hermes_home)
    env["OPENROUTER_API_KEY"] = values.get("OPENROUTER_API_KEY", "")

    run([hermes_cmd, "config", "set", "memory.provider", "honcho"], env=env)
    if smoke:
        run(
            [
                hermes_cmd,
                "chat",
                "-q",
                "Reply exactly: STUDIO54 HERMES READY",
                "--provider",
                values.get("HERMES_MODEL_PROVIDER", "openrouter") or "openrouter",
                "--model",
                values.get("HERMES_MODEL_DEFAULT", DEFAULT_MODEL) or DEFAULT_MODEL,
            ],
            env=env,
        )


def print_operator_next_steps(profile: str | None) -> None:
    print(
        """
Studio54 local bootstrap is up.

Core URLs:
  Honcho API:       http://127.0.0.1:18000/health
  Paperclip:        http://127.0.0.1:3100
  Broker:           http://127.0.0.1:8090
  Postgres:         127.0.0.1:5433
""".rstrip()
    )
    if profile == "ui":
        print("  Open WebUI:       http://127.0.0.1:8080")
    print(
        """
Deferred manual step:
  Configure Codex/OpenAI OAuth after first boot, for example:
    hermes login --provider openai-codex

Useful follow-ups:
  docker compose -p studio54 --env-file .env -f stack/local-ai/docker-compose.yml ps
  docker compose -p studio54 --env-file .env -f stack/local-ai/docker-compose.yml logs -f honcho-api paperclip
""".rstrip()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Start the simplified Studio54 local stack.")
    parser.add_argument("--profile", choices=["none", "ui"], default="none")
    parser.add_argument("--force-env", action="store_true", help="Regenerate .env while preserving real existing values.")
    parser.add_argument("--build", action="store_true", default=True, help="Build local Honcho/Paperclip/Broker images before starting.")
    parser.add_argument("--no-build", action="store_false", dest="build")
    parser.add_argument("--skip-hermes-install", action="store_true")
    parser.add_argument("--skip-hermes-smoke", action="store_true")
    parser.add_argument("--skip-paperclip-wait", action="store_true")
    parser.add_argument("--allow-missing-openrouter", action="store_true")
    parser.add_argument("--down", action="store_true", help="Stop the compose stack instead of starting it.")
    args = parser.parse_args()

    values = render_root_env(force=args.force_env)
    if args.down:
        stop_compose(args.profile)
        return 0

    require_openrouter(values, allow_missing=args.allow_missing_openrouter)
    start_compose(args.profile, build=args.build)
    wait_http(values.get("HONCHO_BASE_URL", DEFAULT_HONCHO_URL) or DEFAULT_HONCHO_URL, 180, "Honcho")
    if not args.skip_paperclip_wait:
        wait_http(DEFAULT_PAPERCLIP_URL, 180, "Paperclip")

    hermes_cmd = ensure_hermes(skip_install=args.skip_hermes_install)
    project_hermes_runtime()
    write_honcho_config(values)
    configure_hermes(hermes_cmd, values, smoke=not args.skip_hermes_smoke)
    print_operator_next_steps(args.profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
