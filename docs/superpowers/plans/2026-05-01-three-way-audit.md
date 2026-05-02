# Three-Way Repo Audit — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable, claim-driven, three-way audit pipeline (docs vs codebase vs live VPS) and run it once against Studio54 to produce a committed `ledger.csv` + `summary.md` + redacted VPS dump under `docs/audits/2026-05-01-three-way/`.

**Architecture:** Two-stage pipeline. Stage 1 fans out one subagent per `.md` file to extract concrete and behavioral claims into a draft YAML ledger; the human reviews and curates. Stage 2 captures a single VPS dump, runs three resolvers (doc, code, vps) per curated claim, classifies each row (`MATCH | DRIFT | UNVERIFIABLE`), and produces a CSV ledger plus a thin Markdown summary. Tooling lives in `audit/`; per-run artifacts under `docs/audits/<date>-<slug>/`; sensitive intermediates under gitignored `.audit-local/`.

**Tech Stack:** Python 3.11+ via UV single-file scripts (PEP 723 inline deps), `pytest` for unit tests, `pyyaml` for the claims schema, `claude --print` (subprocess) for subagent fan-out, plain `bash` + `ssh Studio54` for the VPS dump, `csv` stdlib for the ledger.

**Spec:** [`docs/superpowers/specs/2026-05-01-three-way-audit-design.md`](../specs/2026-05-01-three-way-audit-design.md)

---

## File Structure

```
audit/                                 # tooling (committed)
├── __init__.py                        # marker; empty
├── schema.py                          # Claim dataclass + YAML load/dump + validation
├── manifest.py                        # walk repo, classify owned/upstream, write scope.manifest.json
├── extract.py                         # subagent fan-out driver (calls `claude --print`)
├── extract_prompt.md                  # the per-file extractor system prompt
├── dump_vps.sh                        # SSH capture only (writes raw text → temp file)
├── parse_dump.py                      # parse raw section-marked text into structured JSON
├── redact.py                          # full → redacted JSON (regex + denylist)
├── redaction_denylist.txt             # hand-curated sensitive field names
├── verify.py                          # 3 resolvers + classifier
├── report.py                          # ledger.csv + summary.md generator
├── README.md                          # how to run the audit, end-to-end
└── tests/
    ├── __init__.py
    ├── conftest.py                    # shared fixtures (sample claim, sample dump)
    ├── test_schema.py
    ├── test_manifest.py
    ├── test_extract.py
    ├── test_parse_dump.py
    ├── test_redact.py
    ├── test_verify_resolvers.py
    ├── test_verify_classifier.py
    └── test_report.py

docs/audits/2026-05-01-three-way/      # per-run artifacts (committed)
├── README.md                          # short index for this run
├── scope.manifest.json                # written by manifest.py
├── claims.curated.yaml                # human-reviewed input to verifier
├── ledger.csv                         # written by report.py
├── summary.md                         # written by report.py
└── vps-dump.redacted.json             # written by redact.py

.audit-local/                          # gitignored (full secrets stay here)
├── claims.draft.yaml                  # written by extract.py
└── vps-dump.full.json                 # written by dump_vps.sh
```

**File responsibilities (one purpose each):**
- `schema.py` is the single source of truth for the claim record shape; every other module imports it.
- `manifest.py` only does the filesystem walk; it does not extract claims.
- `extract.py` only orchestrates subagent calls and merges YAML; it never *interprets* claims.
- `dump_vps.sh` only does the SSH capture; parsing lives in `parse_dump.py`; redaction is a separate pass in `redact.py`.
- `redact.py` is the only module that reads the full dump and writes the redacted dump.
- `verify.py` only resolves and classifies; it never writes output files.
- `report.py` only formats; it never resolves.

This separation means each file fits in head, each is independently testable, and a future re-run can swap any one component (e.g., a new `dump_vps.sh` for a different VPS) without touching the others.

---

## Phase 0: Scaffolding

### Task 0.1: Create directories, gitignore, audit README

**Files:**
- Create: `audit/__init__.py`
- Create: `audit/tests/__init__.py`
- Create: `audit/tests/conftest.py`
- Create: `audit/README.md`
- Modify: `.gitignore`
- Create: `docs/audits/2026-05-01-three-way/README.md`

- [ ] **Step 1: Create empty package markers**

```bash
mkdir -p audit/tests docs/audits/2026-05-01-three-way
touch audit/__init__.py audit/tests/__init__.py
```

- [ ] **Step 2: Add `.audit-local/` to .gitignore**

Append to `.gitignore`:

```
# Three-way audit (full dumps and draft claims contain secrets)
.audit-local/
```

- [ ] **Step 3: Write `audit/README.md`**

```markdown
# audit/ — Three-way repo audit pipeline

Compares what the docs say about Studio54 against what the codebase says
against what the live VPS at 148.230.95.154 actually does. Spec:
`docs/superpowers/specs/2026-05-01-three-way-audit-design.md`.

## End-to-end run

    # 1. Manifest — list every .md file with owner tag
    uv run audit/manifest.py docs/audits/2026-05-01-three-way/scope.manifest.json

    # 2. Extract — fan out subagents, write draft claims to .audit-local/
    uv run audit/extract.py \
        --manifest docs/audits/2026-05-01-three-way/scope.manifest.json \
        --out .audit-local/claims.draft.yaml

    # 3. REVIEW GATE — human curates the draft, saves as:
    #    docs/audits/2026-05-01-three-way/claims.curated.yaml

    # 4. Dump — single SSH session captures full VPS state
    bash audit/dump_vps.sh .audit-local/vps-dump.full.json

    # 5. Redact — produce committable copy
    uv run audit/redact.py \
        --in .audit-local/vps-dump.full.json \
        --out docs/audits/2026-05-01-three-way/vps-dump.redacted.json

    # 6. Verify + report — produce ledger.csv and summary.md
    uv run audit/verify.py \
        --claims docs/audits/2026-05-01-three-way/claims.curated.yaml \
        --dump .audit-local/vps-dump.full.json \
        --out .audit-local/claims.verified.yaml
    uv run audit/report.py \
        --verified .audit-local/claims.verified.yaml \
        --out-dir docs/audits/2026-05-01-three-way/

## Tests

    uv run pytest audit/tests/
```

- [ ] **Step 4: Write `docs/audits/2026-05-01-three-way/README.md`**

```markdown
# Three-way audit — 2026-05-01

One-time reality check comparing Studio54 docs, codebase, and the live VPS
at 148.230.95.154. Tooling lives in `/audit/`; design lives in
`/docs/superpowers/specs/2026-05-01-three-way-audit-design.md`.

Files in this directory:

- `scope.manifest.json` — every .md scanned, with owner tag
- `claims.curated.yaml` — claims after human review
- `ledger.csv` — final audit ledger, one row per claim
- `summary.md` — executive summary, top drifts, fix list
- `vps-dump.redacted.json` — frozen VPS snapshot (secrets redacted)

Read `summary.md` first.
```

- [ ] **Step 5: Write `audit/tests/conftest.py` — shared fixtures**

