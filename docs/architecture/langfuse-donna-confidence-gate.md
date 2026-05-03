# Donna Langfuse Confidence Gate

This is the exhaustive handoff plan for Donna to validate PR #5 before it is
merged. It follows the project operating model from this repo and the adjacent
`agent-knowledge-exchange` repo:

- Linear is the source of truth for planned work, ownership, acceptance
  criteria, and final state.
- GitHub is the source of truth for branches, commits, PR review, checks, and
  merge history.
- Repo docs are the durable human-readable operating record.
- Paperclip is the source of truth for company, task, issue, comment,
  approval, and run state.
- Hermes is the runtime executor for agent, model, and tool work.
- The broker/continuity plane is the durable cross-system event spine.
- Langfuse is downstream observability and debugging evidence. It is not a
  source of truth, memory store, task store, or replacement for GitHub, Linear,
  Paperclip, or broker events.

## Mission

Decide whether PR #5 is safe to merge as the direct `hermes_local`
model-call Langfuse tracing slice.

The gate must prove that PR #5:

- preserves normal Hermes execution when Langfuse is absent, misconfigured, or
  unreachable
- traces OpenAI-compatible Hermes model calls on the direct Paperclip
  `hermes_local` path
- preserves the identity chain
  `Paperclip run ID == Hermes run ID == Langfuse trace ID`
- keeps raw prompt/output capture explicit opt-in
- records bounded content and truncation metadata when capture is enabled
- records streaming success, partial-output, and error metadata correctly
- does not leak fake secrets into logs or traces during controlled canary
  checks
- does not regress broader Hermes or Paperclip test surfaces that make the
  direct path credible

This gate does not expand PR #5 into full system-wide observability. Gateway,
broker, tool-call, n8n, Honcho, memory, API middleware, and artifact-lineage
tracing remain follow-up Phase G work.

## Required Inputs

Donna needs these references open before starting:

- PR: <https://github.com/mdc159/studio54/pull/5>
- Branch: `integration/langfuse-traceability`
- Traceability contract:
  [langfuse-traceability.md](langfuse-traceability.md)
- Integration status:
  [langfuse-integration-status.md](langfuse-integration-status.md)
- Direct runtime contract:
  [paperclip-hermes-local-contract.md](paperclip-hermes-local-contract.md)
- Current state:
  [current-state.md](current-state.md)
