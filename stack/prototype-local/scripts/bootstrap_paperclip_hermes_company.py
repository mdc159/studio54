#!/usr/bin/env python3
"""Bootstrap a Paperclip company for the direct hermes_local path."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error, request

from init_env import parse_env_assignments
from prepare_paperclip_hermes_home import (
    DEFAULT_INSTANCE_ID,
    DEFAULT_SOURCE,
    DEFAULT_SOURCE_FALLBACK,
)
from project_hermes_runtime import DEFAULT_HERMES_MODEL


DEFAULT_BASE_URL = "http://127.0.0.1:3100"
DEFAULT_COMPANY_DESCRIPTION = "One-agent Paperclip company using direct per-company hermes_local."
DEFAULT_AGENT_NAME = "Direct Hermes Operator"
DEFAULT_AGENT_ROLE = "general"
DEFAULT_AGENT_TITLE = "Operator"
DEFAULT_ISSUE_TITLE = "Validate direct hermes_local company bootstrap"
DEFAULT_ISSUE_BODY = """Validate this one-agent company bootstrap on the active direct hermes_local path.

Post one concise final completion comment that includes:
1. the active HERMES_HOME
2. whether config.yaml exists
3. whether honcho.json exists
4. whether this issue completed through the direct-path final PATCH contract

Do not create subtasks.
Do not modify infrastructure.
Close this issue explicitly through one final PATCH containing status "done" and the completion comment.
"""
DEFAULT_TOPOLOGY = "one-agent"
DEFAULT_MANAGER_NAME = "Direct Hermes Manager"
DEFAULT_MANAGER_ROLE = "general"
DEFAULT_MANAGER_TITLE = "Manager"
DEFAULT_WORKER_NAME = "Direct Hermes Worker"
DEFAULT_WORKER_ROLE = "general"
DEFAULT_WORKER_TITLE = "Worker"
DEFAULT_MANAGER_WORKER_ISSUE_TITLE = "Validate manager worker direct hermes_local bootstrap"
DEFAULT_MANAGER_WORKER_ISSUE_BODY = """Validate this manager/worker company bootstrap on the active direct hermes_local path.

Worker agent:
- name: {worker_name}
- id: {worker_id}

Manager responsibilities:
1. Create exactly one delegated child issue assigned to the worker agent above.
2. The child issue must be bounded and ask the worker to report this one requirement: both bootstrapped agents use adapterType hermes_local and the same company-scoped HERMES_HOME.
3. Link the child to this parent issue. If Paperclip exposes this issue id in the task context, send it as parentId when creating the child.
4. Do not create more than one child issue.
5. Do not modify infrastructure.
6. On the first run, after creating the child issue, post at most one PENDING comment and stop. Do not keep polling or waiting inside the same run.
7. Do not close this parent issue until the worker child issue is done.
8. When woken after the worker child is done, post one concise final completion comment on this parent issue containing:
   - the worker finding
   - whether the child issue was linked to this parent
   - whether the manager/worker lifecycle completed correctly
9. Close this parent explicitly through one final PATCH containing status "done" and the completion comment.
10. After the final PATCH succeeds, stop. Do not post additional comments or continue working.

