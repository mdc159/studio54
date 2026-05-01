# Langfuse Integration Status

This document explains where the Langfuse integration stands, what we plan to
do next, and what we expect to gain from finishing the cleanup. It is the
plain-language orientation layer. For the exact trace ID, env var, ingestion,
and content-capture contract, see
[Langfuse Traceability](langfuse-traceability.md).

## Where We Are

Langfuse is now treated as downstream observability for Hermes and Paperclip,
not as the source of truth for company state or task completion. Paperclip
remains the system of record for companies, issues, comments, approvals, and
run attribution. Hermes remains the runtime of record for model calls, tools,
and agent execution. Langfuse records what happened inside the model-call
layer so humans and future evaluation workflows can inspect it.

The stale `langfuse-sidecar` work has been replaced rather than rebased. PR #1
is closed as superseded. PR #5 is the clean replacement branch from current
`main`, and it ports only the Langfuse traceability work needed for the active
direct `hermes_local` path.

The direct Paperclip `hermes_local` path now has one run identity across the
stack:

- `PAPERCLIP_RUN_ID`
- `HERMES_RUN_ID`
- `LANGFUSE_TRACE_ID`

For active Paperclip-driven Hermes runs, those three values are the same run
ID. That means an operator can start from a Paperclip issue or heartbeat run,
copy the run ID, and find the corresponding Langfuse trace.

Hermes owns the caller-side Langfuse generation observation for
OpenAI-compatible chat completions. The trace includes provider, model,
base-url host, streaming flag, status, latency, API mode, error class, and
Paperclip correlation metadata when present. In this private self-hosted stack,
prompt and final assistant-output capture is enabled intentionally, with an env
kill switch for cases where content capture should be disabled.

## What We Plan To Do

The immediate plan is to merge PR #5 as the single canonical implementation
after the exhaustive Hermes and Paperclip confidence gate completes. The old
sidecar branch should not be force-rebased, reopened, or replayed. Once PR #5
is merged, `main` becomes the only branch needed for this integration.

The merge gate is broader than the initial Langfuse unit slice. It should run:

- targeted Hermes Langfuse probe tests
- full Hermes non-integration and integration pytest runs
- Hermes syntax/import checks for the touched tracing code
- Hermes Paperclip adapter typecheck and build
- Paperclip workspace typecheck, build, and Vitest suites
- Paperclip Playwright e2e and release-smoke suites
- live direct `hermes_local` one-agent and manager-worker smoke runs when
  Paperclip, Hermes, Langfuse, and model credentials are available

Any live or external test that cannot run must be recorded as a
missing-prerequisite skip, not silently treated as a pass. Any deterministic
local failure should block the merge until it is understood and fixed.

After merge, cleanup is straightforward:

- delete `origin/integration/langfuse-traceability`
- delete the local `integration/langfuse-traceability` branch
- retire the stale local `studio54-langfuse` checkout after confirming it has
  no unpushed work that still matters
- keep PR #1 closed as superseded by PR #5

For future optimization, development tests, and failure reviews, every useful
run record should include the Paperclip issue ID, the shared run ID, the
Langfuse trace URL, model/provider, outcome, and observed failure mode.

## What We Hope To Gain

The main gain is traceability. A future operator or engineer should be able to
move from "this Paperclip issue behaved strangely" to "this exact Hermes model
call received this prompt, returned this output, used this model/provider, took
this long, and failed or succeeded in this way." That shortens debugging loops
and makes failures concrete instead of anecdotal.

The second gain is a clean integration boundary. Paperclip keeps durable work
state. Hermes keeps runtime behavior. Langfuse keeps model-call observability.
The systems reinforce each other without collapsing into one ambiguous source
of truth.

The third gain is better development memory. By recording issue ID, run ID,
trace URL, model/provider, outcome, and failure mode, the repo can accumulate
usable evidence about what works and what fails. That evidence can later feed
evals, prompt improvements, model comparisons, and learning workflows without
requiring agents or humans to reconstruct history from logs.

The final gain is repo hygiene. The stale gateway-first sidecar branch is
retired, the active direct `hermes_local` path is documented, and the
Langfuse integration becomes one merged branch with one canonical contract.
