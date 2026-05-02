"""Tests for the report generator."""
from __future__ import annotations

import csv
from pathlib import Path

from audit.report import write_ledger, write_summary
from audit.schema import Claim, ClaimSet


def _claim(**overrides) -> Claim:
    base = dict(
        id="c-1", source_file="STATE.md", source_line=1, owner="owned",
        claim_type="concrete", subtype="port", claim_text="port 5432",
        expected_value=5432, verifiable_by=["code", "vps"],
        doc_says="port 5432", code_says="5432", vps_says="5432",
        status="MATCH", suggested_fix="",
    )
    base.update(overrides)
    return Claim(**base)


def test_ledger_has_all_columns(tmp_path: Path) -> None:
    cs = ClaimSet(claims=[_claim()])
    out = tmp_path / "ledger.csv"
    write_ledger(cs, out)
    rows = list(csv.DictReader(out.open()))
    assert len(rows) == 1
    expected_cols = {
        "id", "source_files", "source_lines", "owner", "claim_type",
        "subtype", "claim_text", "expected_value", "doc_says", "code_says",
        "vps_says", "status", "suggested_fix", "notes",
    }
    assert expected_cols.issubset(rows[0].keys())


def test_ledger_skips_pruned(tmp_path: Path) -> None:
    cs = ClaimSet(claims=[_claim(), _claim(id="c-2", status="pruned")])
    out = tmp_path / "ledger.csv"
    write_ledger(cs, out)
    rows = list(csv.DictReader(out.open()))
    assert len(rows) == 1
    assert rows[0]["id"] == "c-1"


def test_summary_lists_top_drifts(tmp_path: Path) -> None:
    cs = ClaimSet(claims=[
        _claim(),
        _claim(id="c-2", status="DRIFT", expected_value=14,
               doc_says="14 containers", vps_says="13 running",
               suggested_fix="update STATE.md to 13"),
        _claim(id="c-3", status="DRIFT_DOC_STALE", expected_value="ORC"),
    ])
    out = tmp_path / "summary.md"
    write_summary(cs, out)
    text = out.read_text()
    assert "Headline" in text or "MATCH" in text
    assert "DRIFT" in text
    assert "STATE.md" in text
