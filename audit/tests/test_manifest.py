"""Tests for the scope manifest generator."""
from __future__ import annotations

import json
from pathlib import Path

from audit.manifest import build_manifest


def test_classifies_root_as_owned(tmp_repo: Path) -> None:
    m = build_manifest(tmp_repo)
    by_path = {e["path"]: e for e in m["entries"]}
    assert by_path["README.md"]["owner"] == "owned"
    assert by_path["STATE.md"]["owner"] == "owned"


def test_classifies_docs_as_owned(tmp_repo: Path) -> None:
    m = build_manifest(tmp_repo)
    by_path = {e["path"]: e for e in m["entries"]}
    assert by_path["docs/arch.md"]["owner"] == "owned"


def test_classifies_modules_as_upstream(tmp_repo: Path) -> None:
    m = build_manifest(tmp_repo)
    by_path = {e["path"]: e for e in m["entries"]}
    assert by_path["modules/honcho/README.md"]["owner"] == "upstream"


def test_skips_hidden_dirs(tmp_path: Path) -> None:
    (tmp_path / ".audit-local").mkdir()
    (tmp_path / ".audit-local" / "draft.md").write_text("ignore me")
    (tmp_path / "README.md").write_text("# top")
    m = build_manifest(tmp_path)
    paths = [e["path"] for e in m["entries"]]
    assert ".audit-local/draft.md" not in paths
    assert "README.md" in paths


def test_manifest_has_summary(tmp_repo: Path) -> None:
    m = build_manifest(tmp_repo)
    assert m["summary"]["owned"] == 3
    assert m["summary"]["upstream"] == 1
    assert "generated_at" in m


def test_manifest_writes_valid_json(tmp_repo: Path, tmp_path: Path) -> None:
    from audit.manifest import write_manifest

    out = tmp_path / "manifest.json"
    write_manifest(tmp_repo, out)
    loaded = json.loads(out.read_text())
    assert loaded["summary"]["owned"] == 3
