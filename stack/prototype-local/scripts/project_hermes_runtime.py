#!/usr/bin/env python3
"""Project the canonical repo-root .env contract into Hermes runtime files."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from init_env import parse_env_assignments


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE = REPO_ROOT / ".env"
DEFAULT_SOURCE_FALLBACK = REPO_ROOT / ".env.example"
DEFAULT_ROOT_EXAMPLE = REPO_ROOT / ".env.example"

DEFAULT_HERMES_HOME = "/root/.hermes"
DEFAULT_HERMES_ENV_PATH = f"{DEFAULT_HERMES_HOME}/.env"
DEFAULT_HERMES_CONFIG_PATH = f"{DEFAULT_HERMES_HOME}/config.yaml"

DEFAULT_HERMES_MODEL = "google/gemini-2.5-flash"
DEFAULT_HERMES_PROVIDER = "openrouter"
DEFAULT_HERMES_BASE_URL = "https://openrouter.ai/api/v1"

PROJECTED_ENV_KEYS = (
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
)


def resolve_source_path(path: Path | None) -> Path:
    if path is not None:
        return path.resolve()
    if DEFAULT_SOURCE.exists():
        return DEFAULT_SOURCE.resolve()
    return DEFAULT_SOURCE_FALLBACK.resolve()


def resolve_output_path(
    source_values: dict[str, str],
    *,
    source_key: str,
    fallback: str,
    override: Path | None,
) -> Path:
    if override is not None:
        return override.resolve()
    configured = source_values.get(source_key, "").strip()
    return Path(configured or fallback).expanduser().resolve()


def render_hermes_env(source_values: dict[str, str]) -> str:
    lines = [
        "# Generated from the repo-root operator .env",
        "# Edit the root .env and re-run project_hermes_runtime.py",
        "",
    ]
    for key in PROJECTED_ENV_KEYS:
        value = source_values.get(key, "").strip()
        if value:
            lines.append(f"{key}={value}")
    return "\n".join(lines).rstrip() + "\n"


def quote_yaml(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_hermes_config(source_values: dict[str, str]) -> str:
    model = source_values.get("HERMES_MODEL_DEFAULT", "").strip() or DEFAULT_HERMES_MODEL
    provider = source_values.get("HERMES_MODEL_PROVIDER", "").strip() or DEFAULT_HERMES_PROVIDER
    base_url = source_values.get("HERMES_MODEL_BASE_URL", "").strip() or DEFAULT_HERMES_BASE_URL

    return "\n".join(
        [
            "# Generated from the repo-root operator .env",
            "# Edit the root .env and re-run project_hermes_runtime.py",
            "",
            "model:",
            f"  default: {quote_yaml(model)}",
            f"  provider: {quote_yaml(provider)}",
            f"  base_url: {quote_yaml(base_url)}",
            "",
            "terminal:",
            '  backend: "local"',
            '  cwd: "."',
            "  timeout: 180",
            "  lifetime_seconds: 300",
            "",
            "browser:",
            "  inactivity_timeout: 120",
            "",
            "memory:",
            "  memory_enabled: true",
            "  user_profile_enabled: true",
            "  memory_char_limit: 2200",
            "  user_char_limit: 1375",
            "",
            "compression:",
            "  enabled: true",
            "  threshold: 0.50",
            "  target_ratio: 0.20",
            "  protect_last_n: 20",
            "",
            "display:",
            "  compact: false",
            "  tool_progress: all",
            "  interim_assistant_messages: true",
            "  busy_input_mode: interrupt",
            "  background_process_notifications: all",
            "  bell_on_complete: false",
            "  show_reasoning: false",
            "  streaming: true",
            '  skin: "default"',
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Project repo-root .env values into Hermes runtime files.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Source env file. Defaults to repo-root .env, falling back to .env.example.",
    )
    parser.add_argument(
        "--env-output",
        type=Path,
        default=None,
        help="Hermes runtime .env output path. Defaults to HERMES_ENV_PATH from source or /root/.hermes/.env.",
    )
    parser.add_argument(
        "--config-output",
        type=Path,
        default=None,
        help="Hermes runtime config.yaml output path. Defaults to HERMES_CONFIG_PATH from source or /root/.hermes/config.yaml.",
    )
    args = parser.parse_args()

    source_path = resolve_source_path(args.source)
    root_example_path = DEFAULT_ROOT_EXAMPLE.resolve()

    if not source_path.exists():
        raise SystemExit(f"missing source env: {source_path}")
    if not root_example_path.exists():
        raise SystemExit(f"missing root example template: {root_example_path}")

    source_values = parse_env_assignments(source_path.read_text())
    env_output_path = resolve_output_path(
        source_values,
        source_key="HERMES_ENV_PATH",
        fallback=DEFAULT_HERMES_ENV_PATH,
        override=args.env_output,
    )
    config_output_path = resolve_output_path(
        source_values,
        source_key="HERMES_CONFIG_PATH",
        fallback=DEFAULT_HERMES_CONFIG_PATH,
        override=args.config_output,
    )

    env_output_path.parent.mkdir(parents=True, exist_ok=True)
    config_output_path.parent.mkdir(parents=True, exist_ok=True)

    env_output_path.write_text(render_hermes_env(source_values))
    config_output_path.write_text(render_hermes_config(source_values))

    os.chmod(env_output_path, 0o600)
    os.chmod(config_output_path, 0o600)

    print(env_output_path)
    print(config_output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
