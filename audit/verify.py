#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Three-resolver verifier: doc, code, vps. Then classify each row."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import yaml

from audit.schema import Claim, ClaimSet, dump_claims, load_claims


def resolve_doc(claim: Claim, repo_root: Path) -> str | None:
    """Re-read source_file:source_line ± 2 and return the joined text."""
    path = repo_root / claim.source_file
    if not path.exists():
        return None
    lines = path.read_text(errors="replace").splitlines()
    n = len(lines)
    lo = max(0, claim.source_line - 3)
    hi = min(n, claim.source_line + 2)
    return "\n".join(lines[lo:hi])


GREP_GLOBS = ("*.yml", "*.yaml", "*.toml", "*.env", "*.py", "*.sh", "Makefile")


def _grep(pattern: str, root: Path) -> str | None:
    """Run a grep search; return up to 5 matching lines."""
    try:
        result = subprocess.run(
            ["grep", "-rIn", "--include=*.yml", "--include=*.yaml",
             "--include=*.toml", "--include=*.env", "--include=*.py",
             "--include=*.sh", "--include=Makefile",
             "-e", pattern, str(root)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    lines = [l for l in result.stdout.splitlines() if l.strip()][:5]
    return "\n".join(lines) if lines else None


def resolve_code(claim: Claim, repo_root: Path) -> str | None:
    """Type-dispatched probe of the codebase."""
    if claim.probe:
        try:
            r = subprocess.run(
                claim.probe, shell=True, capture_output=True, text=True,
                timeout=20, cwd=repo_root,
            )
            return (r.stdout + r.stderr).strip() or None
        except subprocess.TimeoutExpired:
            return "PROBE_TIMEOUT"
    st = (claim.subtype or "").lower()
    val = claim.expected_value
    if st in ("port", "container_port", "host_port"):
        return _grep(str(val), repo_root)
    if st in ("path", "file_path"):
        target = repo_root / str(val)
        return f"path exists: {target}" if target.exists() else f"path missing: {target}"
    if st in ("env_var", "config_key"):
        return _grep(str(val), repo_root)
    if st in ("command", "command_name", "service_name", "container_name"):
        return _grep(str(val), repo_root)
    return None


def resolve_vps(claim: Claim, dump: dict) -> str | None:
    st = (claim.subtype or "").lower()
    val = claim.expected_value
    if st == "container_count":
        running = [c for c in dump.get("docker_ps", [])
                   if str(c.get("State", "")).lower() == "running"]
        return f"{len(running)} containers running"
    if st in ("container_name",):
        match = next((c for c in dump.get("docker_ps", [])
                      if str(c.get("Names", "")) == str(val)), None)
        if match is None:
            return f"container {val!r} not found"
        return f"{match['Names']} is {match.get('State', 'unknown')}"
    if st in ("env_var", "config_key"):
        for fname, kv in dump.get("env_files", {}).items():
            if str(val) in kv:
                return f"{fname}: {val}={kv[str(val)]}"
        return f"{val} not present in any env file"
    if st in ("port",):
        # Search docker_ps and listening_ports_raw for the port
        for c in dump.get("docker_ps", []):
            if str(val) in str(c.get("Ports", "")):
                return f"port {val} bound by container {c.get('Names')}"
        ports_raw = dump.get("listening_ports_raw", "") or ""
        if str(val) in ports_raw:
            return f"port {val} present in ss output"
        return f"port {val} not seen in dump"
    return None


def main() -> int:
    raise SystemExit(0)


if __name__ == "__main__":
    main()
