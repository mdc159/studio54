from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "proof" / "plan-paperclip-kanban-proof.py"
FUTURE_EXPIRY = "2099-01-01T00:00:00Z"
MANIFEST_SHA256 = "a" * 64
CANARY_ARGS = (
    "--mode", "canary",
    "--approved-company", "Paperclip Formal Org Canary",
    "--mutation-budget", "12",
    "--approval-id", "approval-test-001",
    "--manifest-sha256", MANIFEST_SHA256,
    "--approval-expires-at", FUTURE_EXPIRY,
)


def run_plan(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_read_only_plan_is_valid_acyclic_and_transitively_gated() -> None:
    result = run_plan()

    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["schema"] == "studio54.paperclip-kanban-proof-plan.v1"
    assert plan["mode"] == "read-only"
    assert plan["approvedCompany"] is None
    assert plan["mutationBudget"] == 0
    assert plan["approval"] == {"id": None, "manifestSha256": None, "expiresAt": None}

    tasks = plan["tasks"]
    assert tasks
    by_id = {task["id"]: task for task in tasks}
    assert len(by_id) == len(tasks)

    for task in tasks:
        assert task["title"]
        assert task["assigneeRole"]
        assert isinstance(task["parents"], list)
        assert task["mutationClass"] in {"read-only", "canary"}
        assert task["acceptanceCriteria"]
        assert task["evidenceRequired"]
        assert all(parent in by_id for parent in task["parents"])
        if task["estimatedMutations"]:
            assert task["humanApprovalRequired"] is True
            assert "approval-gate" in task["parents"]
        if task["executionEligible"]:
            assert all(by_id[parent]["executionEligible"] for parent in task["parents"])

    assert by_id["approval-gate"]["executionEligible"] is False
    assert by_id["bootstrap-formal-org"]["executionEligible"] is False
    assert by_id["prove-memory-isolation"]["executionEligible"] is False
    assert by_id["verify-canary"]["executionEligible"] is False
    assert by_id["pilot-1215-inventory"]["executionEligible"] is False

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str) -> None:
        assert task_id not in visiting, f"cycle detected at {task_id}"
        if task_id in visited:
            return
        visiting.add(task_id)
        for parent in by_id[task_id]["parents"]:
            visit(parent)
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in by_id:
        visit(task_id)

    synthesis = by_id["synthesize-readiness"]
    assert set(synthesis["parents"]) == {
        "inventory-paperclip",
        "reconcile-proof-history",
        "check-kanban-capabilities",
        "check-memory-topology",
        "check-proof-tooling",
    }

    serialized = result.stdout.lower()
    for forbidden in ("api_key=", "password=", "bearer ", "ghp_", "sk-"):
        assert forbidden not in serialized


def test_canary_mode_requires_complete_durable_scope() -> None:
    missing = run_plan("--mode", "canary")
    assert missing.returncode != 0
    assert "--approved-company" in missing.stderr

    under_budget = run_plan(
        "--mode", "canary", "--approved-company", "Paperclip Formal Org Canary",
        "--mutation-budget", "11",
    )
    assert under_budget.returncode != 0
    assert "at least 12" in under_budget.stderr

    no_approval = run_plan(
        "--mode", "canary", "--approved-company", "Paperclip Formal Org Canary",
        "--mutation-budget", "12",
    )
    assert no_approval.returncode != 0
    assert "--approval-id" in no_approval.stderr

    bad_hash = run_plan(
        "--mode", "canary", "--approved-company", "Paperclip Formal Org Canary",
        "--mutation-budget", "12", "--approval-id", "approval-test-001",
        "--manifest-sha256", "not-a-sha", "--approval-expires-at", FUTURE_EXPIRY,
    )
    assert bad_hash.returncode != 0
    assert "64-character hexadecimal" in bad_hash.stderr

    expired = run_plan(
        "--mode", "canary", "--approved-company", "Paperclip Formal Org Canary",
        "--mutation-budget", "12", "--approval-id", "approval-test-001",
        "--manifest-sha256", MANIFEST_SHA256,
        "--approval-expires-at", "2020-01-01T00:00:00Z",
    )
    assert expired.returncode != 0
    assert "future timezone-aware" in expired.stderr


def test_canary_mode_enables_only_durably_approved_graph() -> None:
    result = run_plan(*CANARY_ARGS)

    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert plan["mode"] == "canary"
    assert plan["approvedCompany"] == "Paperclip Formal Org Canary"
    assert plan["mutationBudget"] == 12
    assert plan["estimatedMutations"] == 12
    assert plan["budgetRemaining"] == 0
    assert plan["approval"] == {
        "id": "approval-test-001",
        "manifestSha256": MANIFEST_SHA256,
        "expiresAt": FUTURE_EXPIRY,
    }
    mutation_tasks = [task for task in plan["tasks"] if task["estimatedMutations"]]
    assert sum(task["estimatedMutations"] for task in mutation_tasks) == plan["estimatedMutations"]
    assert mutation_tasks
    assert all(task["executionEligible"] is True for task in plan["tasks"])
    assert all(task["humanApprovalRequired"] is True for task in mutation_tasks)


def test_output_file_matches_stdout(tmp_path: Path) -> None:
    output = tmp_path / "plan.json"
    result = run_plan("--output", str(output))

    assert result.returncode == 0, result.stderr
    assert output.exists()
    assert json.loads(output.read_text()) == json.loads(result.stdout)