- Roadmap Phase G:
  [roadmap.md](roadmap.md#phase-g--langfuse-instrumentation-12-days)
- Agent workflow:
  [../AGENTS.md](../../AGENTS.md)
- Knowledge-exchange workflow:
  `/opt/agent-knowledge-exchange/docs/agent-operating-procedure.md` on the VPS,
  or the local clone at
  `/home/mdc159/projects/company/agent-knowledge-exchange/docs/agent-operating-procedure.md`

## Required Environment

Run this on the Donna VPS or an equivalent node with the same Paperclip,
Hermes, Langfuse, and model-provider wiring.

Local prerequisites:

- clean checkout of `studio54`
- branch `integration/langfuse-traceability`
- `uv`
- Python version compatible with `modules/hermes-agent`
- Node >= 20
- `pnpm` 9.15.x
- Docker and Docker Compose for stack checks
- Playwright browser dependencies if running browser e2e
- Paperclip reachable on the node when live smoke tests run
- Langfuse reachable privately on the node when live smoke tests run
- model-provider credentials available outside git when live model calls run

Do not commit or paste real `.env` contents, API keys, OAuth exports, runtime
logs, trace dumps, memory dumps, or session databases.

## Gate 0: Workspace And PR Sanity

Purpose: confirm Donna is testing the right thing and not mixing unrelated
work into the merge decision.

Commands:

```sh
git fetch origin
git status --short --branch
git log --oneline --decorate --max-count=8
git diff --stat origin/main...HEAD
git diff --check origin/main...HEAD
gh pr view 5 --json url,state,isDraft,mergeStateStatus,mergeable,reviewDecision,headRefName,baseRefName
```

Pass criteria:

- branch is `integration/langfuse-traceability`
- PR #5 targets `main`
- PR is not draft
- PR is mergeable or any conflict is understood before continuing
- diff is limited to Langfuse traceability code/tests/docs plus related
  current-state docs
- `git diff --check` has no whitespace errors
- no uncommitted local changes are mixed into the test result

Block criteria:

- wrong branch
- unresolved conflicts
- unrelated code or runtime state in the diff
- uncommitted changes that affect test results

## Gate 1: Secret And Runtime-State Sanity

Purpose: ensure the branch did not commit secrets or machine residue.

Commands:

```sh
git diff --name-only origin/main...HEAD
git diff origin/main...HEAD | rg -n "LANGFUSE_SECRET_KEY|LANGFUSE_PUBLIC_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|GITHUB_TOKEN|password|token|secret|api_key|\\.env" -i
git ls-files | rg -n "(^|/)\\.env$|trace-dump|session.*\\.db|memory.*dump|auth.*export|runtime.*log" -i
```

Pass criteria:

- only placeholder env names or documentation references appear
- no live values, auth exports, trace dumps, logs, session DBs, memory dumps,
  or `.env` files are tracked

Block criteria:

- any real secret value
- any tracked runtime state
- any unreviewed trace or log dump

## Gate 2: Hermes Targeted Langfuse Tests

Purpose: prove the integration slice itself still behaves as intended.

Commands:

```sh
cd modules/hermes-agent
uv run --frozen python -m py_compile agent/langfuse_probe.py run_agent.py
uv run --frozen --with pytest --with pytest-xdist python -m pytest tests/agent/test_langfuse_probe.py
```

Pass criteria:

- syntax/import compile passes
- Langfuse probe suite passes
- test coverage includes:
  - no-op without config
  - ingestion request shape
  - Basic Auth
  - network failures swallowed
  - trace ID precedence including `PAPERCLIP_RUN_ID`
  - capture disabled by default
  - capture enabled with input/output present
  - truncation metadata
  - streaming partial/error metadata

Block criteria:

- any deterministic failure in these tests
- Langfuse failure can fail a Hermes run
- raw content capture is enabled by default

## Gate 3: Broader Hermes Confidence

Purpose: catch regressions outside the narrow probe unit tests.

Commands:

```sh
cd modules/hermes-agent
uv run --frozen --with pytest --with pytest-xdist python -m pytest
uv run --frozen --with pytest --with pytest-xdist python -m pytest -o addopts="" -m integration tests/integration
```

Notes:

- The first command uses the repo default `addopts`, which excludes
  `integration` tests.
- The second command intentionally runs integration-marked tests and may
  require external services, optional packages, or provider credentials.
- If a required integration prerequisite is absent on the VPS, record the
  exact missing prerequisite and mark that sub-gate as skipped, not passed.

Pass criteria:

- non-integration Hermes suite passes
- integration suite passes, or every skipped integration case has an explicit
  missing prerequisite that is unrelated to PR #5
- no failures implicate `agent/langfuse_probe.py`, `run_agent.py`, OpenAI-
  compatible model calls, streaming, env handling, or error isolation

Block criteria:

- deterministic local Hermes failures introduced by PR #5
- integration failures involving model-call execution, streaming, or env
  propagation that are not understood

## Gate 4: Paperclip Workspace Confidence

Purpose: prove Paperclip still provides a credible direct `hermes_local` run
surface around Hermes.

Commands:

```sh
cd modules/paperclip
pnpm install --frozen-lockfile
pnpm run typecheck
pnpm run build
pnpm run test:run
pnpm run test:e2e
pnpm run test:e2e:multiuser-authenticated
pnpm run test:release-smoke
```

Additional Hermes adapter checks:

```sh
cd modules/paperclip
rg -n "hermes_local|PAPERCLIP_RUN_ID|X-Paperclip-Run-Id|adapter manager|hermes-paperclip-adapter" AGENTS.md docs server packages ui skills
```

Pass criteria:

- typecheck, build, and Vitest pass
- Playwright e2e and release-smoke pass, or each skip has a concrete missing
  browser/service prerequisite
- Donna verifies the VPS Paperclip installation has the Hermes adapter/plugin
  installed and registered as `hermes_local`
- Paperclip still injects `PAPERCLIP_RUN_ID` into local adapter runs
- mutating Paperclip issue operations still use `X-Paperclip-Run-Id`

Block criteria:

- deterministic Paperclip test failure connected to local adapter execution,
  run IDs, issue wake handling, or auth
- Hermes adapter/plugin missing from the VPS runtime when live smokes are
  expected
- `PAPERCLIP_RUN_ID` is not available to the `hermes_local` process

## Gate 5: Stack And Service Readiness

Purpose: prove the VPS services needed for live confidence are actually
running and privately reachable.

Commands:

```sh
./bin/1215 status || true
docker compose -f stack/prototype-local/docker-compose.substrate.yml ps
docker compose -f stack/prototype-local/docker-compose.substrate.yml config
curl -fsS http://127.0.0.1:3000/api/public/health || curl -fsS http://127.0.0.1:3000
curl -fsS http://127.0.0.1:3100/api/health
curl -fsS http://127.0.0.1:18000/health || true
curl -fsS http://127.0.0.1:8090/healthz || true
```

Pass criteria:

- Docker Compose config resolves
- Langfuse web is reachable on loopback/private ingress
- Paperclip API is reachable
- any unavailable optional service is recorded with impact
- no unexpected public `0.0.0.0` service bind is introduced by this branch

Block criteria:

- Paperclip or Langfuse unavailable for live smoke tests with no acceptable
  skip reason
- service exposure drift that creates public binds

## Gate 6: Live Direct `hermes_local` Langfuse Smoke

Purpose: prove the real direct path produces correlated Langfuse evidence.

Run two controlled smokes. Use disposable Paperclip companies/issues. Do not
paste real secrets into prompts.

First, with raw content capture disabled:

```sh
unset LANGFUSE_CAPTURE_CONTENT
export LANGFUSE_HOST=<private-langfuse-host>
export LANGFUSE_PUBLIC_KEY=<from-private-runtime-env>
export LANGFUSE_SECRET_KEY=<from-private-runtime-env>
python3 stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py --topology one-agent --always-create-issue
python3 stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py --topology manager-worker --always-create-issue
```

Then, in a controlled dev-only canary run with raw content capture enabled:

```sh
export LANGFUSE_CAPTURE_CONTENT=true
export LANGFUSE_CONTENT_MAX_CHARS=2048
export LANGFUSE_FAKE_SECRET_CANARY=sk-fake-langfuse-canary-do-not-use
python3 stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py --topology one-agent --always-create-issue
```

Donna should record for each live run:

- Paperclip company ID
- Paperclip issue ID
- Paperclip run ID
- Hermes run ID if separately visible
- Langfuse trace ID
- Langfuse trace URL
- provider and model
- capture setting
- outcome
- observed failure mode, if any

Manual Langfuse checks:

- search Langfuse by the Paperclip run ID
- confirm the trace ID equals the Paperclip run ID
- confirm metadata includes provider, model, base URL host, streaming flag,
  status, latency, API mode, and Paperclip correlation fields when present
- with capture disabled, confirm raw request messages and assistant output are
  not present
- with capture enabled, confirm bounded input/output are present for the
  controlled canary run
- confirm truncation metadata appears when the configured cap is exceeded
- confirm no real secrets appear

Pass criteria:

- one-agent run completes and closes its assigned issue through Paperclip
- manager-worker run completes expected parent/child lifecycle or any failure
  is understood as pre-existing Paperclip behavior
- Langfuse trace is findable by Paperclip run ID
- `PAPERCLIP_RUN_ID == HERMES_RUN_ID == LANGFUSE_TRACE_ID` on the direct path
- Langfuse ingestion failures, if induced or observed, do not fail the
  Paperclip/Hermes run
- fake canary handling is documented and no real secret appears in traces or
  logs

Block criteria:

- trace cannot be found by run ID
- trace ID diverges from Paperclip run ID
- raw content captured when `LANGFUSE_CAPTURE_CONTENT` is unset or false
- Langfuse outage fails a Hermes or Paperclip run
- real secret leakage

## Gate 7: Evidence Record And Merge Recommendation

Purpose: leave a reusable decision trail.

Donna should post one final evidence record in the Linear parent issue and on
PR #5 with:

- commit SHA tested
- VPS/node name
- date/time of test
- command matrix with pass/fail/skip
- exact skip reasons
- Paperclip issue IDs
- shared run IDs
- Langfuse trace URLs
- model/provider used
- content-capture mode for each live run
- failures and whether they are PR blockers
- final recommendation: `merge`, `do not merge`, or `merge after listed fixes`

Recommended compact table:

| Gate | Result | Evidence | Blocker? |
|---|---|---|---|
| 0 workspace | pass/fail | branch, SHA, PR state | yes/no |
| 1 secrets | pass/fail | scan summary | yes/no |
| 2 Hermes targeted | pass/fail | command result | yes/no |
| 3 Hermes broad | pass/fail/skip | command result or prerequisite | yes/no |
| 4 Paperclip | pass/fail/skip | command result or prerequisite | yes/no |
| 5 services | pass/fail/skip | service health | yes/no |
| 6 live smokes | pass/fail/skip | run IDs + trace URLs | yes/no |

## Merge Decision Rule

PR #5 can be recommended for merge only when:

- Gates 0, 1, and 2 pass
- Gate 3 non-integration Hermes tests pass
- Gate 4 deterministic local Paperclip checks pass or unrelated failures are
  documented and accepted by the human operator
- Gate 6 has at least one successful direct `hermes_local` Langfuse trace on
  the Donna VPS, unless the human operator explicitly accepts a missing-live-
  credentials skip
- no real secret or raw runtime state was committed
- no raw prompt/output content is captured by default
- Langfuse remains best-effort and non-blocking
- source-of-truth boundaries remain as documented

If any block criterion triggers, do not merge PR #5. Either push a focused fix
to the same branch and rerun the affected gates, or record the blocker in
Linear and leave the PR unmerged.

## Linear Structure

Create one Linear project and one parent issue with child issues.

Project:

- Name: `Langfuse Direct-Path Confidence Gate`
- Linear URL:
  <https://linear.app/1215-labs/project/langfuse-direct-path-confidence-gate-28e08a64a725>
- Team: `121`
- Priority: High
- Summary: `Validate PR #5 as the direct hermes_local Langfuse tracing slice before merge.`
- Labels: `langfuse`, `hermes`, `paperclip`, `confidence-gate`

Parent issue:

- Title: `Run PR #5 Langfuse direct-path confidence gate`
- Linear issue: `121-26`
  <https://linear.app/1215-labs/issue/121-26/run-pr-5-langfuse-direct-path-confidence-gate>
- State: `Todo` until Donna starts, then `In Progress`, then `Done` only after
  evidence is posted
- Links:
  - PR #5
  - this document
  - Langfuse Traceability
  - Paperclip `hermes_local` Contract

Child issues:

1. `Prepare Donna VPS workspace for PR #5 confidence gate`
   - Linear issue: `121-27`
   - Gates: 0, 1
   - Acceptance: correct branch/SHA, clean diff, no secrets/runtime state
2. `Run Hermes Langfuse targeted and broad suites`
   - Linear issue: `121-28`
   - Gates: 2, 3
   - Acceptance: targeted probe passes, broad Hermes result recorded
3. `Run Paperclip workspace and hermes_local adapter checks`
   - Linear issue: `121-29`
   - Gate: 4
   - Acceptance: typecheck/build/tests/e2e results recorded, adapter/plugin
     registration verified
4. `Verify Donna VPS services for live Langfuse smoke`
   - Linear issue: `121-30`
   - Gate: 5
   - Acceptance: Paperclip and Langfuse reachable, optional service gaps
     recorded
5. `Run live hermes_local Langfuse smoke tests`
   - Linear issue: `121-31`
   - Gate: 6
   - Acceptance: one-agent and manager-worker evidence recorded with trace URLs
6. `Publish PR #5 merge recommendation`
   - Linear issue: `121-32`
   - Gate: 7
   - Acceptance: evidence table posted to Linear and PR #5 with final
     recommendation

Use labels:

- `langfuse`
- `hermes`
- `paperclip`
- `confidence-gate`
- `human-review`
- `codex` if Codex authored the plan

Donna should own or be mentioned on the execution issues if Donna exists as a
Linear user. Otherwise leave assignee blank and put `Preferred executor:
Donna on VPS` in each issue description.
