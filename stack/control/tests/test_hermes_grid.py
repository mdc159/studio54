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
    assert "Nikolai: ssh nikoli -t ~/.local/bin/nikolai-attach" in out
    assert "enabled; explicit operator attach only" in out


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
    assert len(calls) == 2
    assert calls[0][0] == ["ssh", "-G", "victoria"]
    assert calls[1][0] == ["ssh", "-G", "nikoli"]


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


def test_nikoli_metadata_is_checked_after_explicit_live_attach_enablement() -> None:
    checks = hermes_grid.collect_checks(
        runner=lambda *args, **kwargs: _completed("hostname nikoli-wsl\nuser mdc159\nport 22\n"),
        which=lambda name: f"/usr/bin/{name}" if name in {"ssh", "tmux"} else None,
    )

    nikoli_tab = next(check for check in checks if check.name == "nikoli_tab")
    nikoli_attach = next(check for check in checks if check.name == "nikoli_attach_plan")

    assert nikoli_tab.status == "PASS"
    assert "enabled" in nikoli_tab.detail
    assert "wsl-workstation-persona" in nikoli_tab.detail
    assert "attach_mode=ssh-tmux" in nikoli_tab.detail
    assert nikoli_attach.status == "PASS"
    assert "ssh nikoli -t ~/.local/bin/nikolai-attach" in nikoli_attach.detail


def test_nikoli_probe_is_explicit_and_redacted() -> None:
    calls = []

    def fake_runner(args, **kwargs):
        calls.append(args)
        if args[:2] == ["ssh", "-G"]:
            return _completed("hostname nikoli-wsl\nuser mdc159\nport 22\nidentityfile /secret/key\n")
        return _completed("NIKOLI_GRID_PROBE_OK\n", returncode=0)

    checks = hermes_grid.collect_checks(
        probe_remote=True,
        runner=fake_runner,
        which=lambda name: f"/usr/bin/{name}" if name in {"ssh", "tmux"} else None,
    )

    nikoli_alias = next(check for check in checks if check.name == "nikoli_ssh_alias")
    nikoli_probe = next(check for check in checks if check.name == "nikoli_remote_probe")

    assert nikoli_alias.status == "PASS"
    assert "hostname=<configured>" in nikoli_alias.detail
    assert "nikoli-wsl" not in nikoli_alias.detail
    assert "/secret/key" not in nikoli_alias.detail
    assert nikoli_probe.status == "PASS"
    assert "tmux/Hermes markers present" in nikoli_probe.detail
    assert any("nikoli" in call for call in calls)


def test_build_attach_command_uses_enabled_tab_command_from_topology() -> None:
    command = hermes_grid.build_attach_command("Victoria")
    assert command == ["ssh", "victoria", "-t", "victoria-attach"]


def test_attach_refuses_disabled_tabs_without_running_command(capsys) -> None:
    calls = []

    def fake_attach_runner(*args, **kwargs):
        calls.append(args)
        return 0

    exit_code = hermes_grid.attach_tab("Android", attach_runner=fake_attach_runner)

    out = capsys.readouterr().out
    assert exit_code == 1
    assert calls == []
    assert "disabled" in out
    assert "Android" in out


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


def test_attach_supports_enabled_nikoli_wsl_attach_mode(capsys) -> None:
    calls = []

    def fake_attach_runner(args):
        calls.append(args)
        return 0

    exit_code = hermes_grid.attach_tab("Nikolai", dry_run=True, attach_runner=fake_attach_runner)

    out = capsys.readouterr().out
    assert exit_code == 0
    assert calls == []
    assert "tab=Nikolai" in out
    assert "kind=wsl-workstation-persona" in out
    assert "attach_mode=ssh-tmux" in out
    assert "ssh nikoli" in out
    assert "nikolai-attach" in out

    exit_code = hermes_grid.attach_tab("Nikolai", attach_runner=fake_attach_runner)

    assert exit_code == 0
    assert calls == [["ssh", "nikoli", "-t", "~/.local/bin/nikolai-attach"]]


def test_roster_prints_donna_hub_and_tab_states(capsys) -> None:
    assert hermes_grid.main(["roster"]) == 0
    out = capsys.readouterr().out
    assert "Studio54 hermes-grid roster" in out
    assert "Hub: Studio54 / Donna" in out
    assert "Donna: role=hub status=operator-control-plane" in out
    assert "Victoria: enabled kind=remote-ssh-tmux" in out
    assert "Nikolai: enabled kind=wsl-workstation-persona" in out
    assert "Android: disabled kind=pending-mobile-edge" in out
    assert "Termux: disabled kind=pending-mobile-edge" in out
    assert "hostname=" not in out


def test_status_prints_sound_off_contract_without_remote_execution(capsys) -> None:
    assert hermes_grid.main(["status"]) == 0
    out = capsys.readouterr().out
    assert "Studio54 hermes-grid status" in out
    assert "Donna hub: READY" in out
    assert "Enabled tabs: Victoria, Nikolai" in out
    assert "Pending tabs: Android, WSL, Termux" in out
    assert "Sound-off contract:" in out
    for field in ["outcome", "confirmed", "changed", "validation", "safety", "next_action"]:
        assert field in out
    assert "remote execution: none" in out
