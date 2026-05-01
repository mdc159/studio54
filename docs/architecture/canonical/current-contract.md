# Current Proven Contract

This is the short statement of what is active and proven now.

## Active Execution Contract

- active execution path: direct per-company hermes_local
- 1215 Paperclip -> Hermes gateway path: optional/future-state
- active runtime boundary: company-scoped HERMES_HOME
- active memory add-on on the proven path: self-hosted Honcho

## Proven Bootstrap Shapes

- one-agent bootstrap is proven
- manager/worker bootstrap is proven
- template-backed bootstrap is proven for:
  - one-agent
  - manager-worker

## Current Isolation Truth

- each company gets its own HERMES_HOME
- inner Hermes must not use ambient /root/.hermes
- manager and worker currently share the same company-scoped HERMES_HOME
- per-agent Hermes homes are not implemented yet

## Task Lifecycle Contract

- Paperclip is the system of record for issue/task state
- task completion is explicit
- the final successful completion action is one PATCH containing:
  - status: "done"
  - completion comment
- Paperclip does not infer completion from process exit alone

## Proven Runtime Behaviors

- useful comments can land with correct `authorAgentId`
- createdByRunId attribution works
- wake-loop regressions on the active direct path were fixed
- manager/worker delegation and parent/child linkage are proven

## Preferred Next Reference Docs

- [bootstrap-module.md](bootstrap-module.md)
- [../paperclip-hermes-local-contract.md](../paperclip-hermes-local-contract.md)
- [../company-bootstrap.md](../company-bootstrap.md)

