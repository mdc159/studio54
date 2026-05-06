#!/usr/bin/env python3
"""Verify a Studio54 node proof JSON file."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_TOP_LEVEL = {
    "schemaVersion",
    "generatedAt",
    "git",
    "target",
    "redaction",
    "compose",
    "services",
    "paperclip",
    "hermes",
    "memoryIsolation",
    "traceability",
    "artifacts",
    "result",
}
CHECK_STATUSES = {"PASS", "FAIL", "SKIP", "UNKNOWN"}
TARGET_KINDS = {"simulation", "local-vm", "staging-vps", "live-vps"}
HERMES_PATHS = {"hermes_local", "hermes-gateway", "host-hermes", "unknown"}
ARTIFACT_KINDS = {"json", "log", "text", "directory", "other"}
PAPERCLIP_PROOF_KEYS = {"parentIssue", "childIssues", "assignment", "comments", "finalStatus", "runawayChildren"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"failed to parse JSON: {exc}") from exc


def resolve_artifact_path(path_value: str, proof_path: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    proof_relative = (proof_path.parent / path).resolve()
    if proof_relative.exists():
        return proof_relative
    return (ROOT / path).resolve()


def require_object(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def require_status(value: Any, name: str, errors: list[str]) -> None:
    if value not in CHECK_STATUSES:
        errors.append(f"{name} must be one of {sorted(CHECK_STATUSES)}")


def validate_required(proof: dict[str, Any], errors: list[str]) -> None:
    missing = sorted(REQUIRED_TOP_LEVEL - set(proof))
    if missing:
        errors.append(f"missing required top-level fields: {', '.join(missing)}")
    if proof.get("schemaVersion") != "studio54.node-proof.v1":
        errors.append("schemaVersion must be studio54.node-proof.v1")


def require_non_empty_string(section: dict[str, Any], key: str, name: str, errors: list[str]) -> None:
    if not isinstance(section.get(key), str) or not section[key]:
        errors.append(f"{name}.{key} must be a non-empty string")


def require_string_array(section: dict[str, Any], key: str, name: str, errors: list[str]) -> None:
    value = section.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append(f"{name}.{key} must be an array of strings")


def validate_git_and_target(proof: dict[str, Any], errors: list[str]) -> None:
    git = require_object(proof.get("git"), "git", errors)
    require_non_empty_string(git, "sha", "git", errors)
    require_non_empty_string(git, "branch", "git", errors)
    if not isinstance(git.get("dirty"), bool):
        errors.append("git.dirty must be a boolean")

    target = require_object(proof.get("target"), "target", errors)
    if target.get("kind") not in TARGET_KINDS:
        errors.append(f"target.kind must be one of {sorted(TARGET_KINDS)}")
    for key in ("name", "host", "environment"):
        require_non_empty_string(target, key, "target", errors)


def validate_component_statuses(proof: dict[str, Any], errors: list[str]) -> None:
    sections: dict[str, dict[str, Any]] = {}
    for key in ("redaction", "compose", "paperclip", "hermes", "memoryIsolation", "traceability"):
        section = require_object(proof.get(key), key, errors)
        sections[key] = section
        require_status(section.get("status"), f"{key}.status", errors)

    redaction = sections["redaction"]
    if not isinstance(redaction.get("checked"), bool):
        errors.append("redaction.checked must be a boolean")
    if not isinstance(redaction.get("notes"), list) or any(not isinstance(item, str) for item in redaction.get("notes", [])):
        errors.append("redaction.notes must be an array of strings")

    compose = sections["compose"]
    require_non_empty_string(compose, "command", "compose", errors)
    require_string_array(compose, "composeFiles", "compose", errors)
    require_string_array(compose, "services", "compose", errors)

    paperclip = sections["paperclip"]
    for key in ("companyId", "managerAgentId"):
        if not isinstance(paperclip.get(key), str):
            errors.append(f"paperclip.{key} must be a string")
    require_string_array(paperclip, "workerAgentIds", "paperclip", errors)
    proof_summary = require_object(paperclip.get("proofSummary"), "paperclip.proofSummary", errors)
    missing_summary = sorted(PAPERCLIP_PROOF_KEYS - set(proof_summary))
    if missing_summary:
        errors.append(f"paperclip.proofSummary missing keys: {', '.join(missing_summary)}")
    for key in PAPERCLIP_PROOF_KEYS & set(proof_summary):
        require_status(proof_summary.get(key), f"paperclip.proofSummary.{key}", errors)

    hermes = sections["hermes"]
    if hermes.get("path") not in HERMES_PATHS:
        errors.append(f"hermes.path must be one of {sorted(HERMES_PATHS)}")
    require_non_empty_string(hermes, "mode", "hermes", errors)
    if "runIds" in hermes:
        require_string_array(hermes, "runIds", "hermes", errors)

    memory = sections["memoryIsolation"]
    checks = memory.get("checks")
    if not isinstance(checks, dict) or not checks:
        errors.append("memoryIsolation.checks must be a non-empty object")
    elif "" in checks:
        errors.append("memoryIsolation.checks cannot contain a blank key")
    else:
        for key, value in checks.items():
            require_status(value, f"memoryIsolation.checks.{key}", errors)

    services = proof.get("services")
    if not isinstance(services, dict) or not services:
        errors.append("services must be a non-empty object")
    elif "" in services:
        errors.append("services cannot contain a blank key")
    else:
        for name, service in services.items():
            service_obj = require_object(service, f"services.{name}", errors)
            require_status(service_obj.get("status"), f"services.{name}.status", errors)


def validate_traceability(proof: dict[str, Any], errors: list[str]) -> None:
    traceability = require_object(proof.get("traceability"), "traceability", errors)
    ids = traceability.get("ids")
    if ids is None:
        return
    if not isinstance(ids, dict) or not ids:
        errors.append("traceability.ids must be omitted or a non-empty object")
        return
    allowed = {"paperclipRunId", "hermesRunId", "langfuseTraceId", "paperclipIssueId"}
    unknown = sorted(set(ids) - allowed)
    if unknown:
        errors.append(f"traceability.ids contains unknown keys: {', '.join(unknown)}")
    for key, value in ids.items():
        if not isinstance(value, str) or not value:
            errors.append(f"traceability.ids.{key} must be a non-empty string")


def validate_artifacts(proof: dict[str, Any], proof_path: Path, errors: list[str]) -> None:
    artifacts = proof.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts must be a non-empty array")
        return
    for index, item in enumerate(artifacts):
        if not isinstance(item, dict):
            errors.append(f"artifacts[{index}] must be an object")
            continue
        for key in ("name", "path", "kind"):
            if not isinstance(item.get(key), str) or not item[key]:
                errors.append(f"artifacts[{index}].{key} must be a non-empty string")
        if isinstance(item.get("kind"), str) and item["kind"] not in ARTIFACT_KINDS:
            errors.append(f"artifacts[{index}].kind must be one of {sorted(ARTIFACT_KINDS)}")
        if not isinstance(item.get("path"), str):
            continue
        path = resolve_artifact_path(item["path"], proof_path)
        if not path.exists():
            errors.append(f"artifact does not exist: {item['path']}")
            continue
        expected_hash = item.get("sha256")
        if expected_hash:
            if not path.is_file():
                errors.append(f"artifact sha256 provided for non-file path: {item['path']}")
            elif sha256(path) != expected_hash:
                errors.append(f"artifact sha256 mismatch: {item['path']}")


def validate_result(proof: dict[str, Any], errors: list[str]) -> None:
    result = require_object(proof.get("result"), "result", errors)
    if result.get("status") not in {"PASS", "FAIL"}:
        errors.append("result.status must be PASS or FAIL")
    if not isinstance(result.get("summary"), str) or not result["summary"]:
        errors.append("result.summary must be a non-empty string")
    if result.get("status") == "PASS":
        for key in ("redaction", "compose", "hermes", "memoryIsolation"):
            section = proof.get(key)
            if isinstance(section, dict) and section.get("status") == "FAIL":
                errors.append(f"result.status cannot be PASS when {key}.status is FAIL")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proof", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    proof_path = args.proof.resolve()
    try:
        raw = load_json(proof_path)
    except ValueError as exc:
        report = {
            "schema": "studio54.node-proof-verification.v1",
            "proof": str(proof_path),
            "status": "FAIL",
            "errors": [str(exc)],
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1
    proof = require_object(raw, "proof", errors)
    validate_required(proof, errors)
    validate_git_and_target(proof, errors)
    validate_component_statuses(proof, errors)
    validate_traceability(proof, errors)
    validate_artifacts(proof, proof_path, errors)
    validate_result(proof, errors)

    report = {
        "schema": "studio54.node-proof-verification.v1",
        "proof": str(proof_path),
        "status": "FAIL" if errors else "PASS",
        "errors": errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
