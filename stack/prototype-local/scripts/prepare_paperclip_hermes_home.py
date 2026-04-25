#!/usr/bin/env python3
"""Prepare a Paperclip-managed per-company Hermes home."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from init_env import parse_env_assignments
from project_hermes_runtime import (
    DEFAULT_SOURCE,
    DEFAULT_SOURCE_FALLBACK,
    render_hermes_config,
    render_hermes_env,
)


DEFAULT_PAPERCLIP_HOME = "/paperclip"
DEFAULT_INSTANCE_ID = "default"
DEFAULT_PAPERCLIP_UID = 1000
DEFAULT_PAPERCLIP_GID = 1000
DEFAULT_HONCHO_BASE_URL = "http://127.0.0.1:18000"
DEFAULT_HONCHO_OPERATOR_PEER = "operator-root"


def resolve_source_path(path: Path | None) -> Path:
    if path is not None:
        return path.resolve()
    if DEFAULT_SOURCE.exists():
        return DEFAULT_SOURCE.resolve()
    return DEFAULT_SOURCE_FALLBACK.resolve()


def resolve_company_hermes_home(
    source_values: dict[str, str],
    *,
    company_id: str,
    override: Path | None,
    paperclip_home_override: Path | None,
    instance_id_override: str | None,
) -> Path:
    if override is not None:
        return override.resolve()

    if paperclip_home_override is not None:
        paperclip_home = paperclip_home_override.resolve()
    else:
        paperclip_home = resolve_paperclip_home(source_values)
    instance_id = (
        (instance_id_override or "").strip()
        or source_values.get("PAPERCLIP_INSTANCE_ID", "").strip()
        or DEFAULT_INSTANCE_ID
    )
    return (paperclip_home / "instances" / instance_id / "companies" / company_id / "hermes-home").resolve()


def resolve_paperclip_home(source_values: dict[str, str]) -> Path:
    host_home = source_values.get("PAPERCLIP_HOME_HOST_PATH", "").strip()
    if host_home:
        return Path(host_home).expanduser().resolve()

    config_host_path = source_values.get("PAPERCLIP_CONFIG_HOST_PATH", "").strip()
    if config_host_path:
        config_path = Path(config_host_path).expanduser().resolve()
        # .../<paperclip-home>/instances/<instance-id>/config.json
        if len(config_path.parents) >= 3:
            return config_path.parents[2]

    return Path(source_values.get("PAPERCLIP_HOME", "") or DEFAULT_PAPERCLIP_HOME).expanduser().resolve()


def ensure_runtime_dirs(hermes_home: Path) -> None:
    for child in ("skills", "sessions", "logs", "memories"):
        (hermes_home / child).mkdir(parents=True, exist_ok=True)
    keep = hermes_home / "skills" / ".keep"
    if not keep.exists():
        keep.write_text("")


def resolve_int(value: str | None, fallback: int) -> int:
    if value is None or value.strip() == "":
        return fallback
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"invalid integer value: {value}") from exc


def resolve_honcho_base_url(source_values: dict[str, str]) -> str:
    return source_values.get("HONCHO_BASE_URL", "").strip() or DEFAULT_HONCHO_BASE_URL


def resolve_honcho_operator_peer(source_values: dict[str, str], override: str | None) -> str:
    return (
        (override or "").strip()
        or source_values.get("HERMES_HONCHO_OPERATOR_PEER", "").strip()
        or DEFAULT_HONCHO_OPERATOR_PEER
    )


def resolve_honcho_ai_peer(company_id: str, agent_id: str | None) -> str:
    agent_id = (agent_id or "").strip()
    if agent_id:
        return f"paperclip-agent-{agent_id}"
    return f"paperclip-company-{company_id}-hermes"


def render_honcho_config(
    source_values: dict[str, str],
    *,
    company_id: str,
    agent_id: str | None,
    operator_peer: str | None,
) -> str:
    config = {
        "baseUrl": resolve_honcho_base_url(source_values),
        "workspace": company_id,
        "peerName": resolve_honcho_operator_peer(source_values, operator_peer),
        "aiPeer": resolve_honcho_ai_peer(company_id, agent_id),
        "enabled": True,
        "recallMode": "hybrid",
        "writeFrequency": "turn",
        "contextCadence": 1,
        "dialecticCadence": 1,
    }
    return json.dumps(config, indent=2, sort_keys=True) + "\n"


def chown_tree(path: Path, uid: int, gid: int) -> None:
    os.chown(path, uid, gid)
    for root, dirs, files in os.walk(path):
        for name in dirs:
            os.chown(Path(root) / name, uid, gid)
        for name in files:
            os.chown(Path(root) / name, uid, gid)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a company-scoped Hermes home for Paperclip hermes_local agents.",
    )
    parser.add_argument("--company-id", required=True, help="Paperclip company id.")
    parser.add_argument(
        "--agent-id",
        default=None,
        help=(
            "Optional Paperclip agent id. When provided, honcho.json uses it "
            "for the AI peer. Without it, the AI peer is company-scoped."
        ),
    )
    parser.add_argument(
        "--operator-peer",
        default=None,
        help=(
            "Operator-side Honcho peer. Defaults to HERMES_HONCHO_OPERATOR_PEER "
            "from source env or operator-root."
        ),
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Source env file. Defaults to repo-root .env, falling back to .env.example.",
    )
    parser.add_argument(
        "--home-output",
        type=Path,
        default=None,
        help=(
            "Hermes home output path. Defaults to "
            "/paperclip/instances/<instance>/companies/<company-id>/hermes-home."
        ),
    )
    parser.add_argument(
        "--paperclip-home",
        type=Path,
        default=None,
        help="Override the Paperclip home root. Defaults to PAPERCLIP_HOME or /paperclip.",
    )
    parser.add_argument(
        "--instance-id",
        default=None,
        help="Override the Paperclip instance id. Defaults to PAPERCLIP_INSTANCE_ID or default.",
    )
    parser.add_argument(
        "--owner-uid",
        type=int,
        default=None,
        help="UID that should own the prepared tree. Defaults to PAPERCLIP_USER_UID, USER_UID, or 1000.",
    )
    parser.add_argument(
        "--owner-gid",
        type=int,
        default=None,
        help="GID that should own the prepared tree. Defaults to PAPERCLIP_USER_GID, USER_GID, or 1000.",
    )
    args = parser.parse_args()

    source_path = resolve_source_path(args.source)
    if not source_path.exists():
        raise SystemExit(f"missing source env: {source_path}")

    source_values = parse_env_assignments(source_path.read_text())
    hermes_home = resolve_company_hermes_home(
        source_values,
        company_id=args.company_id,
        override=args.home_output,
        paperclip_home_override=args.paperclip_home,
        instance_id_override=args.instance_id,
    )
    env_path = hermes_home / ".env"
    config_path = hermes_home / "config.yaml"
    honcho_config_path = hermes_home / "honcho.json"

    hermes_home.mkdir(parents=True, exist_ok=True)
    ensure_runtime_dirs(hermes_home)
    env_path.write_text(render_hermes_env(source_values))
    config_path.write_text(render_hermes_config(source_values))
    honcho_config_path.write_text(
        render_honcho_config(
            source_values,
            company_id=args.company_id,
            agent_id=args.agent_id,
            operator_peer=args.operator_peer,
        )
    )

    os.chmod(env_path, 0o600)
    os.chmod(config_path, 0o600)
    os.chmod(honcho_config_path, 0o600)

    owner_uid = (
        args.owner_uid
        if args.owner_uid is not None
        else resolve_int(
            source_values.get("PAPERCLIP_USER_UID") or os.environ.get("PAPERCLIP_USER_UID") or os.environ.get("USER_UID"),
            DEFAULT_PAPERCLIP_UID,
        )
    )
    owner_gid = (
        args.owner_gid
        if args.owner_gid is not None
        else resolve_int(
            source_values.get("PAPERCLIP_USER_GID") or os.environ.get("PAPERCLIP_USER_GID") or os.environ.get("USER_GID"),
            DEFAULT_PAPERCLIP_GID,
        )
    )
    company_root = hermes_home.parent
    os.chown(company_root.parent, owner_uid, owner_gid)
    chown_tree(company_root, owner_uid, owner_gid)

    print(hermes_home)
    print(env_path)
    print(config_path)
    print(honcho_config_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
