from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from .topology import resolve_paths

GRID_CONFIG = "hermes-grid.json"
EXPECTED_VICTORIA_COMMAND = "ssh victoria -t victoria-attach"
EXPECTED_NIKOLI_COMMAND = "ssh nikoli -t ~/.local/bin/nikolai-attach"


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


def _ssh_config_fields(stdout: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in stdout.splitlines():
        if " " not in line:
            continue
        key, value = line.split(" ", 1)
        if key in {"hostname", "user", "port"}:
            fields[key] = value
    return fields


def _probe_script(tab: dict) -> str:
    session = shlex.quote(str(tab.get("expected_tmux_session", "")))
    window = shlex.quote(str(tab.get("expected_window_label", "")))
    fallback = shlex.quote(str(tab.get("fallback_command", "")))
    return " && ".join(
        [
            f"([ -x \"$HOME/.local/bin/{str(tab.get('fallback_command', ''))}\" ] || command -v {fallback} >/dev/null)",
            f"tmux has-session -t {session}",
            f"tmux list-windows -t {session} -F '#{{window_name}}' | grep -Fx {window} >/dev/null",
        ]
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
    nikoli = next((tab for tab in tabs if tab.get("name") == "Nikolai"), None)

    if victoria is None:
        checks.append(_check("FAIL", "victoria_tab", "missing Victoria tab definition"))
    elif not victoria.get("enabled"):
        checks.append(_check("FAIL", "victoria_tab", "Victoria tab is not enabled"))
    else:
        checks.append(_check("PASS", "victoria_tab", "Victoria is the only intended enabled remote tab"))

    allowed_enabled = {"Victoria", "Nikolai"}
    other_enabled = [tab.get("name", "<unnamed>") for tab in enabled if tab.get("name") not in allowed_enabled]
    if other_enabled:
        checks.append(_check("FAIL", "expansion_block", f"unexpected enabled tabs: {', '.join(other_enabled)}"))
    else:
        checks.append(_check("PASS", "expansion_block", "Victoria and Nikolai are the only enabled tabs; Android/WSL/Termux remain pending"))

    command = victoria.get("command") if isinstance(victoria, dict) else None
    if command == EXPECTED_VICTORIA_COMMAND:
        checks.append(_check("PASS", "victoria_command", command))
    else:
        checks.append(_check("FAIL", "victoria_command", f"expected {EXPECTED_VICTORIA_COMMAND!r}, got {command!r}"))

    if nikoli is None:
        checks.append(_check("FAIL", "nikoli_tab", "missing Nikolai tab definition"))
    elif nikoli.get("kind") != "wsl-workstation-persona":
        checks.append(_check("FAIL", "nikoli_tab", f"expected wsl-workstation-persona, got {nikoli.get('kind')!r}"))
    elif nikoli.get("attach_mode") != "ssh-tmux":
        checks.append(_check("FAIL", "nikoli_tab", f"expected attach_mode='ssh-tmux', got {nikoli.get('attach_mode')!r}"))
    else:
        state = "enabled" if nikoli.get("enabled") else "disabled"
        checks.append(_check("PASS", "nikoli_tab", f"Nikolai {state} kind=wsl-workstation-persona attach_mode=ssh-tmux"))

    nikoli_command = nikoli.get("command") if isinstance(nikoli, dict) else None
    if nikoli_command == EXPECTED_NIKOLI_COMMAND:
        checks.append(_check("PASS", "nikoli_attach_plan", nikoli_command))
    else:
        checks.append(_check("FAIL", "nikoli_attach_plan", f"expected {EXPECTED_NIKOLI_COMMAND!r}, got {nikoli_command!r}"))

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
            checks.append(
                _check(
                    "PASS",
                    "ssh_alias",
                    _ssh_alias_detail(_ssh_config_fields(result.stdout)),
                )
            )
        else:
            checks.append(_check("WARN", "ssh_alias", "ssh alias 'victoria' is not resolvable in this environment"))

        nikoli_alias = str(nikoli.get("ssh_alias", "nikoli")) if isinstance(nikoli, dict) else "nikoli"
        result = _run(["ssh", "-G", nikoli_alias], runner)
        if result.returncode == 0:
            checks.append(
                _check(
                    "PASS",
                    "nikoli_ssh_alias",
                    _ssh_alias_detail(_ssh_config_fields(result.stdout)),
                )
            )
        else:
            checks.append(_check("WARN", "nikoli_ssh_alias", "ssh alias 'nikoli' is not resolvable in this environment"))

    if probe_remote:
        if not ssh_path:
            checks.append(_check("WARN", "remote_probe", "skipped: ssh unavailable"))
            checks.append(_check("WARN", "nikoli_remote_probe", "skipped: ssh unavailable"))
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

            nikoli_alias = str(nikoli.get("ssh_alias", "nikoli")) if isinstance(nikoli, dict) else "nikoli"
            result = _run(
                [
                    "ssh",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    "ConnectTimeout=8",
                    nikoli_alias,
                    _probe_script(nikoli or {}),
                ],
                runner,
            )
            if result.returncode == 0:
                checks.append(_check("PASS", "nikoli_remote_probe", "Nikolai attach wrapper and tmux/Hermes markers present"))
            else:
                checks.append(_check("WARN", "nikoli_remote_probe", "Nikolai WSL probe did not pass; topology remains disabled"))
    else:
        checks.append(_check("PASS", "remote_probe", "skipped by default; use --probe-remote for non-interactive SSH check"))
        checks.append(_check("PASS", "nikoli_remote_probe", "skipped by default; use --probe-remote for WSL workstation SSH check"))

    return checks


def format_checks(checks: Sequence[Check]) -> str:
    lines = ["Studio54 hermes-grid readiness check", ""]
    for check in checks:
        lines.append(f"{check.status:4} {check.name}: {check.detail}")
    lines.append("")
    lines.append("Dry-run launch summary:")
    lines.append(f"  Victoria: {EXPECTED_VICTORIA_COMMAND}")
    lines.append(f"  Nikolai: {EXPECTED_NIKOLI_COMMAND} (enabled; explicit operator attach only)")
    lines.append("  Android/WSL/Termux: disabled pending readiness gates")
    return "\n".join(lines)


def format_roster(config: dict | None = None) -> str:
    grid = config or load_grid_config()
    hub = grid.get("hub", "Studio54 / Donna")
    lines = ["Studio54 hermes-grid roster", "", f"Hub: {hub}"]
    lines.append("Donna: role=hub status=operator-control-plane")
    lines.append("")
    lines.append("Tabs:")
    for tab in _tabs(grid):
        name = tab.get("name", "<unnamed>")
        state = "enabled" if tab.get("enabled") else "disabled"
        kind = tab.get("kind", "<unset>")
        lines.append(f"  {name}: {state} kind={kind}")
    lines.append("")
    lines.append("Safety: roster is local/topology-only; no remote execution")
    return "\n".join(lines)


def format_status(config: dict | None = None) -> str:
    grid = config or load_grid_config()
    enabled_tabs = [tab.get("name", "<unnamed>") for tab in _tabs(grid) if tab.get("enabled")]
    pending_tabs = [tab.get("name", "<unnamed>") for tab in _tabs(grid) if not tab.get("enabled")]
    lines = ["Studio54 hermes-grid status", ""]
    lines.append("Donna hub: READY")
    lines.append(f"Enabled tabs: {', '.join(enabled_tabs) if enabled_tabs else 'none'}")
    lines.append(f"Pending tabs: {', '.join(pending_tabs) if pending_tabs else 'none'}")
    lines.append("remote execution: none")
    lines.append("")
    lines.append("Sound-off contract:")
    for field in ["outcome", "confirmed", "changed", "validation", "safety", "next_action"]:
        lines.append(f"  - {field}")
    return "\n".join(lines)


def checks_exit_code(checks: Sequence[Check]) -> int:
    return 1 if any(check.status == "FAIL" for check in checks) else 0


def _tabs(config: dict | None = None) -> list[dict]:
    grid = config or load_grid_config()
    return [tab for tab in grid.get("tabs", []) if isinstance(tab, dict)]


def find_tab(name: str, config: dict | None = None) -> dict | None:
    return next((tab for tab in _tabs(config) if tab.get("name") == name), None)


def build_attach_command(name: str, config: dict | None = None) -> list[str]:
    tab = find_tab(name, config)
    if tab is None:
        raise ValueError(f"unknown grid tab: {name}")
    command = tab.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError(f"grid tab {name!r} has no attach command")
    return shlex.split(command)


def attach_tab(
    name: str,
    *,
    dry_run: bool = False,
    attach_runner: Callable[[Sequence[str]], int] = subprocess.call,
) -> int:
    tab = find_tab(name)
    if tab is None:
        print(f"FAIL attach: unknown tab {name!r}")
        return 1
    if not tab.get("enabled"):
        print(f"FAIL attach: tab {name} is disabled; enable it in topology only after validation")
        return 1
    attach_mode = tab.get("attach_mode", tab.get("kind"))
    if attach_mode == "remote-ssh-tmux":
        attach_mode = "ssh-tmux"
    if attach_mode != "ssh-tmux":
        print(f"FAIL attach: tab {name} uses unsupported attach mode {attach_mode!r}")
        return 1

    command = build_attach_command(name)
    command_display = shlex.join(command)
    print("Runtime attach plan")
    print(f"  tab={name}")
    print(f"  kind={tab.get('kind')}")
    print(f"  attach_mode={attach_mode}")
    print(f"  command={command_display}")
    print("  safety=explicit operator attach; no prompt injection; no session creation")
    if dry_run:
        print("  mode=dry-run")
        return 0
    return int(attach_runner(command))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hermes-grid")
    parser.add_argument("command", nargs="?", choices=["attach", "roster", "status"], help="Runtime command. Use 'attach' to open an explicit operator attach session; 'roster' and 'status' are local-only hub views.")
    parser.add_argument("tab", nargs="?", help="Grid tab name for runtime commands, for example Victoria.")
    parser.add_argument("--check", action="store_true", help="Run read-only readiness checks and print the dry-run launch summary.")
    parser.add_argument("--probe-remote", action="store_true", help="Include a non-interactive SSH probe for Victoria. Off by default.")
    parser.add_argument("--dry-run", action="store_true", help="For runtime commands, print the attach plan without executing it.")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Print machine-readable check output.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "attach":
        if args.as_json:
            parser.error("--json is only supported with --check")
        if not args.tab:
            parser.error("attach requires a tab name, e.g. hermes-grid attach Victoria")
        return attach_tab(args.tab, dry_run=args.dry_run)

    if args.command in {"roster", "status"}:
        if args.tab:
            parser.error(f"{args.command} does not accept a tab argument")
        if args.as_json:
            parser.error("--json is only supported with --check")
        if args.probe_remote:
            parser.error("--probe-remote is only supported with --check")
        if args.dry_run:
            parser.error("--dry-run is only supported with runtime attach")
        if args.command == "roster":
            print(format_roster())
        else:
            print(format_status())
        return 0

    if not args.check:
        parser.error("use --check for readiness, 'roster'/'status' for local hub views, or 'attach <tab>' for explicit runtime attach")
        return 2

    if args.dry_run:
        parser.error("--dry-run is only supported with runtime commands")

    checks = collect_checks(probe_remote=args.probe_remote)
    if args.as_json:
        print(json.dumps([check.__dict__ for check in checks], indent=2, sort_keys=True))
    else:
        print(format_checks(checks))
    return checks_exit_code(checks)


if __name__ == "__main__":
    raise SystemExit(main())
