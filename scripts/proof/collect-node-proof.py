#!/usr/bin/env python3
"""Collect a local node proof from existing verifier commands."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COMPOSE_FILE = "stack/prototype-local/docker-compose.substrate.yml"
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*=\s*\S+"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(name: str, command: list[str], output_dir: Path, env: dict[str, str] | None = None) -> dict[str, Any]:
    log_path = output_dir / f"{name}.log"
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    log_path.write_text(result.stdout)
    return {
        "name": name,
        "command": " ".join(command),
        "returncode": result.returncode,
        "log": log_path,
        "status": "PASS" if result.returncode == 0 else "FAIL",
    }


def artifact(name: str, path: Path, kind: str) -> dict[str, Any]:
    data = {
        "name": name,
        "path": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
        "kind": kind,
    }
    if path.is_file():
        data["sha256"] = sha256(path)
    return data


def check_redaction(paths: list[Path]) -> dict[str, Any]:
    findings: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(errors="replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(str(path))
                break
    return {
        "status": "FAIL" if findings else "PASS",
        "checked": True,
        "notes": [f"possible secret pattern in {path}" for path in findings],
    }


def collect_compose(output_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    compose_file = DEFAULT_COMPOSE_FILE
    env_file = output_dir / "prototype.env"
    artifacts: list[dict[str, Any]] = []
    init_result = run_command(
        "init-env",
        ["python3", "stack/prototype-local/scripts/init_env.py", "--output", str(env_file), "--force"],
        output_dir,
    )
    artifacts.append(artifact("init-env-log", init_result["log"], "log"))
    if init_result["returncode"] != 0 or not shutil.which("docker"):
        return {
            "status": "SKIP" if init_result["returncode"] == 0 else "FAIL",
            "command": f"docker compose --env-file {env_file} -f {compose_file} config --services",
            "composeFiles": [compose_file],
            "services": [],
        }, artifacts

    services_result = run_command(
        "compose-services",
        ["docker", "compose", "--env-file", str(env_file), "-f", compose_file, "config", "--services"],
        output_dir,
    )
    artifacts.append(artifact("compose-services-log", services_result["log"], "log"))
    services = [
        line.strip()
        for line in services_result["log"].read_text().splitlines()
        if line.strip() and not line.startswith("time=")
    ]
    return {
        "status": services_result["status"],
        "command": services_result["command"],
        "composeFiles": [compose_file],
        "services": services,
    }, artifacts


def build_memory_isolation(simulation_report: dict[str, Any] | None) -> dict[str, Any]:
    if not simulation_report:
        return {"status": "FAIL", "checks": {"simulationReportPresent": "FAIL"}}
    canaries = simulation_report.get("memoryCanaries")
    if isinstance(canaries, dict) and isinstance(canaries.get("checks"), list):
        checks = {
            str(item.get("name")): item.get("status", "UNKNOWN")
            for item in canaries["checks"]
            if isinstance(item, dict) and item.get("name")
        }
        return {
            "status": canaries.get("status", "UNKNOWN"),
            "checks": checks or {"memoryCanariesPresent": "FAIL"},
        }
    raw_checks = simulation_report.get("checks")
    if isinstance(raw_checks, dict):
        checks = {key: "PASS" if value is True else "FAIL" for key, value in raw_checks.items()}
        return {"status": "PASS" if all(value == "PASS" for value in checks.values()) else "FAIL", "checks": checks}
    return {"status": "FAIL", "checks": {"memoryCanariesPresent": "FAIL"}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".artifacts" / "node-proof" / timestamp())
    parser.add_argument("--target-kind", default="simulation", choices=["simulation", "local-vm", "staging-vps", "live-vps"])
    parser.add_argument("--target-name", default="simulated-vps-bootstrap")
    parser.add_argument("--environment", default="local")
    args = parser.parse_args()

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    command_results = [
        run_command("doctor-agent-env", ["bash", "scripts/doctor-agent-env.sh"], output_dir),
        run_command("validate-repo", ["bash", "scripts/validate-repo.sh"], output_dir),
        run_command(
            "simulate-vps-bootstrap",
            ["bash", "scripts/simulate-vps-bootstrap.sh"],
            output_dir,
            env={"ARTIFACT_DIR": str(ROOT / ".artifacts" / "vps-simulation")},
        ),
    ]
    compose, compose_artifacts = collect_compose(output_dir)

    simulation_path = ROOT / ".artifacts" / "vps-simulation" / "simulated-vps-bootstrap-report.json"
    simulation_parse_error = None
    simulation_report = None
    if simulation_path.exists():
        try:
            simulation_report = json.loads(simulation_path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            simulation_parse_error = f"failed to parse {simulation_path}: {exc}"
    command_artifacts = [artifact(result["name"], result["log"], "log") for result in command_results]
    artifacts = command_artifacts + compose_artifacts
    if simulation_path.exists():
        simulation_snapshot = output_dir / "simulated-vps-bootstrap-report.json"
        shutil.copy2(simulation_path, simulation_snapshot)
        artifacts.append(artifact("simulated-vps-bootstrap-report", simulation_snapshot, "json"))

    redaction = check_redaction([Path(item["path"]) if Path(item["path"]).is_absolute() else ROOT / item["path"] for item in artifacts])
    command_status = "PASS" if all(result["returncode"] == 0 for result in command_results) else "FAIL"
    memory_isolation = build_memory_isolation(simulation_report)
    if simulation_parse_error:
        memory_isolation["checks"]["simulationReportJsonValid"] = "FAIL"
    result_status = "PASS" if command_status == "PASS" and compose["status"] in {"PASS", "SKIP"} and memory_isolation["status"] == "PASS" and redaction["status"] == "PASS" else "FAIL"

    proof = {
        "schemaVersion": "studio54.node-proof.v1",
        "generatedAt": utc_now(),
        "git": {
            "sha": git_output("rev-parse", "--short=12", "HEAD"),
            "branch": git_output("branch", "--show-current") or "detached",
            "dirty": bool(subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).strip()),
        },
        "target": {
            "kind": args.target_kind,
            "name": args.target_name,
            "host": socket.gethostname(),
            "environment": args.environment,
        },
        "redaction": redaction,
        "compose": compose,
        "services": {
            "prototype-local": {
                "status": command_status,
                "health": "standard repo validation and simulation completed",
            }
        },
        "paperclip": {
            "status": "SKIP",
            "companyId": "",
            "managerAgentId": "",
            "workerAgentIds": [],
            "proofSummary": {
                "parentIssue": "SKIP",
                "childIssues": "SKIP",
                "assignment": "SKIP",
                "comments": "SKIP",
                "finalStatus": "SKIP",
                "runawayChildren": "SKIP",
            },
        },
        "hermes": {
            "status": memory_isolation["status"],
            "path": "hermes_local",
            "mode": "simulated per-company Hermes home preparation",
            "runIds": [],
        },
        "memoryIsolation": memory_isolation,
        "traceability": {"status": "SKIP"},
        "artifacts": artifacts,
        "result": {
            "status": result_status,
            "summary": "Node proof collected from existing local verifier commands.",
        },
    }

    proof_path = output_dir / "proof.json"
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    print(proof_path)
    return 0 if result_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
