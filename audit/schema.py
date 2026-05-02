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
