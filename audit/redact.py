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
    if re.search(r'(?i)(password|secret|api[_-]?key)\\?":\\s*"[^<]', blob):
        print("WARN: possible unredacted secret in output; eyeball before commit",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
