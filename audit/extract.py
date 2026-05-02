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
        doc = yaml.safe_load(stripped)
    except yaml.YAMLError as e:
        print(f"WARN: failed to parse YAML for {source_file}: {e}", file=sys.stderr)
        return []
    if doc is None:
        doc = {}
    if not isinstance(doc, dict) or "claims" not in doc:
        print(f"WARN: no 'claims' key in subagent output for {source_file}",
              file=sys.stderr)
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
            "--tools", "",  # disable all tools (text-in/text-out)
            "--append-system-prompt", prompt,
            "--",
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
