#!/usr/bin/env python3
"""Render a non-executing Kanban plan for completing Paperclip proofs.

This program never calls Kanban, Paperclip, n8n, Docker, or the network. It
produces a deterministic plan that an operator may review before creating any
cards. Canary tasks remain disabled unless an explicit company scope and
positive mutation budget are provided.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "studio54.paperclip-kanban-proof-plan.v1"
REQUIRED_CANARY_MUTATION_BUDGET = 12


def task(
    task_id: str,
    title: str,
    assignee_role: str,
    *,
    parents: list[str] | None = None,
    mutation_class: str = "read-only",
    estimated_mutations: int = 0,
    acceptance: list[str],
    evidence: list[str],
) -> dict[str, Any]:
    return {
        "id": task_id,
        "title": title,
        "assigneeRole": assignee_role,
        "parents": parents or [],
        "mutationClass": mutation_class,
        "estimatedMutations": estimated_mutations,
        "humanApprovalRequired": mutation_class == "canary",
        "acceptanceCriteria": acceptance,
        "evidenceRequired": evidence,
    }


def build_tasks() -> list[dict[str, Any]]:
    preflight = [
        task(
            "inventory-paperclip",
            "Inventory live Paperclip proof estate without mutations",
            "paperclip-auditor",
            acceptance=[
                "health, company, agent, issue, goal, project, routine, approval, and org counts captured",
                "no POST, PUT, PATCH, or DELETE request issued",
                "historical fixtures classified separately from operating companies",
            ],
            evidence=["redacted inventory JSON", "HTTP status summary", "mutation count equals zero"],
        ),
        task(
            "reconcile-proof-history",
            "Reconcile Studio54 proof history with live Paperclip records",
            "architecture-researcher",
            acceptance=[
                "proven, partial, planned, and contradicted claims labeled",
                "direct hermes_local identified as the current baseline",
                "formal reportsTo tree not inferred from parent-child issues",
            ],
            evidence=["source-path citation list", "fixture-to-commit mapping", "GREEN/YELLOW/RED table"],
        ),
        task(
            "check-kanban-capabilities",
            "Verify local Kanban dispatcher, board, and profile prerequisites",
            "kanban-operator",
            acceptance=[
                "board and gateway-dispatcher state recorded",
                "assignee roles mapped only to installed profiles",
                "single-host and tenant boundaries acknowledged",
            ],
            evidence=["board status", "profile roster", "dispatcher diagnostic"],
        ),
        task(
            "check-memory-topology",
            "Inspect outer and company memory topology prerequisites",
            "memory-auditor",
            acceptance=[
                "outer Hermes home is not a company home",
                "company home and Honcho workspace expectations documented",
                "manager-worker shared-home caveat recorded",
            ],
            evidence=["redacted path relation report", "Honcho health status", "isolation canary plan"],
        ),
        task(
            "check-proof-tooling",
            "Validate Studio54 proof scripts and schemas",
            "proof-engineer",
            acceptance=[
                "repo-owned proof scripts compile",
                "read-only coordination verifier behavior confirmed",
                "missing production gates enumerated",
            ],
            evidence=["test commands and exit codes", "schema gap list", "redaction scan result"],
        ),
    ]
    synthesis = task(
        "synthesize-readiness",
        "Synthesize Paperclip production-readiness preflight",
        "proof-orchestrator",
        parents=[item["id"] for item in preflight],
        acceptance=[
            "every preflight lane has evidence",
            "YELLOW and RED gates remain explicit",
            "canary mutation scope proposed but not executed",
        ],
        evidence=["readiness report", "risk register", "recommended mutation budget"],
    )
    approval = task(
        "approval-gate",
        "Obtain explicit human approval for disposable Paperclip canary",
        "human-board",
        parents=["synthesize-readiness"],
        mutation_class="canary",
        acceptance=[
            "approved company name recorded",
            "positive mutation budget recorded",
            "public, financial, outreach, and irreversible actions excluded",
        ],
        evidence=["approval record", "approved scope", "mutation budget"],
    )
    canary = [
        task(
            "bootstrap-formal-org",
            "Bootstrap disposable CEO-manager-worker formal org canary",
            "paperclip-operator",
            parents=["approval-gate"],
            mutation_class="canary",
            estimated_mutations=4,
            acceptance=[
                "one CEO root with reportsTo null",
                "manager reports to CEO and worker reports to manager",
                "company-scoped Hermes home exists",
            ],
            evidence=["company and agent IDs", "org endpoint snapshot", "redacted runtime-home manifest"],
        ),
        task(
            "prove-delegation",
            "Prove manager-worker delegation and issue completion",
            "paperclip-manager",
            parents=["approval-gate", "bootstrap-formal-org"],
            mutation_class="canary",
            estimated_mutations=3,
            acceptance=[
                "manager creates linked unassigned backlog child before activation",
                "worker closes child with attributed completion evidence",
                "manager wakes and closes parent without duplicate children",
            ],
            evidence=["parent-child issue snapshot", "comments and run IDs", "coordination-proof JSON"],
        ),
        task(
            "prove-approval-recovery",
            "Prove approval and blocked-child recovery paths",
            "governance-tester",
            parents=["approval-gate", "bootstrap-formal-org"],
            mutation_class="canary",
            estimated_mutations=2,
            acceptance=[
                "governed action remains blocked before approval",
                "human resolution wakes the correct company agent",
                "blocked child wakes manager and resumes only after guidance",
            ],
            evidence=["approval lifecycle", "blocked and resumed issue events", "manager wake evidence"],
        ),
        task(
            "prove-retry-idempotency",
            "Prove restart, retry, and idempotent child creation",
            "reliability-tester",
            parents=["approval-gate", "bootstrap-formal-org"],
            mutation_class="canary",
            estimated_mutations=1,
            acceptance=[
                "controlled retry produces no duplicate child",
                "authoritative issue state survives worker restart",
                "stale attempt cannot overwrite accepted completion",
            ],
            evidence=["attempt timeline", "idempotency comparison", "post-restart issue snapshot"],
        ),
    ]
    memory = task(
        "prove-memory-isolation",
        "Prove outer-company and company-company memory isolation",
        "memory-auditor",
        parents=["bootstrap-formal-org"],
        acceptance=[
            "outer sentinel is not recalled inside canary company",
            "canary sentinel is not recalled by outer Hermes or another company",
            "Honcho workspace and peer mapping match approved scope",
        ],
        evidence=["sentinel matrix", "redacted workspace mapping", "Honcho health evidence"],
    )
    verify = task(
        "verify-canary",
        "Verify and synthesize the complete Paperclip canary",
        "proof-reviewer",
        parents=[item["id"] for item in canary] + ["prove-memory-isolation"],
        acceptance=[
            "all required gates are GREEN or explicitly block production",
            "artifacts pass redaction and correlation checks",
            "result can be reconstructed without raw transcripts",
        ],
        evidence=["final proof JSON", "verification report", "production go-no-go recommendation"],
    )
    productive = task(
        "pilot-1215-inventory",
        "Generate one redacted 1215 current-state inventory",
        "proof-engineer",
        parents=["approval-gate", "verify-canary"],
        mutation_class="canary",
        estimated_mutations=2,
        acceptance=[
            "one useful redacted current-state inventory accepted",
            "service health, canary topology, and exact verification commands recorded",
            "no runtime configuration, publication, performer outreach, spending, or irreversible action",
        ],
        evidence=["inventory artifact", "command/status manifest", "pilot metrics", "human acceptance"],
    )
    return [*preflight, synthesis, approval, *canary, memory, verify, productive]


def build_plan(
    mode: str,
    approved_company: str | None,
    mutation_budget: int,
    approval_id: str | None,
    manifest_sha256: str | None,
    approval_expires_at: str | None,
) -> dict[str, Any]:
    tasks = build_tasks()
    canary_mode = mode == "canary"
    estimated_mutations = sum(item["estimatedMutations"] for item in tasks)
    eligibility: dict[str, bool] = {}
    for item in tasks:
        mode_allows = item["mutationClass"] == "read-only" or canary_mode
        parents_allow = all(eligibility.get(parent, False) for parent in item["parents"])
        item["executionEligible"] = mode_allows and parents_allow
        eligibility[item["id"]] = item["executionEligible"]
    return {
        "schema": SCHEMA,
        "mode": mode,
        "approvedCompany": approved_company,
        "mutationBudget": mutation_budget,
        "estimatedMutations": estimated_mutations,
        "budgetRemaining": mutation_budget - estimated_mutations if canary_mode else 0,
        "approval": {
            "id": approval_id,
            "manifestSha256": manifest_sha256,
            "expiresAt": approval_expires_at,
        },
        "executionPolicy": {
            "executesTasks": False,
            "networkAccess": False,
            "defaultMutationPolicy": "deny",
            "publicActions": "prohibited",
        },
        "tasks": tasks,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["read-only", "canary"], default="read-only")
    parser.add_argument("--approved-company")
    parser.add_argument("--mutation-budget", type=int, default=0)
    parser.add_argument("--approval-id")
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--approval-expires-at")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "canary":
        if not args.approved_company:
            parser.error("--approved-company is required in canary mode")
        if args.mutation_budget < REQUIRED_CANARY_MUTATION_BUDGET:
            parser.error(
                "--mutation-budget must be at least "
                f"{REQUIRED_CANARY_MUTATION_BUDGET} for the complete canary plan"
            )
        if not args.approval_id:
            parser.error("--approval-id is required in canary mode")
        if not args.manifest_sha256 or not re.fullmatch(r"[0-9a-fA-F]{64}", args.manifest_sha256):
            parser.error("--manifest-sha256 must be a 64-character hexadecimal SHA-256 in canary mode")
        if not args.approval_expires_at:
            parser.error("--approval-expires-at is required in canary mode")
        try:
            expires = datetime.fromisoformat(args.approval_expires_at.replace("Z", "+00:00"))
        except ValueError:
            parser.error("--approval-expires-at must be an RFC3339 timestamp")
        if expires.tzinfo is None or expires <= datetime.now(timezone.utc):
            parser.error("--approval-expires-at must be a future timezone-aware timestamp")
    elif any(
        (
            args.approved_company,
            args.mutation_budget,
            args.approval_id,
            args.manifest_sha256,
            args.approval_expires_at,
        )
    ):
        parser.error("canary scope arguments require --mode canary")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    plan = build_plan(
        args.mode,
        args.approved_company,
        args.mutation_budget,
        args.approval_id,
        args.manifest_sha256,
        args.approval_expires_at,
    )
    rendered = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
