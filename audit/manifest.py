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


def _is_in_scope(rel_parts: tuple[str, ...]) -> bool:
    """Filter rule:
    - Skip hidden directories anywhere in the path.
    - Under modules/, only include top-level READMEs (modules/<x>/README.md).
    """
    if any(part.startswith(".") for part in rel_parts):
        return False
    if rel_parts and rel_parts[0] == "modules":
        return len(rel_parts) == 3 and rel_parts[2] == "README.md"
    return True


def build_manifest(root: Path) -> dict:
    entries: list[dict] = []
    for path in sorted(root.rglob("*.md")):
        rel_parts = path.relative_to(root).parts
        if not _is_in_scope(rel_parts):
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
