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
