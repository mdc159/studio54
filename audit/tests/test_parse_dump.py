"""Tests for the VPS-raw-text → structured-JSON parser."""
from __future__ import annotations

from pathlib import Path

from audit.parse_dump import parse_raw

SAMPLE_RAW = """===docker_ps===
{"Names":"n8n","State":"running","Status":"Up 4h","Ports":"5678/tcp"}
{"Names":"open-webui","State":"running","Status":"Up 4h","Ports":"8080/tcp"}
===docker_inspect===
[{"Name":"/n8n","Image":"n8nio/n8n"}]
===systemctl_user===
hermes-gateway.service loaded active running
===listening_ports===
LISTEN 0 128 127.0.0.1:5678
LISTEN 0 128 127.0.0.1:8080
===env_files===
FILE:/opt/1215-vps/stack/prototype-local/.env
# comment line
N8N_OWNER_EMAIL=owner@studio54.local
N8N_OWNER_PASSWORD=hunter2
POSTGRES_PORT=5432
ENDFILE:/opt/1215-vps/stack/prototype-local/.env
===bin_1215===
DOCTOR:
OK
SERVICES:
14 services
===file_hashes===
abc123  /opt/1215-vps/stack/prototype-local/.env
===done===
"""


def test_parse_docker_ps() -> None:
    out = parse_raw(SAMPLE_RAW, started_at="t0", finished_at="t1")
    assert len(out["docker_ps"]) == 2
    assert out["docker_ps"][0]["Names"] == "n8n"


def test_parse_env_files_skips_comments() -> None:
    out = parse_raw(SAMPLE_RAW, started_at="t0", finished_at="t1")
    env = out["env_files"]["/opt/1215-vps/stack/prototype-local/.env"]
    assert env["POSTGRES_PORT"] == "5432"
    assert env["N8N_OWNER_PASSWORD"] == "hunter2"
    assert "# comment line" not in env


def test_parse_keeps_raw_sections() -> None:
    out = parse_raw(SAMPLE_RAW, started_at="t0", finished_at="t1")
    assert "hermes-gateway" in out["systemctl_user_raw"]
    assert "5678" in out["listening_ports_raw"]
    assert "DOCTOR:" in out["bin_1215_raw"]
    assert "abc123" in out["file_hashes_raw"]


def test_parse_records_timestamps() -> None:
    out = parse_raw(SAMPLE_RAW, started_at="2026-05-01T12:00:00Z",
                    finished_at="2026-05-01T12:00:30Z")
    assert out["dump_started_at"] == "2026-05-01T12:00:00Z"
    assert out["dump_finished_at"] == "2026-05-01T12:00:30Z"


def test_parse_handles_missing_section() -> None:
    out = parse_raw("===docker_ps===\n", started_at="t0", finished_at="t1")
    assert out["docker_ps"] == []
    assert out["env_files"] == {}


def test_parse_writes_json_file(tmp_path: Path) -> None:
    from audit.parse_dump import parse_file_to_json

    raw_path = tmp_path / "raw.txt"
    raw_path.write_text(SAMPLE_RAW)
    out_path = tmp_path / "dump.json"
    parse_file_to_json(raw_path, out_path, started_at="t0", finished_at="t1")
    import json
    loaded = json.loads(out_path.read_text())
    assert len(loaded["docker_ps"]) == 2
