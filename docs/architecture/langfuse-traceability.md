# Langfuse Traceability

Langfuse is downstream observability for Hermes and Paperclip runs. It is not
the source of truth for company state, task status, approvals, artifacts, or
memory. Paperclip remains the system of record for company and issue state;
Hermes remains the runtime of record for agent execution.

## Active `hermes_local` Path

On the direct Paperclip `hermes_local` path, one run identifier is used across
the stack:

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

## Captured Content

This private self-hosted stack intentionally captures model-call prompt and
assistant-output content in Langfuse for debugging, evaluation, and future
learning workflows. Hermes records OpenAI-compatible request messages as
generation `input` and final assistant text as generation `output`.

Disable content capture for a run or profile with:

```sh
LANGFUSE_CAPTURE_CONTENT=false
```

The default content cap is 32,768 characters per input or output payload:

```sh
LANGFUSE_CONTENT_MAX_CHARS=32768
```

When content is truncated, Hermes records truncation metadata on the Langfuse
generation observation.

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