Worker task requirement:
- post one concise final completion comment
- close the worker issue explicitly through one final PATCH containing status "done" and the completion comment
- do not create subtasks
- do not modify infrastructure
- after the final PATCH succeeds, stop
"""


def api_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def json_request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: float = 30.0,
) -> Any:
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = request.Request(api_url(base_url, path), method=method, data=data, headers=headers)
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else None
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8") if hasattr(exc, "read") else ""
        try:
            parsed: Any = json.loads(body) if body else None
        except json.JSONDecodeError:
            parsed = body
        raise SystemExit(f"{method} {path} failed with HTTP {exc.code}: {parsed!r}") from exc


def wait_for_paperclip(base_url: str, *, token: str | None, timeout_seconds: int) -> dict[str, Any]:
    deadline = time.time() + timeout_seconds
    last_error: str | None = None
    while time.time() < deadline:
        try:
            health = json_request(base_url, "/api/health", token=token, timeout=5.0)
            if isinstance(health, dict):
                return health
            return {"raw": health}
        except SystemExit as exc:
            last_error = str(exc)
        except Exception as exc:  # noqa: BLE001 - report the last startup failure.
            last_error = str(exc)
        time.sleep(2)
    raise SystemExit(f"timed out waiting for Paperclip health at {base_url}/api/health; last error: {last_error}")


def as_list(value: Any, *, name: str) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("items", "companies", "agents", "issues"):
            items = value.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
    raise SystemExit(f"unexpected {name} response shape: {value!r}")


def find_one_by_name(rows: list[dict[str, Any]], name: str, *, entity: str) -> dict[str, Any] | None:
    matches = [row for row in rows if row.get("name") == name]
    if len(matches) > 1:
        ids = ", ".join(str(row.get("id")) for row in matches)
        raise SystemExit(f"found multiple {entity}s named {name!r}; refusing to choose hidden duplicate: {ids}")
    return matches[0] if matches else None


def find_or_create_company(
    base_url: str,
    *,
    token: str | None,
    name: str,
    description: str | None,
    budget_monthly_cents: int,
) -> tuple[dict[str, Any], bool]:
    companies = as_list(json_request(base_url, "/api/companies", token=token), name="companies")
    existing = find_one_by_name(companies, name, entity="company")
    if existing:
        return existing, False

    payload = {
        "name": name,
        "description": description,
        "budgetMonthlyCents": budget_monthly_cents,
    }
    created = json_request(base_url, "/api/companies", method="POST", payload=payload, token=token)
    if not isinstance(created, dict) or not created.get("id"):
        raise SystemExit(f"unexpected create company response: {created!r}")
    return created, True


def source_values(source: Path | None) -> dict[str, str]:
    source_path = source.resolve() if source else (DEFAULT_SOURCE if DEFAULT_SOURCE.exists() else DEFAULT_SOURCE_FALLBACK)
    if not source_path.exists():
        raise SystemExit(f"missing source env: {source_path}")
    return parse_env_assignments(source_path.read_text())


def instance_id(values: dict[str, str], override: str | None) -> str:
    return (override or "").strip() or values.get("PAPERCLIP_INSTANCE_ID", "").strip() or DEFAULT_INSTANCE_ID


def container_hermes_home(company_id: str, *, container_paperclip_home: str, instance: str) -> str:
    root = container_paperclip_home.rstrip("/") or "/paperclip"
    return f"{root}/instances/{instance}/companies/{company_id}/hermes-home"


def run_prepare(
    *,
    company_id: str,
    agent_id: str | None,
    source: Path | None,
    instance: str | None,
) -> dict[str, str]:
    script = Path(__file__).resolve().with_name("prepare_paperclip_hermes_home.py")
    cmd = [sys.executable, str(script), "--company-id", company_id]
    if agent_id:
        cmd.extend(["--agent-id", agent_id])
    if source:
        cmd.extend(["--source", str(source.resolve())])
    if instance:
        cmd.extend(["--instance-id", instance])
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(
            "prepare_paperclip_hermes_home.py failed\n"
            f"command: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) < 4:
        raise SystemExit(f"unexpected prepare output: {result.stdout!r}")
    return {
        "hostHermesHome": lines[0],
        "hostEnvPath": lines[1],
        "hostConfigPath": lines[2],
        "hostHonchoPath": lines[3],
    }


def env_binding_value(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and value.get("type") == "plain" and isinstance(value.get("value"), str):
        return value["value"]
    return None


def validate_existing_agent(agent: dict[str, Any], *, model: str, hermes_home: str) -> None:
    if agent.get("adapterType") != "hermes_local":
        raise SystemExit(
            f"agent {agent.get('id')} exists but adapterType is {agent.get('adapterType')!r}, not 'hermes_local'"
        )
    adapter_config = agent.get("adapterConfig")
    if not isinstance(adapter_config, dict):
        raise SystemExit(f"agent {agent.get('id')} has invalid adapterConfig: {adapter_config!r}")
    if adapter_config.get("model") != model:
        raise SystemExit(
            f"agent {agent.get('id')} exists with model {adapter_config.get('model')!r}; expected {model!r}"
        )
    env = adapter_config.get("env")
    if not isinstance(env, dict) or env_binding_value(env.get("HERMES_HOME")) != hermes_home:
        raise SystemExit(
            f"agent {agent.get('id')} exists with HERMES_HOME {env_binding_value(env.get('HERMES_HOME'))!r}; "
            f"expected {hermes_home!r}"
        )


def find_or_create_agent(
    base_url: str,
    *,
    token: str | None,
    company_id: str,
    name: str,
    role: str,
    title: str | None,
    model: str,
    hermes_home: str,
) -> tuple[dict[str, Any], bool]:
    agents = as_list(json_request(base_url, f"/api/companies/{company_id}/agents", token=token), name="agents")
    existing = find_one_by_name(agents, name, entity="agent")
    if existing:
        validate_existing_agent(existing, model=model, hermes_home=hermes_home)
        return existing, False

    payload = {
        "name": name,
        "role": role,
        "title": title,
        "adapterType": "hermes_local",
        "adapterConfig": {
            "model": model,
            "env": {
                "HERMES_HOME": {
                    "type": "plain",
                    "value": hermes_home,
                },
            },
        },
    }
    created = json_request(
        base_url,
        f"/api/companies/{company_id}/agents",
        method="POST",
        payload=payload,
        token=token,
    )
    if not isinstance(created, dict) or not created.get("id"):
        raise SystemExit(f"unexpected create agent response: {created!r}")
    return created, True


def open_issue_matches(issue: dict[str, Any], *, title: str, agent_id: str) -> bool:
    return (
        issue.get("title") == title
        and issue.get("assigneeAgentId") == agent_id
        and issue.get("status") not in ("done", "cancelled")
    )


def find_or_create_validation_issue(
    base_url: str,
    *,
    token: str | None,
    company_id: str,
    agent_id: str,
    title: str,
    body: str,
    always_create: bool,
) -> tuple[dict[str, Any], bool]:
    if not always_create:
        issues = as_list(json_request(base_url, f"/api/companies/{company_id}/issues", token=token), name="issues")
        matches = [issue for issue in issues if open_issue_matches(issue, title=title, agent_id=agent_id)]
        if len(matches) > 1:
            ids = ", ".join(str(issue.get("identifier") or issue.get("id")) for issue in matches)
            raise SystemExit(f"found multiple open validation issues titled {title!r}; refusing to choose: {ids}")
        if matches:
            return matches[0], False

    payload = {
        "title": title,
        "description": body,
        "status": "todo",
        "priority": "medium",
        "assigneeAgentId": agent_id,
    }
    created = json_request(
        base_url,
        f"/api/companies/{company_id}/issues",
        method="POST",
        payload=payload,
        token=token,
    )
    if not isinstance(created, dict) or not created.get("id"):
        raise SystemExit(f"unexpected create issue response: {created!r}")
    return created, True


def agent_summary(agent: dict[str, Any], *, created: bool, model: str) -> dict[str, Any]:
    return {
        "id": agent.get("id"),
        "name": agent.get("name"),
        "role": agent.get("role"),
        "title": agent.get("title"),
        "created": created,
        "adapterType": agent.get("adapterType"),
        "model": model,
    }


def read_honcho_ai_peer(host_honcho_path: str) -> str | None:
    path = Path(host_honcho_path)
    if not path.exists():
        return None
    try:
        parsed = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    value = parsed.get("aiPeer")
    return value if isinstance(value, str) else None


def render_manager_worker_issue_body(
    template: str,
    *,
    manager_name: str,
    manager_id: str,
    worker_name: str,
    worker_id: str,
) -> str:
    replacements = {
        "{manager_name}": manager_name,
        "{manager_id}": manager_id,
        "{worker_name}": worker_name,
        "{worker_id}": worker_id,
    }
    rendered = template
    for needle, value in replacements.items():
        rendered = rendered.replace(needle, value)
    return rendered


def bootstrap_one_agent(args: argparse.Namespace, *, values: dict[str, str], model: str, issue_body: str) -> dict[str, Any]:
    resolved_instance_id = instance_id(values, args.instance_id)
    health = wait_for_paperclip(args.base_url, token=args.api_token, timeout_seconds=args.health_timeout)
    company, company_created = find_or_create_company(
        args.base_url,
        token=args.api_token,
        name=args.company_name,
        description=args.company_description,
        budget_monthly_cents=args.budget_monthly_cents,
    )
    company_id = str(company["id"])
    hermes_home = container_hermes_home(
        company_id,
        container_paperclip_home=args.container_paperclip_home,
        instance=resolved_instance_id,
    )
    initial_prepare = run_prepare(
        company_id=company_id,
        agent_id=None,
        source=args.source,
        instance=args.instance_id,
    )
    agent, agent_created = find_or_create_agent(
        args.base_url,
        token=args.api_token,
        company_id=company_id,
        name=args.agent_name,
        role=args.agent_role,
        title=args.agent_title,
        model=model,
        hermes_home=hermes_home,
    )
    agent_id = str(agent["id"])
    final_prepare = run_prepare(
        company_id=company_id,
        agent_id=agent_id,
        source=args.source,
        instance=args.instance_id,
    )
    issue, issue_created = find_or_create_validation_issue(
        args.base_url,
        token=args.api_token,
        company_id=company_id,
        agent_id=agent_id,
        title=args.issue_title,
        body=issue_body,
        always_create=args.always_create_issue,
    )

    return {
        "paperclip": {
            "baseUrl": args.base_url.rstrip("/"),
            "health": health,
        },
        "topology": "one-agent",
        "company": {
            "id": company_id,
            "name": company.get("name"),
            "created": company_created,
        },
        "agent": agent_summary(agent, created=agent_created, model=model),
        "hermes": {
            "containerHome": hermes_home,
            "sharedCompanyHome": True,
            "initialPrepare": initial_prepare,
            "finalPrepare": final_prepare,
            "honchoAiPeer": read_honcho_ai_peer(final_prepare["hostHonchoPath"]),
        },
        "validationIssue": {
            "id": issue.get("id"),
            "identifier": issue.get("identifier"),
            "title": issue.get("title"),
            "status": issue.get("status"),
            "created": issue_created,
        },
        "nextVerification": {
            "issuePath": f"/api/issues/{issue.get('id')}",
            "issueRunsPath": f"/api/issues/{issue.get('identifier') or issue.get('id')}/runs",
            "issueCommentsPath": f"/api/issues/{issue.get('id')}/comments",
        },
    }


def bootstrap_manager_worker(args: argparse.Namespace, *, values: dict[str, str], model: str, issue_body: str) -> dict[str, Any]:
    resolved_instance_id = instance_id(values, args.instance_id)
    health = wait_for_paperclip(args.base_url, token=args.api_token, timeout_seconds=args.health_timeout)
    company, company_created = find_or_create_company(
        args.base_url,
        token=args.api_token,
        name=args.company_name,
        description=args.company_description,
        budget_monthly_cents=args.budget_monthly_cents,
    )
    company_id = str(company["id"])
    hermes_home = container_hermes_home(
        company_id,
        container_paperclip_home=args.container_paperclip_home,
        instance=resolved_instance_id,
    )
    initial_prepare = run_prepare(
        company_id=company_id,
        agent_id=None,
        source=args.source,
        instance=args.instance_id,
    )
    manager, manager_created = find_or_create_agent(
        args.base_url,
        token=args.api_token,
        company_id=company_id,
        name=args.manager_name,
        role=args.manager_role,
        title=args.manager_title,
        model=model,
        hermes_home=hermes_home,
    )
    manager_id = str(manager["id"])
    manager_prepare = run_prepare(
        company_id=company_id,
        agent_id=manager_id,
        source=args.source,
        instance=args.instance_id,
    )
    worker, worker_created = find_or_create_agent(
        args.base_url,
        token=args.api_token,
        company_id=company_id,
        name=args.worker_name,
        role=args.worker_role,
        title=args.worker_title,
        model=model,
        hermes_home=hermes_home,
    )
    worker_id = str(worker["id"])
    worker_prepare = run_prepare(
        company_id=company_id,
        agent_id=worker_id,
        source=args.source,
        instance=args.instance_id,
    )
    parent_body = render_manager_worker_issue_body(
        issue_body,
        worker_name=worker.get("name") or args.worker_name,
        worker_id=worker_id,
        manager_name=manager.get("name") or args.manager_name,
        manager_id=manager_id,
    )
    parent_issue, parent_issue_created = find_or_create_validation_issue(
        args.base_url,
        token=args.api_token,
        company_id=company_id,
        agent_id=manager_id,
        title=args.manager_worker_issue_title,
        body=parent_body,
        always_create=args.always_create_issue,
    )

    return {
        "paperclip": {
            "baseUrl": args.base_url.rstrip("/"),
            "health": health,
        },
        "topology": "manager-worker",
        "company": {
            "id": company_id,
            "name": company.get("name"),
            "created": company_created,
        },
        "manager": agent_summary(manager, created=manager_created, model=model),
        "worker": agent_summary(worker, created=worker_created, model=model),
        "hermes": {
            "containerHome": hermes_home,
            "sharedCompanyHome": True,
            "homeDecision": (
                "manager and worker share the current company-scoped HERMES_HOME; "
                "per-agent Hermes homes are not part of this bootstrap slice"
            ),
            "initialPrepare": initial_prepare,
            "managerPrepare": manager_prepare,
            "workerPrepare": worker_prepare,
            "honchoAiPeer": read_honcho_ai_peer(worker_prepare["hostHonchoPath"]),
            "honchoAiPeerNote": "shared home is rendered last for the worker agent",
        },
        "validationIssue": {
            "id": parent_issue.get("id"),
            "identifier": parent_issue.get("identifier"),
            "title": parent_issue.get("title"),
            "status": parent_issue.get("status"),
            "created": parent_issue_created,
        },
        "expectedFlow": {
            "managerCreatesChildCount": 1,
            "workerCompletesChild": True,
            "managerClosesParentAfterChildDone": True,
        },
        "nextVerification": {
            "parentIssuePath": f"/api/issues/{parent_issue.get('id')}",
            "parentIssueRunsPath": f"/api/issues/{parent_issue.get('identifier') or parent_issue.get('id')}/runs",
            "parentIssueCommentsPath": f"/api/issues/{parent_issue.get('id')}/comments",
            "companyIssuesPath": f"/api/companies/{company_id}/issues",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Paperclip base URL.")
    parser.add_argument("--api-token", default=None, help="Optional Paperclip bearer token.")
    parser.add_argument("--health-timeout", type=int, default=300, help="Seconds to wait for Paperclip health.")
    parser.add_argument(
        "--topology",
        choices=("one-agent", "manager-worker"),
        default=DEFAULT_TOPOLOGY,
        help="Company shape to bootstrap.",
    )
    parser.add_argument("--company-name", required=True, help="Company name to create or reuse.")
    parser.add_argument("--company-description", default=DEFAULT_COMPANY_DESCRIPTION)
    parser.add_argument("--budget-monthly-cents", type=int, default=0)
    parser.add_argument("--agent-name", default=DEFAULT_AGENT_NAME)
    parser.add_argument("--agent-role", default=DEFAULT_AGENT_ROLE)
    parser.add_argument("--agent-title", default=DEFAULT_AGENT_TITLE)
    parser.add_argument("--model", default=None, help="Pinned model. Defaults to HERMES_MODEL_DEFAULT or script default.")
    parser.add_argument("--issue-title", default=DEFAULT_ISSUE_TITLE)
    parser.add_argument("--issue-body", default=DEFAULT_ISSUE_BODY)
    parser.add_argument("--issue-body-file", type=Path, default=None)
    parser.add_argument("--manager-name", default=DEFAULT_MANAGER_NAME)
    parser.add_argument("--manager-role", default=DEFAULT_MANAGER_ROLE)
    parser.add_argument("--manager-title", default=DEFAULT_MANAGER_TITLE)
    parser.add_argument("--worker-name", default=DEFAULT_WORKER_NAME)
    parser.add_argument("--worker-role", default=DEFAULT_WORKER_ROLE)
    parser.add_argument("--worker-title", default=DEFAULT_WORKER_TITLE)
    parser.add_argument("--manager-worker-issue-title", default=DEFAULT_MANAGER_WORKER_ISSUE_TITLE)
    parser.add_argument("--manager-worker-issue-body", default=DEFAULT_MANAGER_WORKER_ISSUE_BODY)
    parser.add_argument("--manager-worker-issue-body-file", type=Path, default=None)
    parser.add_argument("--always-create-issue", action="store_true", help="Do not reuse an existing open validation issue.")
    parser.add_argument("--source", type=Path, default=None, help="Source env file for Hermes projection.")
    parser.add_argument("--instance-id", default=None)
    parser.add_argument("--container-paperclip-home", default="/paperclip")
    args = parser.parse_args()

    values = source_values(args.source)
    model = args.model or values.get("HERMES_MODEL_DEFAULT", "").strip() or DEFAULT_HERMES_MODEL
    if args.topology == "one-agent":
        issue_body = args.issue_body_file.read_text() if args.issue_body_file else args.issue_body
        summary = bootstrap_one_agent(args, values=values, model=model, issue_body=issue_body)
    else:
        issue_body = (
            args.manager_worker_issue_body_file.read_text()
            if args.manager_worker_issue_body_file
            else args.manager_worker_issue_body
        )
        summary = bootstrap_manager_worker(args, values=values, model=model, issue_body=issue_body)
    json.dump(summary, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
