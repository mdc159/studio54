#!/usr/bin/env python3
"""Prepare a Paperclip-managed per-company Hermes home."""

from __future__ import annotations

import argparse
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

    paperclip_home = (
        paperclip_home_override.resolve()
        if paperclip_home_override is not None
        else Path(source_values.get("PAPERCLIP_HOME", "") or DEFAULT_PAPERCLIP_HOME).expanduser().resolve()
    )
    instance_id = (
        (instance_id_override or "").strip()
        or source_values.get("PAPERCLIP_INSTANCE_ID", "").strip()
        or DEFAULT_INSTANCE_ID
    )
    return (paperclip_home / "instances" / instance_id / "companies" / company_id / "hermes-home").resolve()


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

    hermes_home.mkdir(parents=True, exist_ok=True)
    ensure_runtime_dirs(hermes_home)
    env_path.write_text(render_hermes_env(source_values))
    config_path.write_text(render_hermes_config(source_values))

    os.chmod(env_path, 0o600)
    os.chmod(config_path, 0o600)

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
    chown_tree(company_root, owner_uid, owner_gid)

    print(hermes_home)
    print(env_path)
    print(config_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
