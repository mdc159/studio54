from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from .topology import resolve_paths

GRID_CONFIG = "hermes-grid.json"
EXPECTED_VICTORIA_COMMAND = "ssh victoria -t victoria-attach"


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def _config_path() -> Path:
    return resolve_paths().topology_root / GRID_CONFIG


def load_grid_config(path: Path | None = None) -> dict:
    config_path = path or _config_path()
    return json.loads(config_path.read_text(encoding="utf-8"))


def _check(status: str, name: str, detail: str) -> Check:
    return Check(name=name, status=status, detail=detail)


def _run(
    args: Sequence[str],
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    return runner(args, check=False, text=True, capture_output=True, timeout=8)


def _ssh_alias_detail(ssh_fields: dict[str, str]) -> str:
    """Summarize an SSH alias without exposing hostnames/IPs or key material."""
    return " ".join(
        (
            "hostname=<configured>" if ssh_fields.get("hostname") else "hostname=<unset>",
            f"user={ssh_fields.get('user', '<unset>')}",
            f"port={ssh_fields.get('port', '<unset>')}",
        )
    )


def collect_checks(
    *,
    probe_remote: bool = False,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    which: Callable[[str], str | None] = shutil.which,
) -> list[Check]:
    checks: list[Check] = []
    path = _config_path()

    if not path.exists():
        return [_check("FAIL", "grid_config", f"missing {path.relative_to(resolve_paths().repo_root)}")]

    try:
        config = load_grid_config(path)
    except json.JSONDecodeError as exc:
        return [_check("FAIL", "grid_config", f"invalid JSON: {exc}")]

    checks.append(_check("PASS", "grid_config", str(path.relative_to(resolve_paths().repo_root))))

    tabs = config.get("tabs", [])
    enabled = [tab for tab in tabs if tab.get("enabled")]
    victoria = next((tab for tab in tabs if tab.get("name") == "Victoria"), None)

    if victoria is None:
        checks.append(_check("FAIL", "victoria_tab", "missing Victoria tab definition"))
    elif not victoria.get("enabled"):
        checks.append(_check("FAIL", "victoria_tab", "Victoria tab is not enabled"))
    else:
        checks.append(_check("PASS", "victoria_tab", "Victoria is the only intended enabled remote tab"))

    other_enabled = [tab.get("name", "<unnamed>") for tab in enabled if tab.get("name") != "Victoria"]
    if other_enabled:
        checks.append(_check("FAIL", "expansion_block", f"unexpected enabled tabs: {', '.join(other_enabled)}"))
    else:
        checks.append(_check("PASS", "expansion_block", "Nikolai/WSL/Termux are not enabled"))

    command = victoria.get("command") if isinstance(victoria, dict) else None
    if command == EXPECTED_VICTORIA_COMMAND:
        checks.append(_check("PASS", "victoria_command", command))
    else:
        checks.append(_check("FAIL", "victoria_command", f"expected {EXPECTED_VICTORIA_COMMAND!r}, got {command!r}"))

    ssh_path = which("ssh")
    if ssh_path:
        checks.append(_check("PASS", "ssh_binary", "ssh available"))
    else:
        checks.append(_check("WARN", "ssh_binary", "ssh not found in PATH; cannot validate alias locally"))

    tmux_path = which("tmux")
    if tmux_path:
        checks.append(_check("PASS", "tmux_binary", "tmux available for hub launch environment"))
    else:
        checks.append(_check("WARN", "tmux_binary", "tmux not found in PATH; grid launch may need a terminal host"))

    if ssh_path:
        alias = str(victoria.get("ssh_alias", "victoria")) if isinstance(victoria, dict) else "victoria"
        result = _run(["ssh", "-G", alias], runner)
        if result.returncode == 0:
            ssh_fields = {}
            for line in result.stdout.splitlines():
                if " " not in line:
                    continue
                key, value = line.split(" ", 1)
                if key in {"hostname", "user", "port"}:
                    ssh_fields[key] = value
            checks.append(
                _check(
                    "PASS",
                    "ssh_alias",
                    _ssh_alias_detail(ssh_fields),
                )
            )
        else:
            checks.append(_check("WARN", "ssh_alias", "ssh alias 'victoria' is not resolvable in this environment"))

    if probe_remote:
        if not ssh_path:
            checks.append(_check("WARN", "remote_probe", "skipped: ssh unavailable"))
        else:
            result = _run(
                [
                    "ssh",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "ConnectTimeout=8",
                    "victoria",
                    "([ -x /root/.local/bin/victoria-attach ] || command -v victoria-attach >/dev/null) && tmux has-session -t victoria-hermes",
                ],
                runner,
            )
            if result.returncode == 0:
                checks.append(_check("PASS", "remote_probe", "victoria-attach exists and victoria-hermes tmux session exists"))
            else:
                checks.append(_check("WARN", "remote_probe", "remote probe did not pass; attach flow may still work interactively"))
    else:
        checks.append(_check("PASS", "remote_probe", "skipped by default; use --probe-remote for non-interactive SSH check"))

    return checks


def format_checks(checks: Sequence[Check]) -> str:
    lines = ["Studio54 hermes-grid readiness check", ""]
    for check in checks:
        lines.append(f"{check.status:4} {check.name}: {check.detail}")
    lines.append("")
    lines.append("Dry-run launch summary:")
    lines.append(f"  Victoria: {EXPECTED_VICTORIA_COMMAND}")
    lines.append("  Nikolai/WSL/Termux: disabled pending Victoria-only pass")
    return "\n".join(lines)


def checks_exit_code(checks: Sequence[Check]) -> int:
    return 1 if any(check.status == "FAIL" for check in checks) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hermes-grid")
    parser.add_argument("--check", action="store_true", help="Run read-only readiness checks and print the dry-run launch summary.")
    parser.add_argument("--probe-remote", action="store_true", help="Include a non-interactive SSH probe for Victoria. Off by default.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print machine-readable check output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.check:
        parser.error("only --check is implemented in Phase 1.5")
        return 2

    checks = collect_checks(probe_remote=args.probe_remote)
    if args.as_json:
        print(json.dumps([check.__dict__ for check in checks], indent=2, sort_keys=True))
    else:
        print(format_checks(checks))
    return checks_exit_code(checks)


if __name__ == "__main__":
    raise SystemExit(main())
