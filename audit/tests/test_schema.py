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
