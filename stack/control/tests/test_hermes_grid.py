from __future__ import annotations

import subprocess

from control1215 import hermes_grid


def _completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr="")


def test_hermes_grid_check_lists_victoria_only(capsys) -> None:
    assert hermes_grid.main(["--check"]) == 0
    out = capsys.readouterr().out
    assert "Studio54 hermes-grid readiness check" in out
    assert "PASS victoria_tab" in out
    assert "ssh victoria -t victoria-attach" in out
    assert "Nikolai/WSL/Termux: disabled" in out


def test_collect_checks_sanitizes_ssh_alias_details() -> None:
    def fake_runner(*args, **kwargs):
        return _completed("hostname paperclip.tailnet.example\nuser root\nport 22\nidentityfile /secret/key\n")

    checks = hermes_grid.collect_checks(
        runner=fake_runner,
        which=lambda name: f"/usr/bin/{name}" if name in {"ssh", "tmux"} else None,
    )
    alias = next(check for check in checks if check.name == "ssh_alias")
    assert alias.status == "PASS"
    assert "hostname=<configured>" in alias.detail
    assert "paperclip.tailnet.example" not in alias.detail
    assert "user=root" in alias.detail
    assert "port=22" in alias.detail
    assert "identityfile" not in alias.detail
    assert "/secret/key" not in alias.detail


def test_remote_probe_is_skipped_by_default() -> None:
    calls = []

    def fake_runner(*args, **kwargs):
        calls.append(args)
        return _completed("hostname example\nuser root\nport 22\n")

    checks = hermes_grid.collect_checks(
        runner=fake_runner,
        which=lambda name: f"/usr/bin/{name}" if name in {"ssh", "tmux"} else None,
    )
    remote_probe = next(check for check in checks if check.name == "remote_probe")
    assert remote_probe.status == "PASS"
    assert "skipped by default" in remote_probe.detail
    assert len(calls) == 1


def test_remote_probe_can_run_non_interactive_check() -> None:
    calls = []

    def fake_runner(args, **kwargs):
        calls.append(args)
        if args[:2] == ["ssh", "-G"]:
            return _completed("hostname example\nuser root\nport 22\n")
        return _completed(returncode=0)

    checks = hermes_grid.collect_checks(
        probe_remote=True,
        runner=fake_runner,
        which=lambda name: f"/usr/bin/{name}" if name in {"ssh", "tmux"} else None,
    )
    remote_probe = next(check for check in checks if check.name == "remote_probe")
    assert remote_probe.status == "PASS"
    assert any("BatchMode=yes" in call for call in calls)


def test_build_attach_command_uses_enabled_tab_command_from_topology() -> None:
    command = hermes_grid.build_attach_command("Victoria")
    assert command == ["ssh", "victoria", "-t", "victoria-attach"]


def test_attach_refuses_disabled_tabs_without_running_command(capsys) -> None:
    calls = []

    def fake_attach_runner(*args, **kwargs):
        calls.append(args)
        return 0

    exit_code = hermes_grid.attach_tab("Nikolai", attach_runner=fake_attach_runner)

    out = capsys.readouterr().out
    assert exit_code == 1
    assert calls == []
    assert "disabled" in out
    assert "Nikolai" in out


def test_attach_dry_run_prints_generic_runtime_plan_without_executing(capsys) -> None:
    calls = []

    def fake_attach_runner(*args, **kwargs):
        calls.append(args)
        return 0

    exit_code = hermes_grid.attach_tab("Victoria", dry_run=True, attach_runner=fake_attach_runner)

    out = capsys.readouterr().out
    assert exit_code == 0
    assert calls == []
    assert "Runtime attach plan" in out
    assert "tab=Victoria" in out
    assert "ssh victoria -t victoria-attach" in out
    assert "hostname=" not in out


def test_attach_executes_enabled_tab_command_only_when_explicit() -> None:
    calls = []

    def fake_attach_runner(args):
        calls.append(args)
        return 0

    exit_code = hermes_grid.attach_tab("Victoria", attach_runner=fake_attach_runner)

    assert exit_code == 0
    assert calls == [["ssh", "victoria", "-t", "victoria-attach"]]


def test_roster_prints_donna_hub_and_tab_states(capsys) -> None:
    assert hermes_grid.main(["roster"]) == 0
    out = capsys.readouterr().out
    assert "Studio54 hermes-grid roster" in out
    assert "Hub: Studio54 / Donna" in out
    assert "Donna: role=hub status=operator-control-plane" in out
    assert "Victoria: enabled kind=remote-ssh-tmux" in out
    assert "Nikolai: disabled kind=pending" in out
    assert "Termux: disabled kind=pending" in out
    assert "hostname=" not in out


def test_status_prints_sound_off_contract_without_remote_execution(capsys) -> None:
    assert hermes_grid.main(["status"]) == 0
    out = capsys.readouterr().out
    assert "Studio54 hermes-grid status" in out
    assert "Donna hub: READY" in out
    assert "Sound-off contract:" in out
    for field in ["outcome", "confirmed", "changed", "validation", "safety", "next_action"]:
        assert field in out
    assert "remote execution: none" in out
