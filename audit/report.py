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
            files = [c.source_file, *(c.seen_in or [])]
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
    lines.append(
        f"- Headline: {counts.get('MATCH', 0)} MATCH, "
        f"{sum(v for k, v in counts.items() if k and 'DRIFT' in k)} DRIFT, "
        f"{counts.get('UNVERIFIABLE', 0)} UNVERIFIABLE\n"
    )
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
