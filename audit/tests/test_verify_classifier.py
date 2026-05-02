"""Tests for the MATCH/DRIFT/UNVERIFIABLE classifier."""
from __future__ import annotations

from audit.verify import classify


def test_match_when_all_three_agree() -> None:
    s, fix = classify("port 5432", "5432 in compose", "5432 listening", expected="5432")
    assert s == "MATCH"


def test_drift_when_doc_disagrees() -> None:
    s, fix = classify("port 5432", "5432 in compose", "port 5433 not seen", expected="5433")
    assert s == "DRIFT"
    assert "fix" in fix.lower() or "update" in fix.lower() or "reconcile" in fix.lower()


def test_unverifiable_when_only_one_resolver() -> None:
    s, fix = classify("rationale", None, None, expected="phil")
    assert s == "UNVERIFIABLE"


def test_doc_stale_when_code_and_vps_agree_doc_disagrees() -> None:
    s, fix = classify(
        "STATE.md says 14 containers",   # doc sees old value 14
        "compose declares 13 services",  # code sees new value 13
        "13 containers running",         # vps sees new value 13
        expected=13,                     # truth is 13 (code/vps agree)
    )
    assert s == "DRIFT_DOC_STALE"
