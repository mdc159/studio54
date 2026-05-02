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


from audit.verify import resolve_code


def test_code_resolver_finds_port(tmp_path: Path) -> None:
    (tmp_path / "compose.yml").write_text("services:\n  db:\n    ports: ['5432:5432']\n")
    claim = Claim(
        id="c-2", source_file="x.md", source_line=1, owner="owned",
        claim_type="concrete", subtype="port", claim_text="DB on 5432",
        expected_value=5432, verifiable_by=["code"],
    )
    out = resolve_code(claim, repo_root=tmp_path)
    assert out is not None
    assert "5432" in out


def test_code_resolver_finds_path(tmp_path: Path) -> None:
    (tmp_path / "stack").mkdir()
    (tmp_path / "stack" / "real.env").write_text("X=1\n")
    claim = Claim(
        id="c-3", source_file="x.md", source_line=1, owner="owned",
        claim_type="concrete", subtype="path", claim_text="stack/real.env exists",
        expected_value="stack/real.env", verifiable_by=["code"],
    )
    out = resolve_code(claim, repo_root=tmp_path)
    assert "exists" in out.lower()


def test_code_resolver_returns_none_for_unsupported_subtype() -> None:
    claim = Claim(
        id="c-4", source_file="x.md", source_line=1, owner="owned",
        claim_type="behavioral", subtype="weird", claim_text="...",
        expected_value=None, verifiable_by=["code"],
    )
    assert resolve_code(claim, repo_root=Path("/nonexistent")) is None


def test_code_resolver_runs_probe_when_provided(tmp_path: Path) -> None:
    claim = Claim(
        id="c-5", source_file="x.md", source_line=1, owner="owned",
        claim_type="behavioral", subtype="probe", claim_text="echo says hi",
        expected_value="hi", verifiable_by=["code"], probe="echo hi",
    )
    out = resolve_code(claim, repo_root=tmp_path)
    assert out is not None
    assert "hi" in out
