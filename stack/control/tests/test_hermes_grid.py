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
    assert "hostname=paperclip.tailnet.example" in alias.detail
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
