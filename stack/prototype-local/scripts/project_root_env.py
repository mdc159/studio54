#!/usr/bin/env python3
"""Project the canonical repo-root .env contract into stack/prototype-local/.env."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from init_env import parse_env_assignments, render_env


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE = REPO_ROOT / ".env"
DEFAULT_SOURCE_FALLBACK = REPO_ROOT / ".env.example"
DEFAULT_STACK_EXAMPLE = REPO_ROOT / "stack" / "prototype-local" / ".env.example"
DEFAULT_STACK_OUTPUT = REPO_ROOT / "stack" / "prototype-local" / ".env"
DEFAULT_ROOT_EXAMPLE = REPO_ROOT / ".env.example"


def resolve_source_path(path: Path | None) -> Path:
    if path is not None:
        return path.resolve()
    if DEFAULT_SOURCE.exists():
        return DEFAULT_SOURCE.resolve()
    return DEFAULT_SOURCE_FALLBACK.resolve()


def render_with_projection(
    stack_example_text: str,
    source_values: dict[str, str],
    source_placeholders: dict[str, str],
    existing_output_values: dict[str, str],
) -> str:
    baseline = render_env(stack_example_text, existing_output_values)
    baseline_values = parse_env_assignments(baseline)

    for key in list(baseline_values):
        if key in source_values and should_project_value(
            key,
            source_values[key],
            source_placeholders,
        ):
            baseline_values[key] = source_values[key]

    rendered_lines: list[str] = []
    for line in stack_example_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            rendered_lines.append(line)
            continue
        key, _ = line.split("=", 1)
        rendered_lines.append(f"{key}={baseline_values[key]}")

    return "\n".join(rendered_lines) + "\n"


def should_project_value(
    key: str,
    value: str,
    source_placeholders: dict[str, str],
) -> bool:
    if value == "":
        return False
    placeholder = source_placeholders.get(key)
    if placeholder is not None and value == placeholder:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Project repo-root .env values into stack/prototype-local/.env",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Source env file. Defaults to repo-root .env, falling back to .env.example.",
    )
    parser.add_argument(
        "--stack-example",
        type=Path,
        default=DEFAULT_STACK_EXAMPLE,
        help="Stack-local .env.example template.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_STACK_OUTPUT,
        help="Projected stack-local .env output path.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists.",
    )
    args = parser.parse_args()

    source_path = resolve_source_path(args.source)
    stack_example_path = args.stack_example.resolve()
    output_path = args.output.resolve()
    root_example_path = DEFAULT_ROOT_EXAMPLE.resolve()

    if not source_path.exists():
        raise SystemExit(f"missing source env: {source_path}")
    if not stack_example_path.exists():
        raise SystemExit(f"missing stack example template: {stack_example_path}")
    if not root_example_path.exists():
        raise SystemExit(f"missing root example template: {root_example_path}")
    if output_path.exists() and not args.force:
        raise SystemExit(f"refusing to overwrite existing env file: {output_path} (use --force)")

    source_values = parse_env_assignments(source_path.read_text())
    source_placeholders = parse_env_assignments(root_example_path.read_text())
    stack_example_text = stack_example_path.read_text()
    existing_output_values = parse_env_assignments(output_path.read_text()) if output_path.exists() else {}
    rendered = render_with_projection(
        stack_example_text,
        source_values,
        source_placeholders,
        existing_output_values,
    )

    output_path.write_text(rendered)
    os.chmod(output_path, 0o600)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
