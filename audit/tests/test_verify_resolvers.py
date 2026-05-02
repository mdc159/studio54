"""Tests for verify.py resolvers."""
from __future__ import annotations

from pathlib import Path

import pytest

from audit.schema import Claim
from audit.verify import resolve_doc


def test_doc_resolver_reads_line(tmp_path: Path) -> None:
    f = tmp_path / "x.md"
    f.write_text("line one\nport 5432 here\nline three\n")
    claim = Claim(
        id="c-1", source_file=str(f), source_line=2, owner="owned",
        claim_type="concrete", subtype="port", claim_text="port 5432 here",
        expected_value=5432, verifiable_by=["doc"],
    )
    out = resolve_doc(claim, repo_root=tmp_path)
    assert "port 5432 here" in out


def test_doc_resolver_handles_missing_file(tmp_path: Path) -> None:
    claim = Claim(
        id="c-1", source_file="missing.md", source_line=1, owner="owned",
        claim_type="concrete", subtype="x", claim_text="t",
        expected_value=1, verifiable_by=["doc"],
    )
    assert resolve_doc(claim, repo_root=tmp_path) is None
