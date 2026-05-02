"""Tests for the secret redactor."""
from __future__ import annotations

import json
from pathlib import Path

from audit.redact import redact_dump, redact_value


def test_regex_redacts_keylike_names() -> None:
    assert redact_value("API_KEY", "sk-abc", denylist=set()).startswith("<REDACTED:")
    assert redact_value("SOMETHING_SECRET", "x", denylist=set()).startswith("<REDACTED:")
    assert redact_value("DB_PASSWORD", "x", denylist=set()).startswith("<REDACTED:")
    assert redact_value("ACCESS_TOKEN", "x", denylist=set()).startswith("<REDACTED:")


def test_denylist_redacts_named_fields() -> None:
    assert redact_value("N8N_OWNER_EMAIL", "x", denylist={"N8N_OWNER_EMAIL"}).startswith(
        "<REDACTED:"
    )


def test_keeps_non_secret_values() -> None:
    assert redact_value("POSTGRES_PORT", "5432", denylist=set()) == "5432"


def test_redact_dump_walks_env_files(sample_dump_dict: dict) -> None:
    out = redact_dump(sample_dump_dict, denylist={"N8N_OWNER_EMAIL"})
    env = out["env_files"]["stack/prototype-local/.env"]
    assert env["POSTGRES_PORT"] == "5432"
    assert env["N8N_OWNER_PASSWORD"].startswith("<REDACTED:")
    assert env["N8N_OWNER_EMAIL"].startswith("<REDACTED:")


def test_redacted_dump_contains_no_known_secret(sample_dump_dict: dict) -> None:
    out = redact_dump(sample_dump_dict, denylist={"N8N_OWNER_EMAIL"})
    blob = json.dumps(out)
    assert "hunter2-real-secret" not in blob
