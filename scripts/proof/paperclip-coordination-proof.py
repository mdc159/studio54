#!/usr/bin/env python3
"""Collect a Paperclip manager/worker coordination proof.

This script is intended for staging/live proof runs, not for every PR. It uses
read-only Paperclip API calls by default and writes a JSON proof summary.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, parse, request


TERMINAL_STATUSES = {"done", "cancelled"}
NOISE_MARKERS = (
    "process_lost",
    "retried dispatch",
    "retried continuation",
    "latest retry failure",
    "[openclaw-gateway:event]",
    "traceback (most recent call last)",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_api_base(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if not normalized.endswith("/api"):
        normalized = f"{normalized}/api"
    return normalized


def non_empty(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def issue_id(issue: dict[str, Any]) -> str:
    return non_empty(issue.get("id")) or non_empty(issue.get("identifier")) or "<unknown>"


def issue_created_at(issue: dict[str, Any]) -> str:
    return non_empty(issue.get("createdAt")) or non_empty(issue.get("updatedAt")) or ""


class PaperclipClient:
    def __init__(self, base_url: str, token: str | None, timeout: float) -> None:
        self.base_url = normalize_api_base(base_url)
        self.token = token
        self.timeout = timeout

    def get(self, path: str, query: dict[str, str] | None = None) -> Any:
        suffix = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{suffix}"
        if query:
            url = f"{url}?{parse.urlencode(query)}"
        headers = {"accept": "application/json"}
        if self.token:
            headers["authorization"] = f"Bearer {self.token}"
        req = request.Request(url, headers=headers, method="GET")
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GET {url} failed: HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"GET {url} failed: {exc}") from exc
        return json.loads(body) if body else None


def check(name: str, passed: bool, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "status": "PASS" if passed else "FAIL",
        "details": details or {},
    }


def list_issues(client: PaperclipClient, company_id: str, query: dict[str, str]) -> list[dict[str, Any]]:
    payload = client.get(f"/companies/{parse.quote(company_id)}/issues", query)
    if not isinstance(payload, list):
        raise RuntimeError("Paperclip issues list response was not an array")
    return [item for item in payload if isinstance(item, dict)]


def list_comments(client: PaperclipClient, issue: dict[str, Any]) -> list[dict[str, Any]]:
    payload = client.get(f"/issues/{parse.quote(issue_id(issue))}/comments")
    if not isinstance(payload, list):
        raise RuntimeError(f"Paperclip comments response was not an array for {issue_id(issue)}")
    return [item for item in payload if isinstance(item, dict)]


def list_runs(client: PaperclipClient, issue: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        payload = client.get(f"/issues/{parse.quote(issue_id(issue))}/runs")
    except RuntimeError:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def select_parent_issue(
    client: PaperclipClient,
    company_id: str,
    manager_agent_id: str,
    parent_issue_id: str | None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if parent_issue_id:
        parent = client.get(f"/issues/{parse.quote(parent_issue_id)}")
        if not isinstance(parent, dict):
            raise RuntimeError(f"parent issue {parent_issue_id} response was not an object")
        children = list_issues(client, company_id, {"parentId": issue_id(parent)})
        return parent, children

    candidates = list_issues(client, company_id, {"assigneeAgentId": manager_agent_id})
    candidates.sort(key=issue_created_at, reverse=True)
    if not candidates:
        raise RuntimeError("could not infer parent issue: no manager-assigned issues found")
    parent = candidates[0]
    children = list_issues(client, company_id, {"parentId": issue_id(parent)})
    return parent, children


def collect_run_ids(*collections: list[dict[str, Any]]) -> list[str]:
    found: set[str] = set()
    keys = ("runId", "run_id", "paperclipRunId", "hermesRunId", "langfuseTraceId")
    for collection in collections:
        for item in collection:
            for key in keys:
                value = non_empty(item.get(key))
                if value:
                    found.add(value)
            metadata = item.get("metadata") or item.get("metadataJson") or item.get("metadata_json")
            if isinstance(metadata, dict):
                for key in keys:
                    value = non_empty(metadata.get(key))
                    if value:
                        found.add(value)
    return sorted(found)


def comment_body(comment: dict[str, Any]) -> str:
    body = comment.get("body")
    return body if isinstance(body, str) else ""


def has_noise(comments: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    noisy: list[str] = []
    for comment in comments:
        body = comment_body(comment).lower()
        if any(marker in body for marker in NOISE_MARKERS):
            noisy.append(non_empty(comment.get("id")) or comment_body(comment)[:80])
    return bool(noisy), noisy


def build_proof(args: argparse.Namespace) -> dict[str, Any]:
    client = PaperclipClient(args.paperclip_base_url, args.api_token, args.timeout)
    worker_ids = [worker.strip() for worker in args.worker_agent_id if worker.strip()]
    max_child_issues = args.max_child_issues if args.max_child_issues is not None else max(1, len(worker_ids))

    parent, children = select_parent_issue(client, args.company_id, args.manager_agent_id, args.parent_issue_id)
    parent_comments = list_comments(client, parent)
    child_comments_by_id = {issue_id(child): list_comments(client, child) for child in children}
    parent_runs = list_runs(client, parent)
    child_runs_by_id = {issue_id(child): list_runs(client, child) for child in children}
    all_comments = parent_comments + [comment for comments in child_comments_by_id.values() for comment in comments]
    all_runs = parent_runs + [run for runs in child_runs_by_id.values() for run in runs]

    child_assignments = {
        issue_id(child): non_empty(child.get("assigneeAgentId"))
        for child in children
    }
    child_statuses = {
        issue_id(child): non_empty(child.get("status")) or "unknown"
        for child in children
    }
    child_parent_ids = {
        issue_id(child): non_empty(child.get("parentId"))
        for child in children
    }
    expected_parent_id = issue_id(parent)
    child_assignees = {assignee for assignee in child_assignments.values() if assignee}
    missing_workers = sorted(set(worker_ids) - child_assignees)
    unexpected_workers = sorted(child_assignees - set(worker_ids)) if worker_ids else []
    noisy, noisy_comment_ids = has_noise(all_comments)
    run_ids = collect_run_ids(all_comments, all_runs)

    checks = [
        check(
            "parentIssueShape",
            non_empty(parent.get("companyId")) == args.company_id
            and non_empty(parent.get("assigneeAgentId")) == args.manager_agent_id,
            {
                "parentIssueId": expected_parent_id,
                "companyId": parent.get("companyId"),
                "assigneeAgentId": parent.get("assigneeAgentId"),
                "status": parent.get("status"),
            },
        ),
        check(
            "childIssueShape",
            bool(children) and all(parent_id == expected_parent_id for parent_id in child_parent_ids.values()),
            {
                "childIssueIds": [issue_id(child) for child in children],
                "parentIds": child_parent_ids,
            },
        ),
        check(
            "assignment",
            not missing_workers and not unexpected_workers,
            {
                "expectedWorkerAgentIds": worker_ids,
                "childAssignments": child_assignments,
                "missingWorkerAgentIds": missing_workers,
                "unexpectedWorkerAgentIds": unexpected_workers,
            },
        ),
        check(
            "comments",
            bool(parent_comments) and all(child_comments_by_id.get(issue_id(child)) for child in children),
            {
                "parentCommentCount": len(parent_comments),
                "childCommentCounts": {
                    child_id: len(comments)
                    for child_id, comments in child_comments_by_id.items()
                },
            },
        ),
        check(
            "runIds",
            bool(run_ids),
            {
                "runIds": run_ids,
                "runCount": len(all_runs),
            },
        ),
        check(
            "finalStatus",
            (non_empty(parent.get("status")) in TERMINAL_STATUSES)
            and all(status in TERMINAL_STATUSES for status in child_statuses.values()),
            {
                "parentStatus": parent.get("status"),
                "childStatuses": child_statuses,
                "terminalStatuses": sorted(TERMINAL_STATUSES),
            },
        ),
        check(
            "noRuntimeNoiseComments",
            not noisy,
            {
                "noiseMarkers": list(NOISE_MARKERS),
                "noisyCommentIds": noisy_comment_ids,
            },
        ),
        check(
            "noRunawayChildCreation",
            len(children) <= max_child_issues,
            {
                "childIssueCount": len(children),
                "maxChildIssues": max_child_issues,
            },
        ),
    ]
    status = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"

    return {
        "schema": "studio54.paperclip-coordination-proof.v1",
        "generatedAt": utc_now(),
        "status": status,
        "paperclipBaseUrl": normalize_api_base(args.paperclip_base_url),
        "companyId": args.company_id,
        "managerAgentId": args.manager_agent_id,
        "workerAgentIds": worker_ids,
        "parentIssue": {
            "id": expected_parent_id,
            "identifier": parent.get("identifier"),
            "title": parent.get("title"),
            "status": parent.get("status"),
            "assigneeAgentId": parent.get("assigneeAgentId"),
        },
        "childIssues": [
            {
                "id": issue_id(child),
                "identifier": child.get("identifier"),
                "title": child.get("title"),
                "status": child.get("status"),
                "parentId": child.get("parentId"),
                "assigneeAgentId": child.get("assigneeAgentId"),
            }
            for child in children
        ],
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paperclip-base-url", required=True, help="Paperclip base URL, with or without /api.")
    parser.add_argument("--api-token", default=None, help="Optional Paperclip API bearer token.")
    parser.add_argument("--company-id", required=True)
    parser.add_argument("--manager-agent-id", required=True)
    parser.add_argument("--worker-agent-id", action="append", required=True, help="Worker agent ID. Repeat for multiple workers.")
    parser.add_argument("--parent-issue-id", default=None, help="Optional known parent issue ID/identifier.")
    parser.add_argument("--max-child-issues", type=int, default=None, help="Defaults to number of worker IDs, minimum 1.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--no-fail", action="store_true", help="Write proof JSON but exit 0 even when proof status is FAIL.")
    args = parser.parse_args(argv)

    proof = build_proof(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    print(json.dumps(proof, indent=2, sort_keys=True))
    return 0 if args.no_fail or proof["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
