# Agent Enablement Checklist (for unencumbered PR evaluation and merge work)

Date: 2026-05-03 (UTC)

This checklist describes exactly what to provision so the agent can perform end-to-end PR checkout, review, validation, and merge operations without environment blockers.

## 1) Required tools

Install these CLIs and ensure they are in `PATH`:

1. **GitHub CLI (`gh`)**
   - Why: checkout PRs, inspect review threads, comment, and merge.
   - Verify:
     ```bash
     gh --version
     gh auth status
     ```

2. **Git (`git`)**
   - Why: fetch remotes, diff branches, commit, merge.
   - Verify:
     ```bash
     git --version
     ```

3. **uv**
   - Why: project-standard Python env + test execution.
   - Verify:
     ```bash
     uv --version
     ```

4. **Docker + Docker Compose plugin**
   - Why: compose config validation and optional stack smoke checks.
   - Verify:
     ```bash
     docker --version
     docker compose version
     ```

## 2) Repository wiring

1. Ensure the local clone has a remote (`origin`) configured:
   ```bash
   git remote add origin <repo-url>   # if missing
   git remote -v
   ```

2. Ensure fetch access to PR refs:
   ```bash
   git fetch origin
   git ls-remote origin
   ```

3. Optional but recommended: set default branch tracking
   ```bash
   git branch --set-upstream-to=origin/main main
   ```

## 3) GitHub authentication and permissions

Authenticate `gh` with a token/user that has:

- `repo` scope (private repos) or equivalent fine-grained repo permissions
- PR read/write (view PR, read comments, post comments, merge)
- Actions read (optional, for CI status inspection)

Setup:
```bash
gh auth login
# or
echo "$GITHUB_TOKEN" | gh auth login --with-token
```

Verify:
```bash
gh auth status
gh pr view 24 --json number,title,headRefName,baseRefName,state
```

## 4) Environment variables (minimum)

These are the most useful variables for this repo’s workflows.

### Required for GitHub CLI in non-interactive environments

- `GITHUB_TOKEN` (or `GH_TOKEN`)
  - Token must authorize this repository.

Example:
```bash
export GITHUB_TOKEN=<token>
```

### Helpful for deterministic local operations

- `TZ=UTC` (stable timestamps in generated outputs/logs)
- `PYTHONUNBUFFERED=1` (clear live logs)

## 5) Optional variables for runtime/smoke checks

Only needed when you want deep stack validation that touches Langfuse paths:

- `LANGFUSE_HOST`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`

If omitted, some flows are designed to no-op Langfuse safely; PR diff review can still proceed.

## 6) Network and container access

1. Outbound network must allow:
   - `github.com` and `api.github.com`
   - package/image endpoints needed by `uv` and `docker`

2. Docker daemon access:
   - current user can run `docker ps` without sudo prompts.

## 7) Fast “ready” script you can run before asking for PR work

```bash
set -euo pipefail

echo "== toolchain =="
command -v gh
command -v git
command -v uv
command -v docker

echo "== github auth =="
gh auth status

echo "== repo remotes =="
git remote -v

echo "== network/ref access =="
git fetch origin --prune

echo "== PR visibility =="
gh pr view 24 --json number,title,state,headRefName,baseRefName

echo "ready"
```

## 8) What to do if something fails

- `gh: command not found` → install GitHub CLI and restart shell.
- `fatal: 'origin' does not appear to be a git repository` → add/fix remote URL.
- `gh auth status` unauthenticated → set `GITHUB_TOKEN` and run `gh auth login --with-token`.
- `git fetch` permission denied → token/user lacks repo access.
- `docker` permission denied → add user to docker group or use an environment with daemon access.

## 9) Minimal unblock set (if you want just the essentials)

If you only want me unblocked for PR checkout + review (without deep runtime smoke):

1. Install `gh`.
2. Configure `origin` remote.
3. Provide `GITHUB_TOKEN` with repo PR permissions.
4. Confirm outbound access to GitHub.

That is sufficient to fetch PRs, inspect inline comments, diff against latest base, and produce a precise merge plan.
