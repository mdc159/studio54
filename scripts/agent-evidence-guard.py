#!/usr/bin/env python3
"""Small anti-cheat guard for agent PRs.

This is not security theater: an LLM can edit repo files, so the first defense is
making evaluator changes visible and separating them from feature changes. CI runs
this script to mark protected verifier-path edits as an explicit review item.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

PROTECTED_PREFIXES = (
    ".github/workflows/",
    "scripts/agent-evidence-guard.py",
    "scripts/verify-simulated-vps-bootstrap.py",
    "scripts/simulate-vps-bootstrap.sh",
    "docs/architecture/cloud-agent-vps-simulation.md",
)


def changed_files(base_ref: str) -> list[str]:
    subprocess.run(["git", "fetch", "origin", base_ref, "--depth=1"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    result = subprocess.run(
        ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--output", type=Path, default=Path(".artifacts/agent-validation/evidence-guard.json"))
    args = parser.parse_args()

    files = changed_files(args.base_ref)
    protected = [path for path in files if path.startswith(PROTECTED_PREFIXES) or path in PROTECTED_PREFIXES]
    report = {
        "schema": "studio54.agent-evidence-guard.v1",
        "baseRef": args.base_ref,
        "changedFiles": files,
        "protectedVerifierChanges": protected,
        "status": "REVIEW_REQUIRED" if protected else "PASS",
        "note": "Protected verifier changes are allowed only when the PR is explicitly about the verifier/workbench.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
