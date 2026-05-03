# PR 24 Evaluation — "Enhance Langfuse integration and introduce three-way audit framework"

Date: 2026-05-03 (UTC)
Evaluator: Codex agent

## Scope and environment findings

I could not directly check out PR #24 in this container because:

- `gh` CLI is not installed (`gh pr checkout 24` fails with `gh: command not found`).
- No Git remote is configured in the local clone (`git remote -v` returns empty), so `git fetch origin pull/24/head:...` is not possible.

Given these constraints, this evaluation is based on the latest local branch state (`work`) and repo content inspection.

## Current branch baseline

Local `HEAD` is:

- `a50182a` — `proto: add hermes langfuse model-call probe`

Recent history indicates multiple Hermes/Langfuse-related hardening commits are already present in this workspace.

## Evidence: Langfuse integration exists and is wired end-to-end

### Gateway-side ingestion client and tracing

- `stack/services/hermes-gateway/hermes_gateway/langfuse.py` implements a minimal async Langfuse ingestion client and documents run correlation semantics.
- `stack/services/hermes-gateway/hermes_gateway/app.py` creates traces/spans during run lifecycle.
- `stack/services/hermes-gateway/hermes_gateway/spawn.py` injects `LANGFUSE_TRACE_ID` and `LANGFUSE_SESSION_ID` into child process env.

### Broker-side correlation and metadata stamping

- `stack/broker/broker_service/app.py` stamps `metadata.langfuse_trace_id = run_id` when appropriate.
- `stack/broker/tests/test_app.py` contains tests for stamping and explicit override preservation.

### Stack bring-up and Langfuse substrate

- `stack/prototype-local/docker-compose.substrate.yml` includes `langfuse-web` and `langfuse-worker`, S3/minio integration, and bootstrap env.
- `stack/prototype-local/README.md` documents Langfuse tracing behavior and optional env-driven no-op mode.

## Evidence: Three-way audit framework appears implemented

The repo already includes a canary-based three-surface audit path that checks:

1. Broker payloads
2. Langfuse traces
3. (By design/docs) log/trace surfaces tied to run lifecycle

Primary implementation anchor:

- `stack/control/control1215/lifecycle.py` defines canary checks and reports (`canary absent from broker + langfuse`), with conditional Langfuse probe behavior.

Supporting architecture and rationale:

- `docs/architecture/pitfalls-and-recoveries.md` explains the multi-surface verification strategy and outage semantics.
- `docs/architecture/execution-plan.md` and `docs/architecture/roadmap.md` define Phase G acceptance checks for broker + Langfuse correlation.

## Risk assessment before merge

Because PR #24 itself is not fetchable in this environment, merge readiness must be gated on a diff-level review elsewhere. Based on current repo state, likely risk areas for overlap/conflict are:

- `hermes_gateway/langfuse.py`
- `hermes_gateway/app.py`
- `hermes_gateway/spawn.py`
- `broker_service/app.py`
- `control1215/lifecycle.py`
- corresponding tests under `stack/services/hermes-gateway/tests/`, `stack/broker/tests/`, and `stack/control/tests/`

## Proposed merge plan

1. **Acquire PR diff in a remote-enabled environment**
   - Run `gh pr checkout 24` (or fetch by ref) where remotes and GitHub auth are configured.

2. **Perform overlap/conflict review against latest `work`/default branch**
   - Focus on Langfuse trace semantics (`run_id` as `trace_id`), no-op behavior, and canary/audit logic.

3. **Run targeted validation suite**
   - `uv run --project stack/services/hermes-gateway pytest`
   - `uv run --project stack/broker pytest`
   - `uv run --project stack/control pytest`
   - `docker compose -f stack/prototype-local/docker-compose.substrate.yml config`

4. **Run smoke verification for lifecycle-level behavior**
   - `./bin/1215 up --target prototype-local`
   - `./bin/1215 smoke`
   - Confirm canary remains absent across broker + Langfuse probes.

5. **Merge strategy**
   - If PR duplicates already-landed code: close as superseded or merge with conflict-resolution commit that preserves latest tests/docs.
   - If PR adds net-new audit coverage: squash-merge with scoped subject (`proto:` or `fix:`) and attach validation logs.

## Recommendation

Status: **conditionally mergeable** pending remote diff review.

Given current local state already contains substantial Langfuse + audit wiring, the most probable outcome is partial or full overlap with existing commits. Proceed with a remote-enabled, file-by-file comparison before merge.
