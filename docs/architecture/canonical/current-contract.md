# Current Contract

This is the active, proven contract for Paperclip execution through Hermes on
the current reference node shape.

## Active Path

- Paperclip runs Hermes directly through per-company `hermes_local`.
- The Paperclip -> Hermes gateway path is optional/future-state for Paperclip
  task execution.
- The active runtime boundary is company-scoped `HERMES_HOME`.
- No Paperclip company should point at ambient outer Hermes state such as
  `/root/.hermes`.

## Memory Contract

- Self-hosted Honcho is proven on the active direct path.
- Honcho is additive; it does not replace Hermes local state under
  `HERMES_HOME`.
- The Honcho workspace key is the Paperclip `companyId`.
- For one-agent bootstrap, the Honcho AI peer is
  `paperclip-agent-<agent-id>` after agent-aware rendering.
- In the current manager/worker topology, manager and worker share one
  company-scoped `HERMES_HOME`, so home-local files such as `honcho.json` are
  shared and the last agent-aware render can determine the active `aiPeer`.

## Bootstrap Contract

- One-agent bootstrap is proven.
- Manager/worker bootstrap is proven.
- Manager and worker currently share the company-scoped `HERMES_HOME`.
- The current manager/worker shape is not per-agent Hermes home isolation.
- Per-agent Hermes homes remain future work.

## Issue Execution Contract

- Paperclip is the system of record for issue state.
- A successful `hermes_local` process exit does not imply issue completion.
- Bounded assigned work must end with one run-scoped PATCH containing both:

```json
{
  "status": "done",
  "comment": "DONE: <completion summary>"
}
```

- Completion must carry `Authorization: Bearer $PAPERCLIP_API_KEY`.
- Completion must carry `X-Paperclip-Run-Id: $PAPERCLIP_RUN_ID`.
- Comment attribution, `createdByRunId`, and assignment wake-loop fixes are
  part of the active contract.

## Detailed References

- [Paperclip hermes_local contract](../paperclip-hermes-local-contract.md)
- [Company bootstrap](../company-bootstrap.md)
- [Honcho memory topology](../honcho-memory-topology.md)
- [Reference node target](../reference-node-target.md)
