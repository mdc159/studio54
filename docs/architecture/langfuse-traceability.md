# Langfuse Traceability

This document describes the current direct `hermes_local` model-call
traceability slice. It is a precursor to roadmap Phase G, not the completed
development-wide observability plane.

Langfuse is downstream observability for Hermes model calls. It is not the
source of truth for company state, task status, approvals, artifacts, broker
events, or memory.

For the plain-language integration status, cleanup plan, and expected benefits,
see [Langfuse Integration Status](langfuse-integration-status.md).

## Source-Of-Truth Boundaries

- Paperclip is the source of truth for company, task, issue, comment,
  approval, and run state.
- Hermes is the runtime executor for agent, model, and tool work.
- The broker/continuity plane is the durable cross-system event spine.
- Langfuse is an observability, evidence, and debugging surface.
- GitHub, Linear, and repo docs carry planning decisions and durable
  human-readable knowledge.

## Active `hermes_local` Path

On the direct Paperclip `hermes_local` path, one run identifier is used across
Paperclip, Hermes, and Langfuse:

- Paperclip run ID: `PAPERCLIP_RUN_ID`
- Hermes run ID: `HERMES_RUN_ID`
- Langfuse trace ID: `LANGFUSE_TRACE_ID`

The Paperclip Hermes adapter stamps all three values from the active Paperclip
run after adapter env is merged. For this path, the Paperclip run ID equals the
Hermes run ID and equals the Langfuse trace ID. Operators can find a trace by
copying the Paperclip run ID into Langfuse trace search.

Hermes also accepts trace IDs in this precedence order:

1. `LANGFUSE_TRACE_ID`
2. `HERMES_RUN_ID`
3. `PAPERCLIP_RUN_ID`
4. generated UUID

Langfuse tracing no-ops unless all of these are present:

- `LANGFUSE_HOST`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`

Langfuse ingestion is best effort. Langfuse network, auth, or API failures must
never fail a Hermes or Paperclip run.

## Scope And Non-Goals

This slice covers:

- the current direct `hermes_local` path
- Hermes OpenAI-compatible model-call tracing
- run ID / trace ID correlation
- bounded prompt/output capture when explicitly enabled
- best-effort ingestion that must not break Hermes or Paperclip execution

This slice does not cover:

- full system-wide API tracing
- all tool-call tracing
- broker-wide or gateway-wide tracing
- n8n workflow tracing
- Honcho or memory-event tracing
- artifact lineage tracing
- Langfuse as a memory store
- Langfuse as a source of truth
- the completed roadmap Phase G architecture

## Captured Content

Raw prompt/output capture is explicit opt-in. By default, Hermes records
generation metadata without sending request messages or assistant text to
Langfuse.

Enable raw content capture for a private development run or profile with:

```sh
LANGFUSE_CAPTURE_CONTENT=true
```

Disable it explicitly with:

```sh
LANGFUSE_CAPTURE_CONTENT=false
```

The default content cap is 32,768 characters per input or output payload:

```sh
LANGFUSE_CONTENT_MAX_CHARS=32768
```

When content is truncated, Hermes records truncation metadata on the Langfuse
generation observation.

Important safety notes:

- Request messages can include system prompts, tool outputs, terminal output,
  logs, or accidentally pasted secrets.
- Truncation is not redaction.
- Live or prod-like runs should leave raw content capture disabled unless a
  redaction policy and fake-secret canary check are in place.
- Never commit trace dumps, logs, raw auth exports, `.env` files, memory dumps,
  or session databases.

## Streaming And Error Semantics

For normal streaming success, Hermes records the final accumulated assistant
text when raw content capture is enabled and adds metadata:

- `finish_reason: completed`
- `partial_output: false`
- `stream_attempt: <attempt number>`

If a streaming exception occurs after partial text has been accumulated, Hermes
records the partial output when content capture is enabled and adds metadata:

- `finish_reason: error`
- `partial_output: true`
- `stream_attempt: <attempt number>`
- `error_class: <exception class>`

If a stream is interrupted after partial text, Hermes records the interrupted
partial state with `finish_reason: interrupted`. Retry and stale-stream
handling can still produce multiple generation observations for one logical
agent turn; grouping is by the shared trace ID.

## Relationship To Roadmap Phase G

Roadmap Phase G expects correlation across gateway, broker, and Hermes. PR #5
lands before the full gateway/broker path exists, so it is useful for the
current direct path but does not finish Phase G.

Final Phase G still needs:

- a gateway-generated or normalized canonical `run_id`
- broker events stamped with `metadata_json.langfuse_trace_id`
- all spans nested under the same canonical trace
- shared correlation across Paperclip, Hermes, broker, and gateway
- a Langfuse dashboard or saved view for `trace_id == run_id`

## Run Records For Development And Optimization

For future optimization, development tests, and failure reviews, record this
minimum tuple in the issue, PR, or experiment notes:

- Paperclip issue ID
- Paperclip/Hermes/Langfuse run ID
- Langfuse trace URL
- model and provider
- outcome
- observed failure mode

Langfuse traces are supporting evidence. The durable decision log should live
in Paperclip issues, repository docs, PRs, or experiment artifacts.
