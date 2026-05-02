"""Tests for the extractor driver: parsing and merging."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from audit.extract import (
    assign_ids,
    merge_claims,
    parse_subagent_output,
)


def test_parse_valid_yaml() -> None:
    raw = """claims:
  - source_line: 5
    claim_type: concrete
    subtype: port
    claim_text: "DB port 5432"
    expected_value: 5432
    verifiable_by: [vps]
"""
    parsed = parse_subagent_output(raw, source_file="STATE.md", owner="owned")
    assert len(parsed) == 1
    assert parsed[0]["source_file"] == "STATE.md"
    assert parsed[0]["owner"] == "owned"
    assert parsed[0]["expected_value"] == 5432


def test_parse_strips_code_fences() -> None:
    raw = "```yaml\nclaims: []\n```\n"
    parsed = parse_subagent_output(raw, source_file="x.md", owner="owned")
    assert parsed == []


def test_parse_invalid_yaml_returns_empty_with_warning(capsys) -> None:
    parsed = parse_subagent_output(
        "not yaml :\n  - definitely [not", source_file="x.md", owner="owned"
    )
    assert parsed == []
    assert "WARN" in capsys.readouterr().err


def test_merge_dedupes_by_text_and_value() -> None:
    a = {"source_file": "A.md", "source_line": 1, "claim_text": "X",
         "expected_value": 1, "claim_type": "concrete", "subtype": "n",
         "owner": "owned", "verifiable_by": ["doc"]}
    b = {"source_file": "B.md", "source_line": 2, "claim_text": "X",
         "expected_value": 1, "claim_type": "concrete", "subtype": "n",
         "owner": "owned", "verifiable_by": ["doc"]}
    merged = merge_claims([a, b])
    assert len(merged) == 1
    assert merged[0]["source_file"] == "A.md"
    assert "B.md" in merged[0]["seen_in"]


def test_assign_ids_is_stable_and_unique() -> None:
    claims = [
        {"claim_text": "A", "expected_value": 1},
        {"claim_text": "B", "expected_value": 2},
    ]
    assign_ids(claims)
    assert claims[0]["id"] == "c-0001"
    assert claims[1]["id"] == "c-0002"