```python
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
        "probe": None,
        "seen_in": [],
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
    return tmp_path
```

- [ ] **Step 6: Commit**

```bash
git add audit/ docs/audits/ .gitignore
git commit -m "audit: scaffold pipeline directories, gitignore, READMEs"
```

---

## Phase 1: Claim schema (TDD)

### Task 1.1: Define and validate the Claim schema

**Files:**
- Create: `audit/schema.py`
- Create: `audit/tests/test_schema.py`

- [ ] **Step 1: Write the failing tests**

`audit/tests/test_schema.py`:

```python
"""Tests for the Claim schema and YAML round-trip."""
from __future__ import annotations

import pytest
import yaml

from audit.schema import Claim, ClaimSet, dump_claims, load_claims


def test_claim_from_dict_roundtrip(sample_claim_dict: dict) -> None:
    claim = Claim.from_dict(sample_claim_dict)
    assert claim.id == "c-0001"
    assert claim.owner == "owned"
    assert claim.expected_value == 14
    assert claim.verifiable_by == ["vps"]
    assert claim.to_dict() == sample_claim_dict


def test_claim_rejects_unknown_owner(sample_claim_dict: dict) -> None:
    bad = dict(sample_claim_dict, owner="bogus")
    with pytest.raises(ValueError, match="owner"):
        Claim.from_dict(bad)


def test_claim_rejects_unknown_type(sample_claim_dict: dict) -> None:
    bad = dict(sample_claim_dict, claim_type="philosophical")
    with pytest.raises(ValueError, match="claim_type"):
        Claim.from_dict(bad)


def test_claim_rejects_bad_verifiable_by(sample_claim_dict: dict) -> None:
    bad = dict(sample_claim_dict, verifiable_by=["smoke"])
    with pytest.raises(ValueError, match="verifiable_by"):
        Claim.from_dict(bad)


def test_load_dump_yaml_roundtrip(tmp_path, sample_claim_dict: dict) -> None:
    path = tmp_path / "claims.yaml"
    dump_claims(ClaimSet(claims=[Claim.from_dict(sample_claim_dict)]), path)
    loaded = load_claims(path)
    assert len(loaded.claims) == 1
    assert loaded.claims[0].id == "c-0001"


def test_load_rejects_duplicate_ids(tmp_path) -> None:
    bad = [
        {**dict(id="c-1", source_file="a.md", source_line=1, owner="owned",
                claim_type="concrete", subtype="x", claim_text="t",
                expected_value=1, verifiable_by=["doc"])},
        {**dict(id="c-1", source_file="b.md", source_line=2, owner="owned",
                claim_type="concrete", subtype="x", claim_text="t2",
                expected_value=2, verifiable_by=["doc"])},
    ]
    p = tmp_path / "dup.yaml"
    p.write_text(yaml.safe_dump({"claims": bad}))
    with pytest.raises(ValueError, match="duplicate"):
        load_claims(p)
```

- [ ] **Step 2: Run tests, confirm they fail**

```bash
cd /home/mdc159/projects/company/studio54
uv run --with pyyaml --with pytest pytest audit/tests/test_schema.py -v
```
Expected: FAIL with `ImportError: No module named 'audit.schema'` (or similar).

- [ ] **Step 3: Implement `audit/schema.py`**

```python
"""Claim schema, YAML load/dump, validation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

VALID_OWNERS = ("owned", "upstream")
VALID_CLAIM_TYPES = ("concrete", "behavioral")
VALID_VERIFIERS = ("doc", "code", "vps")
VALID_STATUSES = (
    "MATCH",
    "DRIFT",
    "DRIFT_DOC_STALE",
    "UNVERIFIABLE",
    "UNVERIFIABLE_AGAINST_CODE",
    "pruned",
)


@dataclass
class Claim:
    id: str
    source_file: str
    source_line: int
    owner: str
    claim_type: str
    subtype: str
    claim_text: str
    expected_value: Any
    verifiable_by: list[str]
    probe: str | None = None
    seen_in: list[str] = field(default_factory=list)
    status: str | None = None
    doc_says: str | None = None
    code_says: str | None = None
    vps_says: str | None = None
    suggested_fix: str | None = None
    notes: str | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "Claim":
        if d.get("owner") not in VALID_OWNERS:
            raise ValueError(f"invalid owner: {d.get('owner')!r}")
        if d.get("claim_type") not in VALID_CLAIM_TYPES:
            raise ValueError(f"invalid claim_type: {d.get('claim_type')!r}")
        vb = d.get("verifiable_by", [])
        if not vb or any(v not in VALID_VERIFIERS for v in vb):
            raise ValueError(f"invalid verifiable_by: {vb!r}")
        if d.get("status") is not None and d["status"] not in VALID_STATUSES:
            raise ValueError(f"invalid status: {d['status']!r}")
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__ if k in d})

    def to_dict(self) -> dict:
        out = asdict(self)
        # Drop fields that are None or empty list to keep YAML tidy
        for k in list(out):
            if out[k] is None or out[k] == []:
                if k not in ("expected_value",):  # keep explicit None for clarity
                    out.pop(k)
        return out


@dataclass
class ClaimSet:
    claims: list[Claim]


def load_claims(path: Path | str) -> ClaimSet:
    raw = yaml.safe_load(Path(path).read_text())
    claims = [Claim.from_dict(c) for c in (raw or {}).get("claims", [])]
    seen: set[str] = set()
    for c in claims:
        if c.id in seen:
            raise ValueError(f"duplicate claim id: {c.id}")
        seen.add(c.id)
    return ClaimSet(claims=claims)


def dump_claims(cs: ClaimSet, path: Path | str) -> None:
    Path(path).write_text(
        yaml.safe_dump(
            {"claims": [c.to_dict() for c in cs.claims]},
            sort_keys=False,
        )
    )
```

- [ ] **Step 4: Run tests, confirm they pass**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_schema.py -v
```
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add audit/schema.py audit/tests/test_schema.py audit/tests/conftest.py
git commit -m "audit: add Claim schema with YAML round-trip and validation"
```

---

## Phase 2: Scope manifest (TDD)

### Task 2.1: Walk repo, classify owned/upstream

**Files:**
- Create: `audit/manifest.py`
- Create: `audit/tests/test_manifest.py`

- [ ] **Step 1: Write the failing tests**

`audit/tests/test_manifest.py`:

```python
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
```

- [ ] **Step 2: Run tests, confirm they fail**

```bash
uv run --with pytest pytest audit/tests/test_manifest.py -v
```
Expected: FAIL with `ImportError: No module named 'audit.manifest'`.

- [ ] **Step 3: Implement `audit/manifest.py`**

