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
