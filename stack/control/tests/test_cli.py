from __future__ import annotations

import json
from types import SimpleNamespace

from control1215 import cli


def test_targets_command_lists_known_targets(capsys) -> None:
    assert cli.main(["targets"]) == 0
    out = capsys.readouterr().out
    assert "prototype-local" in out
    assert "vps-hub" in out


def test_docs_command_lists_architecture_pack(capsys) -> None:
    assert cli.main(["docs"]) == 0
    out = capsys.readouterr().out
    assert "docs/architecture/overview.md" in out
    assert "docs/architecture/execution-plan.md" in out


def test_nodes_command_lists_manifest_examples(capsys) -> None:
    assert cli.main(["nodes"]) == 0
    out = capsys.readouterr().out
    assert "linux-prototype: target=prototype-local" in out


def test_services_command_for_prototype_target(capsys) -> None:
    assert cli.main(["services", "--target", "prototype-local"]) == 0
    out = capsys.readouterr().out
    assert "open-webui" in out
    assert "broker" in out
    assert "n8n-mcp" in out
    assert "comfyui" in out


def test_show_target_command(capsys) -> None:
    assert cli.main(["show-target", "vps-hub"]) == 0
    out = capsys.readouterr().out
    assert '"name": "vps-hub"' in out
    assert '"ingress": "cloudflare+tunnel+tailnet"' in out


def test_show_node_command(capsys) -> None:
    assert cli.main(["show-node", "linux-prototype"]) == 0
    out = capsys.readouterr().out
    assert '"name": "linux-prototype"' in out
    assert '"target": "prototype-local"' in out
    assert '"compose_profiles": [' in out
    assert '"role_compose_files": [' in out
    assert '"media"' in out
    assert '"tools"' in out
    assert '"stack/roles/media-cpu/docker-compose.role.yml"' in out
    assert '"stack/roles/tools/docker-compose.role.yml"' in out


def test_compose_cmd_for_node_includes_env_file_and_profiles(capsys) -> None:
    assert cli.main(["compose-cmd", "linux-prototype", "config"]) == 0
    out = capsys.readouterr().out
    assert "--env-file" in out
    assert "stack/prototype-local/.env" in out
    assert "stack/roles/media-cpu/docker-compose.role.yml" in out
    assert "stack/roles/tools/docker-compose.role.yml" in out
    assert "--profile media" in out
    assert "--profile tools" in out
    assert "stack/prototype-local/docker-compose.substrate.yml" in out
    assert out.rstrip().endswith("config")


def test_broker_files_command(capsys) -> None:
    assert cli.main(["broker-files"]) == 0
    out = capsys.readouterr().out
    assert "stack/sql/broker/001_core.sql" in out


def test_broker_ddl_command(capsys) -> None:
    assert cli.main(["broker-ddl"]) == 0
    out = capsys.readouterr().out
    assert "CREATE SCHEMA IF NOT EXISTS broker;" in out
    assert "CREATE TABLE IF NOT EXISTS broker.events" in out


def test_proof_node_json_collects_and_verifies(monkeypatch, tmp_path, capsys) -> None:
    proof_path = tmp_path / "proof.json"
    proof_path.write_text("{}")
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):  # noqa: ANN001, ANN202
        calls.append([str(part) for part in cmd])
        if str(cmd[1]).endswith("collect-node-proof.py"):
            return SimpleNamespace(returncode=0, stdout=f"{proof_path}\n", stderr="")
        if str(cmd[1]).endswith("verify-node-proof.py"):
            payload = {
                "schema": "studio54.node-proof-verification.v1",
                "status": "PASS",
                "errors": [],
            }
            return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert cli.main(["proof", "node", "--json", "--output-dir", str(tmp_path)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["schema"] == "studio54.proof-node-command.v1"
    assert out["status"] == "PASS"
    assert out["proofPath"] == str(proof_path)
    assert any("collect-node-proof.py" in part for part in calls[0])
    assert any("verify-node-proof.py" in part for part in calls[1])


def test_proof_node_json_fails_when_collector_omits_path(monkeypatch, capsys) -> None:
    def fake_run(cmd, **kwargs):  # noqa: ANN001, ANN202
        if str(cmd[1]).endswith("collect-node-proof.py"):
            return SimpleNamespace(returncode=1, stdout="", stderr="failed\n")
        raise AssertionError(f"unexpected command: {cmd}")

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert cli.main(["proof", "node", "--json"]) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "FAIL"
    assert out["collector"]["returncode"] == 1
    assert out["verification"]["errors"] == ["collector did not report a proof path"]


def test_company_bootstrap_wraps_template_script(monkeypatch, tmp_path) -> None:
    template = tmp_path / "company.json"
    template.write_text("{}")
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):  # noqa: ANN001, ANN202
        calls.append([str(part) for part in cmd])
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    assert cli.main(
        [
            "company",
            "bootstrap",
            "--template-file",
            str(template),
            "--base-url",
            "http://paperclip.test",
        ]
    ) == 0
    command = calls[0]
    assert command[1].endswith("bootstrap_paperclip_hermes_company.py")
    assert command[2:4] == ["--template-file", str(template)]
    assert command[-2:] == ["--base-url", "http://paperclip.test"]