```python
"""Walk a repo, list every .md, classify each as owned or upstream."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

OWNED_PREFIXES = ("docs/", "deploy/")
OWNED_ROOT_FILES = {"README.md", "STATE.md", "AGENTS.md", "CLAUDE.md"}
UPSTREAM_PREFIXES = ("modules/",)


def classify(rel_path: str) -> str:
    if rel_path in OWNED_ROOT_FILES:
        return "owned"
    if any(rel_path.startswith(p) for p in OWNED_PREFIXES):
        return "owned"
    if any(rel_path.startswith(p) for p in UPSTREAM_PREFIXES):
        return "upstream"
    return "owned"  # any other top-level .md is treated as owned


def build_manifest(root: Path) -> dict:
    entries: list[dict] = []
    for path in sorted(root.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        rel = str(path.relative_to(root))
        entries.append(
            {
                "path": rel,
                "owner": classify(rel),
                "size_bytes": path.stat().st_size,
            }
        )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "summary": {
            "owned": sum(1 for e in entries if e["owner"] == "owned"),
            "upstream": sum(1 for e in entries if e["owner"] == "upstream"),
            "total": len(entries),
        },
        "entries": entries,
    }


def write_manifest(root: Path, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(build_manifest(root), indent=2))


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: manifest.py <out.json>", file=sys.stderr)
        return 2
    write_manifest(Path.cwd(), Path(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests, confirm they pass**

```bash
uv run --with pytest pytest audit/tests/test_manifest.py -v
```
Expected: PASS (6 tests).

- [ ] **Step 5: Generate the real manifest**

```bash
uv run audit/manifest.py docs/audits/2026-05-01-three-way/scope.manifest.json
head -40 docs/audits/2026-05-01-three-way/scope.manifest.json
```
Expected: valid JSON, summary shows owned/upstream counts. Eyeball that the counts make sense (>20 owned, several upstream).

- [ ] **Step 6: Commit**

```bash
git add audit/manifest.py audit/tests/test_manifest.py docs/audits/2026-05-01-three-way/scope.manifest.json
git commit -m "audit: scope manifest generator with owned/upstream classifier"
```

---

## Phase 3: Extractor

### Task 3.1: Write the extractor system prompt

**Files:**
- Create: `audit/extract_prompt.md`

- [ ] **Step 1: Write `audit/extract_prompt.md`**

```markdown
You are extracting verifiable claims from a markdown document. Your output
will be merged into a structured ledger and verified against the codebase
and a live system. Precision matters more than recall — a missed claim is
fine, a hallucinated claim wastes the human reviewer's time.

## What is a claim

Emit one entry for each:

1. **Concrete fact:** a string, number, ID, path, port, container name,
   service name, version, command name, env var name, or file existence
   assertion.
2. **Behavioral assertion:** a testable statement of the form "X causes Y"
   or "running command Z produces output W" or "service P depends on Q".

## What is NOT a claim

Skip:
- Philosophy, motivation, rationale ("we believe in...", "the goal is...")
- Anything you'd have to infer from context
- Aspirational or future-tense statements ("will eventually...", "should...")
- Architectural-role statements ("Hermes is the tier-0 agent")

## Output format

Emit a YAML document. One entry per claim. No prose, no markdown, just YAML.

    claims:
      - source_line: 12          # 1-indexed line in the input
        claim_type: concrete     # concrete | behavioral
        subtype: port            # short tag: port, path, env_var, container_name, etc.
        claim_text: "Postgres listens on port 5432"
        expected_value: 5432
        verifiable_by: [code, vps]
        probe: null              # optional shell command for behavioral claims

If the document has no extractable claims, emit:

    claims: []

## Rules

- `source_line` must match the actual line in the input, 1-indexed.
- `expected_value` is the smallest concrete value the claim asserts (a
  number, string, bool, or short list). For behavioral claims, set it to
  the assertion's predicate (e.g., "auto-creates owner on first boot").
- `verifiable_by` lists which sources COULD verify this — `doc` (the doc
  itself), `code` (the repo), `vps` (the running system). Use your
  judgment; the human reviewer will fix mistakes.
- For `probe` on behavioral claims: only fill it in if you can write a
  short, safe, non-destructive shell command that would reveal the answer.
  Otherwise leave as null.
- Do NOT emit `id`, `owner`, `source_file`, or `seen_in` — the driver
  fills those in.
```

- [ ] **Step 2: Commit**

```bash
git add audit/extract_prompt.md
git commit -m "audit: extractor system prompt"
```

### Task 3.2: Implement the extractor driver with a unit test

**Files:**
- Create: `audit/extract.py`
- Create: `audit/tests/test_extract.py`

- [ ] **Step 1: Write the failing tests**

The driver does three things: (a) call the subagent for each file, (b) parse the YAML it returns, (c) merge into a single ledger with deduped claims. We unit-test (b) and (c) and stub (a) so tests do not call the real `claude` CLI.

`audit/tests/test_extract.py`:

```python
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
```

- [ ] **Step 2: Run tests, confirm they fail**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_extract.py -v
```
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `audit/extract.py`**

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Fan out one `claude --print` subagent per .md file; merge YAML claims."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import yaml

PROMPT_PATH = Path(__file__).parent / "extract_prompt.md"
DEFAULT_CONCURRENCY = 10


def parse_subagent_output(raw: str, source_file: str, owner: str) -> list[dict]:
    """Strip code fences, parse YAML, decorate with source_file + owner."""
    stripped = re.sub(r"^```(?:yaml)?\n|```\n?$", "", raw.strip(), flags=re.MULTILINE)
    try:
        doc = yaml.safe_load(stripped) or {}
    except yaml.YAMLError as e:
        print(f"WARN: failed to parse YAML for {source_file}: {e}", file=sys.stderr)
        return []
    items = doc.get("claims", []) or []
    out: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item["source_file"] = source_file
        item["owner"] = owner
        out.append(item)
    return out


def merge_claims(all_claims: list[dict]) -> list[dict]:
    """Dedupe by (claim_text, expected_value); track every source in seen_in."""
    by_key: dict[tuple, dict] = {}
    for c in all_claims:
        key = (c.get("claim_text"), repr(c.get("expected_value")))
        if key in by_key:
            existing = by_key[key]
            sf = c.get("source_file")
            if sf and sf != existing.get("source_file"):
                existing.setdefault("seen_in", []).append(sf)
        else:
            by_key[key] = dict(c)
            by_key[key].setdefault("seen_in", [])
    return list(by_key.values())


def assign_ids(claims: list[dict]) -> None:
    """In-place: assign c-0001, c-0002, ... in current order."""
    for i, c in enumerate(claims, start=1):
        c["id"] = f"c-{i:04d}"


