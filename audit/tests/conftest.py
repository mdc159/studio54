"""Shared pytest fixtures for the audit pipeline tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_claim_dict() -> dict:
    return {
        "id": "c-0001",
        "source_file": "STATE.md",
        "source_line": 5,
        "owner": "owned",
        "claim_type": "concrete",
        "subtype": "container_count",
        "claim_text": "14 containers running, all healthy",
        "expected_value": 14,
        "verifiable_by": ["vps"],
    }


@pytest.fixture
def sample_dump_dict() -> dict:
    return {
        "dump_started_at": "2026-05-01T12:00:00Z",
        "dump_finished_at": "2026-05-01T12:00:42Z",
        "docker_ps": [
            {"Names": "n8n", "State": "running", "Status": "Up 4 hours"},
            {"Names": "open-webui", "State": "running", "Status": "Up 4 hours"},
        ],
        "ports": [{"port": 5678, "addr": "127.0.0.1"}],
        "env_files": {
            "stack/prototype-local/.env": {
                "N8N_OWNER_EMAIL": "owner@studio54.local",
                "N8N_OWNER_PASSWORD": "hunter2-real-secret",
                "POSTGRES_PORT": "5432",
            }
        },
        "bin_1215": {"doctor": "OK", "services": "14 services"},
    }


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """A small fake repo tree for manifest/extract tests."""
    (tmp_path / "README.md").write_text("# Top-level\nport 5432 is the DB.\n")
    (tmp_path / "STATE.md").write_text("- 14 containers running\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "arch.md").write_text("Hermes is tier-0.\n")
    (tmp_path / "modules" / "honcho").mkdir(parents=True)
    (tmp_path / "modules" / "honcho" / "README.md").write_text("Upstream.\n")
    (tmp_path / "modules" / "honcho" / "internal").mkdir()
    (tmp_path / "modules" / "honcho" / "internal" / "details.md").write_text("deep")
    return tmp_path
