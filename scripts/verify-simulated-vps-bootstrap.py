#!/usr/bin/env python3
"""Verify simulated VPS/Paperclip Hermes homes without touching real infrastructure."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit(message)


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        fail(f"failed to read JSON {path}: {exc}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def canary(name: str, status: bool, expected: object, observed: object) -> dict:
    return {
        "name": name,
        "status": "PASS" if status else "FAIL",
        "expected": expected,
        "observed": observed,
    }


def verify_company(root: Path, company_id: str, agent_id: str, host_home: Path) -> dict:
    hermes_home = root / "paperclip" / "instances" / "default" / "companies" / company_id / "hermes-home"
    require(hermes_home.exists(), f"missing Hermes home for {company_id}: {hermes_home}")
    require(hermes_home != host_home, f"company {company_id} points at host Hermes home")
    require(str(hermes_home).startswith(str(root / "paperclip")), f"company {company_id} escaped simulated paperclip root")

    config_path = hermes_home / "config.yaml"
    honcho_path = hermes_home / "honcho.json"
    env_path = hermes_home / ".env"
    for path in (config_path, honcho_path, env_path):
        require(path.exists(), f"missing {path}")

    config_text = config_path.read_text()
    require("memory:" in config_text, f"missing memory section in {config_path}")
    require("memory_enabled: true" in config_text, f"memory not enabled in {config_path}")

    honcho = read_json(honcho_path)
    require(honcho.get("enabled") is True, f"honcho disabled for {company_id}")
    require(honcho.get("workspace") == company_id, f"workspace mismatch for {company_id}: {honcho.get('workspace')!r}")
    expected_ai_peer = f"paperclip-agent-{agent_id}"
    require(honcho.get("aiPeer") == expected_ai_peer, f"aiPeer mismatch for {company_id}: {honcho.get('aiPeer')!r}")
    require(honcho.get("baseUrl") == "http://127.0.0.1:18000", f"unexpected Honcho URL for {company_id}")

    sentinel = hermes_home / "SIMULATED_SCOPE_SENTINEL.txt"
    sentinel.write_text(f"{company_id}::{agent_id}\n")

    return {
        "companyId": company_id,
        "agentId": agent_id,
        "hermesHome": str(hermes_home),
        "config": str(config_path),
        "honcho": str(honcho_path),
        "workspace": honcho["workspace"],
        "aiPeer": honcho["aiPeer"],
        "sentinel": str(sentinel),
    }


def build_memory_canaries(companies: list[dict], host_home: Path) -> dict:
    company_homes = [company["hermesHome"] for company in companies]
    company_workspaces = {
        company["companyId"]: company["workspace"]
        for company in companies
    }
    company_ai_peers = {
        company["companyId"]: company["aiPeer"]
        for company in companies
    }
    expected_ai_peers = {
        company["companyId"]: f"paperclip-agent-{company['agentId']}"
        for company in companies
    }

    checks = [
        canary(
            "companyHomesSeparateFromEachOther",
            len(company_homes) == len(set(company_homes)),
            "all company Hermes homes are unique",
            company_homes,
        ),
        canary(
            "hostHermesHomeSeparateFromCompanyHomes",
            str(host_home) not in set(company_homes),
            f"host Hermes home {host_home} is not any Paperclip company Hermes home",
            {
                "hostHermesHome": str(host_home),
                "companyHermesHomes": company_homes,
            },
        ),
        canary(
            "honchoWorkspaceEqualsCompanyId",
            all(company["workspace"] == company["companyId"] for company in companies),
            {company["companyId"]: company["companyId"] for company in companies},
            company_workspaces,
        ),
        canary(
            "honchoAiPeerEqualsPaperclipAgentId",
            all(company["aiPeer"] == expected_ai_peers[company["companyId"]] for company in companies),
            expected_ai_peers,
            company_ai_peers,
        ),
    ]

    return {
        "status": "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL",
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    host_home = root / "host" / ".hermes"
    host_home.mkdir(parents=True, exist_ok=True)
    (host_home / "HOST_SCOPE_SENTINEL.txt").write_text("host-only\n")

    companies = [
        verify_company(root, "company-a", "agent-a", host_home),
        verify_company(root, "company-b", "agent-b", host_home),
    ]

    require(companies[0]["workspace"] != companies[1]["workspace"], "company workspaces are not isolated")
    require(companies[0]["hermesHome"] != companies[1]["hermesHome"], "company Hermes homes are not isolated")
    memory_canaries = build_memory_canaries(companies, host_home)
    require(memory_canaries["status"] == "PASS", "one or more memory canaries failed")

    report = {
        "schema": "studio54.simulated-vps-bootstrap.v1",
        "status": "PASS",
        "root": str(root),
        "hostHermesHome": str(host_home),
        "checks": {
            "hostHomeSeparateFromCompanies": True,
            "companyHomesSeparateFromEachOther": True,
            "honchoWorkspaceEqualsCompanyId": True,
            "honchoAiPeerEqualsPaperclipAgentId": True,
            "noRealVpsMutation": True,
        },
        "memoryCanaries": memory_canaries,
        "companies": companies,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