def run_subagent(file_path: Path, owner: str, prompt: str) -> list[dict]:
    """Invoke `claude --print` on the file content; return parsed claim dicts."""
    content = file_path.read_text(errors="replace")
    user_input = f"# Document: {file_path}\n\n{content}"
    result = subprocess.run(
        [
            "claude",
            "--print",
            "--append-system-prompt", prompt,
            "--allowedTools", "",  # no tools needed
            user_input,
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if result.returncode != 0:
        print(f"WARN: claude failed for {file_path}: {result.stderr[:500]}",
              file=sys.stderr)
        return []
    return parse_subagent_output(result.stdout, str(file_path), owner)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY)
    ap.add_argument("--limit", type=int, default=None,
                    help="Process only the first N files (smoke testing).")
    args = ap.parse_args()

    prompt = PROMPT_PATH.read_text()
    manifest = json.loads(args.manifest.read_text())
    entries = manifest["entries"]
    if args.limit:
        entries = entries[: args.limit]

    all_claims: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {
            ex.submit(run_subagent, Path(manifest["root"]) / e["path"],
                      e["owner"], prompt): e["path"]
            for e in entries
        }
        for fut in as_completed(futures):
            path = futures[fut]
            try:
                all_claims.extend(fut.result())
                print(f"OK   {path}", file=sys.stderr)
            except Exception as e:  # noqa: BLE001
                print(f"FAIL {path}: {e}", file=sys.stderr)

    merged = merge_claims(all_claims)
    assign_ids(merged)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(yaml.safe_dump({"claims": merged}, sort_keys=False))
    print(f"\nWrote {len(merged)} unique claims to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests, confirm they pass**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_extract.py -v
```
Expected: PASS (5 tests).

- [ ] **Step 5: Smoke test against a single file**

```bash
uv run audit/extract.py \
    --manifest docs/audits/2026-05-01-three-way/scope.manifest.json \
    --out /tmp/claims.smoke.yaml \
    --limit 1
head -40 /tmp/claims.smoke.yaml
```
Expected: a YAML file with `claims:` and at least one entry derived from the first file in the manifest. If the file errors, debug the `claude --print` invocation first.

- [ ] **Step 6: Commit**

```bash
git add audit/extract.py audit/tests/test_extract.py
git commit -m "audit: extractor driver with subagent fan-out and dedupe"
```

### Task 3.3: Run the full extraction

**Files:**
- Write: `.audit-local/claims.draft.yaml`

- [ ] **Step 1: Confirm `.audit-local/` exists and is gitignored**

```bash
mkdir -p .audit-local
git check-ignore .audit-local/test.yaml
```
Expected: `.audit-local/test.yaml` (proving it is ignored).

- [ ] **Step 2: Run extraction across the whole manifest**

```bash
uv run audit/extract.py \
    --manifest docs/audits/2026-05-01-three-way/scope.manifest.json \
    --out .audit-local/claims.draft.yaml \
    --concurrency 10 \
    2> .audit-local/extract.log
wc -l .audit-local/claims.draft.yaml
tail -20 .audit-local/extract.log
```
Expected: hundreds of lines in `claims.draft.yaml`; the log ends with `Wrote N unique claims`.

- [ ] **Step 3: No commit (draft is local-only)**

The draft is gitignored. Move on to the review gate.

---

## Phase 4: Review gate (manual)

### Task 4.1: Curate the draft into `claims.curated.yaml`

**Files:**
- Read: `.audit-local/claims.draft.yaml`
- Write: `docs/audits/2026-05-01-three-way/claims.curated.yaml`

- [ ] **Step 1: Open the draft and skim**

```bash
less .audit-local/claims.draft.yaml
```
Look for: hallucinated claims (no actual line match), claims that should have been skipped (philosophy/role), `expected_value` errors, missing `verifiable_by` entries, and obvious gaps.

- [ ] **Step 2: Curate**

Copy the draft to the curated location and edit:

```bash
cp .audit-local/claims.draft.yaml docs/audits/2026-05-01-three-way/claims.curated.yaml
${EDITOR:-vi} docs/audits/2026-05-01-three-way/claims.curated.yaml
```

For each claim, choose: keep (no edit), edit `expected_value`/`subtype`/`verifiable_by`, set `status: pruned` to drop, or add a fresh row. Add a `probe` for behavioral claims that have a safe, idempotent shell check.

Mass-prune trick: any row with `owner: upstream` whose claim is about an upstream module's internal behavior can be set to `status: pruned` in bulk.

- [ ] **Step 3: Validate the curated file with the schema loader**

```bash
uv run --with pyyaml python -c \
  "from audit.schema import load_claims; print(len(load_claims('docs/audits/2026-05-01-three-way/claims.curated.yaml').claims), 'claims OK')"
```
Expected: `N claims OK` where N is your curated count. Any schema violation (bad enum, duplicate id) raises here — fix and re-validate.

- [ ] **Step 4: Commit the curated file**

```bash
git add docs/audits/2026-05-01-three-way/claims.curated.yaml
git commit -m "audit: curated claims ledger (post-review)"
```

---

## Phase 5: VPS dump

The dump is split into two pieces so each is testable in isolation:

- `audit/dump_vps.sh` — bash; only does the SSH capture, writes raw section-marked text to a temp file, then invokes the parser.
- `audit/parse_dump.py` — pure-Python parser; reads the raw text file, emits structured JSON. Unit-testable against fixture text.

### Task 5.1: Implement and test the parser

**Files:**
- Create: `audit/parse_dump.py`
- Create: `audit/tests/test_parse_dump.py`

- [ ] **Step 1: Write the failing tests**

`audit/tests/test_parse_dump.py`:

```python
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
```

- [ ] **Step 2: Run tests, confirm they fail**

```bash
uv run --with pytest pytest audit/tests/test_parse_dump.py -v
```
Expected: FAIL with `ImportError: No module named 'audit.parse_dump'`.

- [ ] **Step 3: Implement `audit/parse_dump.py`**

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Parse the section-marked raw text from dump_vps.sh into structured JSON.

The raw text uses `===<section_name>===` markers. Each section's payload is
the lines until the next marker. Some sections are JSON-per-line
(`docker_ps`); others are key=value (`env_files`); the rest are kept as
raw strings so verifiers can grep them.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SECTION_RE = re.compile(r"^===\s*(\w+)\s*===\s*$", re.MULTILINE)


def _split_sections(raw: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(SECTION_RE.finditer(raw))
    for i, m in enumerate(matches):
        name = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        sections[name] = raw[start:end].strip("\n")
    return sections


def _parse_docker_ps(text: str) -> list[dict]:
    out: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _parse_env_files(text: str) -> dict[str, dict[str, str]]:
    files: dict[str, dict[str, str]] = {}
    cur_file: str | None = None
    cur_kv: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("FILE:"):
            cur_file = line[len("FILE:"):].strip()
            cur_kv = {}
        elif line.startswith("ENDFILE:") and cur_file is not None:
            files[cur_file] = cur_kv
            cur_file = None
            cur_kv = {}
        elif cur_file is not None:
            stripped = line.lstrip()
            if not stripped or stripped.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cur_kv[k.strip()] = v.strip()
    return files


def parse_raw(raw: str, started_at: str, finished_at: str) -> dict:
    """Convert the section-marked raw output into the dump dict."""
    s = _split_sections(raw)
    return {
        "dump_started_at": started_at,
        "dump_finished_at": finished_at,
        "docker_ps": _parse_docker_ps(s.get("docker_ps", "")),
        "docker_inspect_raw": s.get("docker_inspect", ""),
        "systemctl_user_raw": s.get("systemctl_user", ""),
        "listening_ports_raw": s.get("listening_ports", ""),
        "env_files": _parse_env_files(s.get("env_files", "")),
        "bin_1215_raw": s.get("bin_1215", ""),
        "file_hashes_raw": s.get("file_hashes", ""),
    }


def parse_file_to_json(
    raw_path: Path, out_path: Path, started_at: str, finished_at: str
) -> dict:
    raw = raw_path.read_text(errors="replace")
    dump = parse_raw(raw, started_at=started_at, finished_at=finished_at)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(dump, indent=2))
    return dump


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--started-at", required=True)
    ap.add_argument("--finished-at", required=True)
    args = ap.parse_args()
    dump = parse_file_to_json(
        args.raw, args.out, args.started_at, args.finished_at
    )
    print(f"Wrote {args.out} ({len(dump['docker_ps'])} containers)",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests, confirm they pass**

```bash
uv run --with pytest pytest audit/tests/test_parse_dump.py -v
```
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add audit/parse_dump.py audit/tests/test_parse_dump.py
git commit -m "audit: VPS-dump parser with section split + env-file parse"
```

### Task 5.2: Write the SSH capture script

**Files:**
- Create: `audit/dump_vps.sh`

- [ ] **Step 1: Write `audit/dump_vps.sh`**

```bash
#!/usr/bin/env bash
# Capture a single-shot snapshot of the live VPS into a JSON file.
# Usage: bash audit/dump_vps.sh <out-path>
# Requires: ssh alias `Studio54` reaching root@148.230.95.154.
#
# This script only runs the SSH capture and writes the raw section-marked
# text to a temp file. The temp file is then handed to audit/parse_dump.py
# to produce the structured JSON. Splitting capture from parsing keeps each
# piece unit-testable.
set -euo pipefail

OUT="${1:?missing <out-path>}"
SSH_HOST="${VPS_SSH_HOST:-Studio54}"
HERE="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$(dirname "$OUT")"
START="$(date -u +%FT%TZ)"

RAW_TMP="$(mktemp -t vps-dump-raw.XXXXXX)"
trap 'rm -f "$RAW_TMP"' EXIT

# Single SSH session; remote bash interprets the heredoc.
# Quoted 'REMOTE' prevents local interpolation of $variables.
ssh -o BatchMode=yes "$SSH_HOST" 'bash -s' >"$RAW_TMP" <<'REMOTE'
set -uo pipefail
echo "===docker_ps==="
docker ps -a --format '{{json .}}' || true
echo "===docker_inspect==="
for c in $(docker ps --format '{{.Names}}'); do
  docker inspect "$c" || true
  echo
done
echo "===systemctl_user==="
systemctl --user list-units --state=running --no-pager --plain || true
echo "===listening_ports==="
ss -tlnp || true
echo "===env_files==="
for f in /opt/1215-vps/stack/prototype-local/.env; do
  if [ -r "$f" ]; then
    echo "FILE:$f"
    cat "$f"
    echo "ENDFILE:$f"
  fi
done
echo "===bin_1215==="
cd /opt/1215-vps 2>/dev/null && {
  echo "DOCTOR:"
  ./bin/1215 doctor 2>&1 || true
  echo "SERVICES:"
  ./bin/1215 services 2>&1 || true
  echo "STATUS:"
  ./bin/1215 status 2>&1 || true
}
echo "===file_hashes==="
for f in /opt/1215-vps/stack/prototype-local/.env \
         /opt/1215-vps/stack/prototype-local/docker-compose.yml; do
  if [ -r "$f" ]; then
    sha256sum "$f"
  fi
done
echo "===done==="
REMOTE

FINISH="$(date -u +%FT%TZ)"

uv run "$HERE/parse_dump.py" \
    --raw "$RAW_TMP" \
    --out "$OUT" \
    --started-at "$START" \
    --finished-at "$FINISH"
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x audit/dump_vps.sh
```

- [ ] **Step 3: Run a real dump**

```bash
bash audit/dump_vps.sh .audit-local/vps-dump.full.json
chmod 600 .audit-local/vps-dump.full.json
ls -la .audit-local/vps-dump.full.json
python3 -c "import json; d=json.load(open('.audit-local/vps-dump.full.json')); print('containers:', len(d['docker_ps'])); print('env_files:', list(d['env_files']))"
```
Expected: a `.audit-local/vps-dump.full.json` mode 600, with at least 1 container and the prototype-local `.env` parsed.

- [ ] **Step 4: Commit the script (not the dump)**

```bash
git add audit/dump_vps.sh
git commit -m "audit: one-shot VPS SSH capture script"
```

---

## Phase 6: Redaction (TDD)

### Task 6.1: Implement the redactor

**Files:**
- Create: `audit/redact.py`
- Create: `audit/redaction_denylist.txt`
- Create: `audit/tests/test_redact.py`

- [ ] **Step 1: Write the failing tests**

`audit/tests/test_redact.py`:

```python
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
```

- [ ] **Step 2: Create the initial denylist (empty file with comment header)**

`audit/redaction_denylist.txt`:

```
# Sensitive env-var / config-key names to ALWAYS redact, regardless of regex.
# One key per line. Lines starting with `#` are comments.
# Populate after running the first dump, by inspecting .audit-local/vps-dump.full.json.
N8N_OWNER_EMAIL
OPEN_WEBUI_ADMIN_EMAIL
```

- [ ] **Step 3: Run tests, confirm they fail**

```bash
uv run --with pytest pytest audit/tests/test_redact.py -v
```
Expected: FAIL with `ImportError`.

- [ ] **Step 4: Implement `audit/redact.py`**

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Redact secrets from a full VPS dump; emit a committable copy.

Two layers:
  1. Regex on the field name (catches *_KEY, *_SECRET, *_TOKEN, *_PASSWORD,
     *_PASS, *_CREDENTIAL).
  2. Explicit denylist of field names (for things the regex misses, e.g.
     N8N_OWNER_EMAIL).
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

SECRET_NAME_RE = re.compile(
    r"(?:_KEY|_SECRET|_TOKEN|_PASSWORD|_PASS|_CREDENTIAL|_AUTH)$",
    re.IGNORECASE,
)


def load_denylist(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def redact_value(key: str, value: str, denylist: set[str]) -> str:
    if key in denylist or SECRET_NAME_RE.search(key):
        return f"<REDACTED:{key}>"
    return value


def redact_dump(dump: dict, denylist: set[str]) -> dict:
    out = copy.deepcopy(dump)
    env_files = out.get("env_files", {})
    for fname, kv in env_files.items():
        env_files[fname] = {k: redact_value(k, v, denylist) for k, v in kv.items()}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument(
        "--denylist",
        type=Path,
        default=Path(__file__).parent / "redaction_denylist.txt",
    )
    args = ap.parse_args()
    dump = json.loads(args.inp.read_text())
    denylist = load_denylist(args.denylist)
    redacted = redact_dump(dump, denylist)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(redacted, indent=2))
    # Final sanity check: no obvious secret-shaped value left.
    blob = json.dumps(redacted)
    if re.search(r"(?i)(password|secret|api[_-]?key)\\\\?\":\\s*\"[^<]", blob):
        print("WARN: possible unredacted secret in output; eyeball before commit",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run tests, confirm they pass**

```bash
uv run --with pytest pytest audit/tests/test_redact.py -v
```
Expected: PASS (5 tests).

- [ ] **Step 6: Run redaction on the real dump**

```bash
uv run audit/redact.py \
    --in .audit-local/vps-dump.full.json \
    --out docs/audits/2026-05-01-three-way/vps-dump.redacted.json
grep -E "REDACTED|password|secret|hunter2" docs/audits/2026-05-01-three-way/vps-dump.redacted.json | head -20
```
Expected: every line containing `password|secret|hunter2` should be a `<REDACTED:...>` placeholder. Eyeball the output. If any plaintext secret remains, add the field name to `audit/redaction_denylist.txt` and re-run.

- [ ] **Step 7: Commit redactor and the redacted dump**

```bash
git add audit/redact.py audit/redaction_denylist.txt audit/tests/test_redact.py \
        docs/audits/2026-05-01-three-way/vps-dump.redacted.json
git commit -m "audit: redactor with regex + denylist; first redacted dump"
```

---

## Phase 7: Verifier (TDD)

### Task 7.1: Doc resolver

**Files:**
- Create: `audit/verify.py` (skeleton, just doc resolver for now)
- Create: `audit/tests/test_verify_resolvers.py`

- [ ] **Step 1: Write the failing test**

`audit/tests/test_verify_resolvers.py`:

```python
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
```

- [ ] **Step 2: Run test, confirm it fails**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_verify_resolvers.py::test_doc_resolver_reads_line -v
```
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement skeleton + doc resolver in `audit/verify.py`**

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Three-resolver verifier: doc, code, vps. Then classify each row."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import yaml

from audit.schema import Claim, ClaimSet, dump_claims, load_claims


def resolve_doc(claim: Claim, repo_root: Path) -> str | None:
    """Re-read source_file:source_line ± 2 and return the joined text."""
    path = repo_root / claim.source_file
    if not path.exists():
        return None
    lines = path.read_text(errors="replace").splitlines()
    n = len(lines)
    lo = max(0, claim.source_line - 3)
    hi = min(n, claim.source_line + 2)
    return "\n".join(lines[lo:hi])


def main() -> int:
    raise SystemExit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests, confirm they pass**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_verify_resolvers.py -v
```
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add audit/verify.py audit/tests/test_verify_resolvers.py
git commit -m "audit: verify.py skeleton + doc resolver"
```

### Task 7.2: Code resolver

**Files:**
- Modify: `audit/verify.py` — add `resolve_code`
- Modify: `audit/tests/test_verify_resolvers.py` — add tests

- [ ] **Step 1: Add the failing tests**

Append to `audit/tests/test_verify_resolvers.py`:

```python
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
```

- [ ] **Step 2: Run tests, confirm they fail**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_verify_resolvers.py -v
```
Expected: 4 new tests FAIL with `ImportError`.

- [ ] **Step 3: Implement `resolve_code` in `audit/verify.py`**

Insert after `resolve_doc`:

```python
GREP_GLOBS = ("*.yml", "*.yaml", "*.toml", "*.env", "*.py", "*.sh", "Makefile")


def _grep(pattern: str, root: Path) -> str | None:
    """Run a ripgrep-like search; return up to 5 matching lines."""
    try:
        result = subprocess.run(
            ["grep", "-rIn", "--include=*.yml", "--include=*.yaml",
             "--include=*.toml", "--include=*.env", "--include=*.py",
             "--include=*.sh", "--include=Makefile",
             "-e", pattern, str(root)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    lines = [l for l in result.stdout.splitlines() if l.strip()][:5]
    return "\n".join(lines) if lines else None


def resolve_code(claim: Claim, repo_root: Path) -> str | None:
    """Type-dispatched probe of the codebase."""
    if claim.probe:
        try:
            r = subprocess.run(
                claim.probe, shell=True, capture_output=True, text=True,
                timeout=20, cwd=repo_root,
            )
            return (r.stdout + r.stderr).strip() or None
        except subprocess.TimeoutExpired:
            return "PROBE_TIMEOUT"
    st = (claim.subtype or "").lower()
    val = claim.expected_value
    if st in ("port", "container_port", "host_port"):
        return _grep(str(val), repo_root)
    if st in ("path", "file_path"):
        target = repo_root / str(val)
        return f"path exists: {target}" if target.exists() else f"path missing: {target}"
    if st in ("env_var", "config_key"):
        return _grep(str(val), repo_root)
    if st in ("command", "command_name", "service_name", "container_name"):
        return _grep(str(val), repo_root)
    return None
```

- [ ] **Step 4: Run tests, confirm they pass**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_verify_resolvers.py -v
```
Expected: PASS (6 tests total).

- [ ] **Step 5: Commit**

```bash
git add audit/verify.py audit/tests/test_verify_resolvers.py
git commit -m "audit: code resolver with type-dispatched grep + probe support"
```

### Task 7.3: VPS resolver

**Files:**
- Modify: `audit/verify.py` — add `resolve_vps`
- Modify: `audit/tests/test_verify_resolvers.py` — add tests

- [ ] **Step 1: Add the failing tests**

Append to `audit/tests/test_verify_resolvers.py`:

```python
from audit.verify import resolve_vps


def test_vps_resolver_container_count(sample_dump_dict: dict) -> None:
    claim = Claim(
        id="c-6", source_file="STATE.md", source_line=1, owner="owned",
        claim_type="concrete", subtype="container_count",
        claim_text="2 containers", expected_value=2, verifiable_by=["vps"],
    )
    out = resolve_vps(claim, sample_dump_dict)
    assert "2" in out


def test_vps_resolver_container_name(sample_dump_dict: dict) -> None:
    claim = Claim(
        id="c-7", source_file="x.md", source_line=1, owner="owned",
        claim_type="concrete", subtype="container_name",
        claim_text="n8n is up", expected_value="n8n", verifiable_by=["vps"],
    )
    out = resolve_vps(claim, sample_dump_dict)
    assert "running" in out.lower()


def test_vps_resolver_env_var_present(sample_dump_dict: dict) -> None:
    claim = Claim(
        id="c-8", source_file="x.md", source_line=1, owner="owned",
        claim_type="concrete", subtype="env_var",
        claim_text="postgres port set", expected_value="POSTGRES_PORT",
        verifiable_by=["vps"],
    )
    out = resolve_vps(claim, sample_dump_dict)
    assert "5432" in out


def test_vps_resolver_port_listening(sample_dump_dict: dict) -> None:
    claim = Claim(
        id="c-9", source_file="x.md", source_line=1, owner="owned",
        claim_type="concrete", subtype="port",
        claim_text="5678 is listening", expected_value=5678,
        verifiable_by=["vps"],
    )
    out = resolve_vps(claim, sample_dump_dict)
    assert out is None or "not" in out.lower() or "5678" not in out  # noqa: PLR1714
    # Note: sample_dump only declares 5432; this asserts the resolver returns
    # a clean "not found" rather than a hallucinated match.
```

- [ ] **Step 2: Run tests, confirm they fail**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_verify_resolvers.py -v
```
Expected: 4 new tests FAIL with `ImportError`.

- [ ] **Step 3: Implement `resolve_vps`**

Append to `audit/verify.py`:

```python
def resolve_vps(claim: Claim, dump: dict) -> str | None:
    st = (claim.subtype or "").lower()
    val = claim.expected_value
    if st == "container_count":
        running = [c for c in dump.get("docker_ps", [])
                   if str(c.get("State", "")).lower() == "running"]
        return f"{len(running)} containers running"
    if st in ("container_name",):
        match = next((c for c in dump.get("docker_ps", [])
                      if str(c.get("Names", "")) == str(val)), None)
        if match is None:
            return f"container {val!r} not found"
        return f"{match['Names']} is {match.get('State', 'unknown')}"
    if st in ("env_var", "config_key"):
        for fname, kv in dump.get("env_files", {}).items():
            if str(val) in kv:
                return f"{fname}: {val}={kv[str(val)]}"
        return f"{val} not present in any env file"
    if st in ("port",):
        # Search docker_ps and listening_ports_raw for the port
        for c in dump.get("docker_ps", []):
            if str(val) in str(c.get("Ports", "")):
                return f"port {val} bound by container {c.get('Names')}"
        ports_raw = dump.get("listening_ports_raw", "")
        if str(val) in ports_raw:
            return f"port {val} present in ss output"
        return f"port {val} not seen in dump"
    return None
```

- [ ] **Step 4: Run tests, confirm they pass**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_verify_resolvers.py -v
```
Expected: PASS (10 tests total).

- [ ] **Step 5: Commit**

```bash
git add audit/verify.py audit/tests/test_verify_resolvers.py
git commit -m "audit: vps resolver matches container/port/env_var against dump"
```

### Task 7.4: Classifier and end-to-end verification

**Files:**
- Modify: `audit/verify.py` — add `classify` and a `main` that walks all claims
- Create: `audit/tests/test_verify_classifier.py`

- [ ] **Step 1: Write the failing tests**

`audit/tests/test_verify_classifier.py`:

```python
"""Tests for the MATCH/DRIFT/UNVERIFIABLE classifier."""
from __future__ import annotations

from audit.verify import classify


def test_match_when_all_three_agree() -> None:
    s, fix = classify("port 5432", "5432 in compose", "5432 listening", expected="5432")
    assert s == "MATCH"


def test_drift_when_doc_disagrees() -> None:
    s, fix = classify("port 5432", "5432 in compose", "port 5433 not seen", expected="5433")
    assert s == "DRIFT"
    assert "fix" in fix.lower() or "update" in fix.lower()


def test_unverifiable_when_only_one_resolver() -> None:
    s, fix = classify("rationale", None, None, expected="phil")
    assert s == "UNVERIFIABLE"


def test_doc_stale_when_code_and_vps_agree_doc_disagrees() -> None:
    s, fix = classify(
        "STATE.md says 14 containers",
        "compose declares 13 services",
        "13 containers running",
        expected=14,
    )
    assert s == "DRIFT_DOC_STALE"
```

- [ ] **Step 2: Run tests, confirm they fail**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_verify_classifier.py -v
```
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `classify` and the `main` driver**

Append to `audit/verify.py`:

```python
def _agrees(text: str | None, expected) -> bool:
    if text is None or expected is None:
        return False
    return str(expected) in text


def classify(
    doc_says: str | None,
    code_says: str | None,
    vps_says: str | None,
    expected,
) -> tuple[str, str]:
    d = _agrees(doc_says, expected)
    c = _agrees(code_says, expected)
    v = _agrees(vps_says, expected)
    n_known = sum(x is not None for x in (doc_says, code_says, vps_says))
    if n_known == 0:
        return "UNVERIFIABLE", ""
    if d and c and v:
        return "MATCH", ""
    # One non-doc resolver disagrees but doc and code agree → DRIFT_DOC_STALE
    if (c and v) and not d and doc_says is not None:
        return "DRIFT_DOC_STALE", (
            f"update doc to match: {vps_says or code_says}"
        )
    if any((d, c, v)) and n_known < 2:
        return "UNVERIFIABLE", "partial_match" if any((d, c, v)) else ""
    return "DRIFT", f"reconcile sources; vps says: {vps_says or code_says or doc_says}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", required=True, type=Path)
    ap.add_argument("--dump", required=True, type=Path)
    ap.add_argument("--repo-root", default=Path.cwd(), type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    cs = load_claims(args.claims)
    dump = json.loads(args.dump.read_text())

    for claim in cs.claims:
        if claim.status == "pruned":
            continue
        claim.doc_says = resolve_doc(claim, args.repo_root) if "doc" in claim.verifiable_by else None
        claim.code_says = resolve_code(claim, args.repo_root) if "code" in claim.verifiable_by else None
        claim.vps_says = resolve_vps(claim, dump) if "vps" in claim.verifiable_by else None
        claim.status, claim.suggested_fix = classify(
            claim.doc_says, claim.code_says, claim.vps_says, claim.expected_value
        )

    dump_claims(cs, args.out)
    n_drift = sum(1 for c in cs.claims if c.status and "DRIFT" in c.status)
    print(f"Verified {len(cs.claims)} claims, {n_drift} drift(s)", flush=True)
    return 0
```

- [ ] **Step 4: Run all verifier tests**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_verify_resolvers.py audit/tests/test_verify_classifier.py -v
```
Expected: PASS (14 tests total).

- [ ] **Step 5: Run end-to-end verify against real data**

```bash
uv run audit/verify.py \
    --claims docs/audits/2026-05-01-three-way/claims.curated.yaml \
    --dump .audit-local/vps-dump.full.json \
    --repo-root . \
    --out .audit-local/claims.verified.yaml
grep -c '^- ' .audit-local/claims.verified.yaml
```
Expected: count matches the curated claim count; stdout shows `Verified N claims, M drift(s)`.

- [ ] **Step 6: Commit**

```bash
git add audit/verify.py audit/tests/test_verify_classifier.py
git commit -m "audit: classifier (MATCH/DRIFT/DOC_STALE/UNVERIFIABLE) + verify driver"
```

---

## Phase 8: Reporter (TDD)

### Task 8.1: ledger.csv writer

**Files:**
- Create: `audit/report.py`
- Create: `audit/tests/test_report.py`

- [ ] **Step 1: Write the failing tests**

`audit/tests/test_report.py`:

```python
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
```

- [ ] **Step 2: Run tests, confirm they fail**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_report.py -v
```
Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement `audit/report.py`**

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Format the verified claim set into ledger.csv + summary.md."""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from audit.schema import ClaimSet, load_claims

LEDGER_COLUMNS = [
    "id", "source_files", "source_lines", "owner", "claim_type",
    "subtype", "claim_text", "expected_value", "doc_says", "code_says",
    "vps_says", "status", "suggested_fix", "notes",
]


def write_ledger(cs: ClaimSet, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS)
        w.writeheader()
        for c in cs.claims:
            if c.status == "pruned":
                continue
            files = [c.source_file, *c.seen_in]
            w.writerow({
                "id": c.id,
                "source_files": "; ".join(files),
                "source_lines": str(c.source_line),
                "owner": c.owner,
                "claim_type": c.claim_type,
                "subtype": c.subtype,
                "claim_text": c.claim_text,
                "expected_value": "" if c.expected_value is None else str(c.expected_value),
                "doc_says": (c.doc_says or "")[:300],
                "code_says": (c.code_says or "")[:300],
                "vps_says": (c.vps_says or "")[:300],
                "status": c.status or "",
                "suggested_fix": c.suggested_fix or "",
                "notes": c.notes or "",
            })


def write_summary(cs: ClaimSet, out: Path) -> None:
    active = [c for c in cs.claims if c.status != "pruned"]
    counts = Counter(c.status for c in active)
    drifts = [c for c in active if c.status and "DRIFT" in c.status]
    drifts.sort(key=lambda c: c.source_file)
    by_file = Counter(c.source_file for c in drifts)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Three-way audit — 2026-05-01\n")
    lines.append(f"- Total claims: {len(active)}")
    lines.append(f"- Headline: {counts.get('MATCH', 0)} MATCH, "
                 f"{sum(v for k, v in counts.items() if 'DRIFT' in k)} DRIFT, "
                 f"{counts.get('UNVERIFIABLE', 0)} UNVERIFIABLE\n")
    lines.append("## Top drifts\n")
    for c in drifts[:10]:
        lines.append(
            f"- **{c.source_file}:{c.source_line}** ({c.status}) — "
            f"{c.claim_text} → {c.suggested_fix}"
        )
    lines.append("\n## Drift by source\n")
    for src, n in by_file.most_common():
        lines.append(f"- {src}: {n} drift(s)")
    lines.append("\n## Suggested fix list (grouped by file)\n")
    fix_by_file: dict[str, list] = {}
    for c in drifts:
        fix_by_file.setdefault(c.source_file, []).append(c)
    for src, items in sorted(fix_by_file.items()):
        lines.append(f"### {src}")
        for c in items:
            lines.append(f"- L{c.source_line}: {c.suggested_fix or '(see ledger.csv)'}")
        lines.append("")
    out.write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verified", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()
    cs = load_claims(args.verified)
    write_ledger(cs, args.out_dir / "ledger.csv")
    write_summary(cs, args.out_dir / "summary.md")
    print(f"Wrote {args.out_dir}/ledger.csv and summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests, confirm they pass**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/test_report.py -v
```
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add audit/report.py audit/tests/test_report.py
git commit -m "audit: report generator — ledger.csv + summary.md"
```

---

## Phase 9: End-to-end run

### Task 9.1: Run the full pipeline against real data

**Files:**
- Write: `docs/audits/2026-05-01-three-way/ledger.csv`
- Write: `docs/audits/2026-05-01-three-way/summary.md`

- [ ] **Step 1: Make sure all prior artifacts exist**

```bash
ls -la docs/audits/2026-05-01-three-way/
ls -la .audit-local/
```
Expected: `scope.manifest.json`, `claims.curated.yaml`, `vps-dump.redacted.json` in `docs/audits/...`; `claims.draft.yaml`, `vps-dump.full.json`, `claims.verified.yaml` in `.audit-local/`.

- [ ] **Step 2: Run the report generator**

```bash
uv run audit/report.py \
    --verified .audit-local/claims.verified.yaml \
    --out-dir docs/audits/2026-05-01-three-way/
head -60 docs/audits/2026-05-01-three-way/summary.md
wc -l docs/audits/2026-05-01-three-way/ledger.csv
```
Expected: a populated `summary.md` with a headline like `"X MATCH, Y DRIFT, Z UNVERIFIABLE"`; `ledger.csv` line count = curated claim count + 1 header row.

- [ ] **Step 3: Read summary.md, eyeball top drifts**

```bash
less docs/audits/2026-05-01-three-way/summary.md
```
Sanity check: any "drift" that is actually a false positive should be re-curated (set `status: pruned` in `claims.curated.yaml` with a note) and the pipeline re-run from Step 2. Real drifts are expected — that is the point of the audit.

- [ ] **Step 4: Final secret-leak check on the redacted dump**

```bash
grep -E "(?i)password|secret|api.{0,2}key" docs/audits/2026-05-01-three-way/vps-dump.redacted.json | grep -v REDACTED | head
```
Expected: NO output (every secret-shaped key/value is `<REDACTED:...>`). If anything leaks, add the field name to `audit/redaction_denylist.txt`, re-run `audit/redact.py`, and re-verify.

- [ ] **Step 5: Run the full test suite once more**

```bash
uv run --with pyyaml --with pytest pytest audit/tests/ -v
```
Expected: PASS (all tests across schema, manifest, extract, parse_dump, redact, verify, and report).

- [ ] **Step 6: Commit the final artifacts**

```bash
git add docs/audits/2026-05-01-three-way/ledger.csv \
        docs/audits/2026-05-01-three-way/summary.md
git commit -m "audit: 2026-05-01 three-way audit — ledger and summary"
```

### Task 9.2: Update repo-level docs

**Files:**
- Modify: `README.md` — add a one-line pointer to the audit
- Modify: `docs/architecture/current-state.md` — note any drift the audit caught (or schedule fixes)

- [ ] **Step 1: Add audit pointer to `README.md`**

Find the appropriate section (probably near "Documentation" or "State") and add:

```markdown
- [Three-way audit (2026-05-01)](docs/audits/2026-05-01-three-way/summary.md) — most recent docs/code/VPS reality check
```

- [ ] **Step 2: Note follow-up actions**

Open `summary.md` and skim the suggested fix list. Each entry is a future task: it lives in `summary.md` and `ledger.csv`. Decide whether to file them as a TODO list, Archon tasks, or fix immediately. (This plan does not require fixing the drift; surfacing it is the deliverable.)

- [ ] **Step 3: Commit the README update**

```bash
git add README.md
git commit -m "docs: link to 2026-05-01 three-way audit summary"
```

---

## Self-review checklist (run before handing off)

- [ ] Every spec section maps to at least one task (schema → P1; manifest → P2; extractor → P3; review → P4; dump → P5; redact → P6; verify → P7; report → P8; run → P9).
- [ ] Every TDD task runs the failing test before implementing.
- [ ] Every code step has actual code, not "implement X".
- [ ] Function names are consistent across tasks (`resolve_doc / resolve_code / resolve_vps / classify`, `write_ledger / write_summary`, `redact_value / redact_dump`, `build_manifest / write_manifest`, `parse_subagent_output / merge_claims / assign_ids`, `parse_raw / parse_file_to_json`).
- [ ] All artifacts the spec lists under `docs/audits/2026-05-01-three-way/` are produced by the listed tasks.
- [ ] Secrets policy: full dump is gitignored (Phase 0 Step 2); redacted dump is committed only after Phase 6 Step 6 inspection.
- [ ] Reusable: every script under `audit/` has a CLI entry point, not just a function.
