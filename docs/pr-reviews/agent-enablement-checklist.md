# Agent Enablement Checklist

Date: 2026-05-03

This checklist defines the minimum environment needed for an agent to work on
Studio54 PRs without getting blocked by local setup. It is intentionally paired
with the cloud workbench and VPS simulation gates in
[`docs/architecture/cloud-agent-vps-simulation.md`](../architecture/cloud-agent-vps-simulation.md).

## Required tools

Install these CLIs and ensure they are in `PATH`:

1. `git` — fetch, diff, commit, push.
2. `gh` — inspect PRs, comments, checks, artifacts.
3. `uv` — Python test/runtime environment.
4. `python3` 3.12+ — scripts and tests.
5. Docker + Docker Compose plugin — compose config and optional substrate smoke.
6. Node.js + package manager (`npm`/`pnpm`) — Paperclip package checks.

Verify with:

```bash
bash scripts/doctor-agent-env.sh
```

## GitHub authentication

The agent environment should have `gh` authenticated with access to this repo:

```bash
gh auth status
gh pr list --limit 5
```

A token should have enough permission to:

- read repository contents,
- fetch branches and PR refs,
- push branches,
- open/comment on PRs,
- read GitHub Actions runs and artifacts.

Do not print token values in logs. Use presence/status checks only.

## Standard local/cloud loop

```bash
bash scripts/doctor-agent-env.sh
bash scripts/validate-repo.sh
bash scripts/simulate-vps-bootstrap.sh
```

Expected artifact paths:

```text
.artifacts/agent-validation/
.artifacts/vps-simulation/simulated-vps-bootstrap-report.json
```

## Codespaces

A fresh Codespace should be able to run:

```bash
bash scripts/validate-repo.sh
bash scripts/simulate-vps-bootstrap.sh
```

If Docker is not available yet, `validate-repo.sh` may skip compose smoke, but
GitHub Actions should still run the canonical gate.

## Anti-cheat rule

Agents must not claim success from screenshots, hand-drawn graphs, edited result
files, or verbal summaries alone. Success requires verifier-produced artifacts
from the current branch.

Protected verifier changes require explicit review:

```text
.github/workflows/*
scripts/agent-evidence-guard.py
scripts/verify-simulated-vps-bootstrap.py
scripts/simulate-vps-bootstrap.sh
docs/architecture/cloud-agent-vps-simulation.md
```

## Minimal unblock set

If only PR checkout/review is needed:

1. `gh` authenticated.
2. `git fetch origin` works.
3. `uv` can run the Python tests.
4. The agent can run the two canonical commands:

```bash
bash scripts/validate-repo.sh
bash scripts/simulate-vps-bootstrap.sh
```
