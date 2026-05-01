# Bootstrap Module

Module name: direct Paperclip/Hermes company bootstrap module.

This module is the reusable block proven by the recent Paperclip/Hermes/Honcho
bootstrap work. It creates or reuses a Paperclip company, prepares the local
Hermes runtime boundary for that company, wires self-hosted Honcho, creates
agents, and proves execution with a bounded validation issue.

## Responsibilities

The module performs the direct-path sequence:

1. Create or reuse a Paperclip company.
2. Prepare a company-scoped Hermes home.
3. Create or reuse Paperclip agents.
4. Render `.env`, `config.yaml`, `honcho.json`, and local Hermes directories.
5. Assign active `hermes_local` runtime config to the agent.
6. Create a validation issue.
7. Prove lifecycle completion with a bounded task.

Current implementations:

- `stack/prototype-local/scripts/prepare_paperclip_hermes_home.py`
- `stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py`
- `stack/prototype-local/templates/paperclip-hermes-one-agent.json`
- `stack/prototype-local/templates/paperclip-hermes-manager-worker.json`

Supported topologies:

- `one-agent`
- `manager-worker`

Current limitation:

- Manager and worker share the same company-scoped `HERMES_HOME`.
- This is practical company-level isolation, not per-agent Hermes home
  isolation.

## Inputs And Outputs

Inputs:

- Paperclip API URL and API key.
- Company name and description.
- Agent names, roles, titles, and model.
- Topology selection: `one-agent` or `manager-worker`.
- Optional Honcho base URL and operator peer defaults.
- Container-visible company Hermes home path.

Outputs:

- Paperclip company.
- One or more `hermes_local` Paperclip agents.
- Company-scoped Hermes home under
  `/paperclip/instances/<instance-id>/companies/<company-id>/hermes-home`.
- Agent runtime config with `adapterConfig.env.HERMES_HOME`.
- Agent-aware `honcho.json` when an agent ID is available.
- Validation issue assigned through the normal Paperclip execution path.
- JSON summary with company, agent, Hermes home, Honcho peer, issue, and
  verification API paths.

## Guarantees And Boundaries

The module guarantees:

- Exact-name company reuse or explicit failure on duplicate company names.
- Company-scoped local Hermes runtime state.
- Honcho workspace set to the Paperclip `companyId`.
- Honcho AI peer set to `paperclip-agent-<agent-id>` after agent creation.
- Prepared home ownership suitable for the Paperclip runtime user.
- Direct `hermes_local` execution for validation.
- Explicit Paperclip issue completion when the agent follows the prompt.

The module does not guarantee:

- Per-agent Hermes homes.
- Gateway-first Paperclip execution.
- Per-task Honcho session mapping as an active contract.
- Cross-node company migration.
- Shared graph/vector fabric or alignment-log promotion.

## Dependencies

The active path depends on:

- A healthy Paperclip service.
- A Paperclip image that contains a working `hermes` CLI.
- The Hermes launcher and Python interpreter being executable by the Paperclip
  runtime user.
- Writable company Hermes home ownership for the Paperclip runtime UID/GID.
- Self-hosted Honcho on loopback when Honcho memory is expected.
- Hermes installed with the Honcho provider dependency inside the Paperclip
  runtime environment.
- Service environment precedence that keeps generated Honcho settings
  authoritative.

## Sequencing Rules

Rerender `honcho.json` after agent creation:

- First preparation can only know the company ID.
- After agent creation, rerun preparation with `--agent-id`.
- The final AI peer must be `paperclip-agent-<agent-id>`.

Create delegated worker issues in two steps:

- Create the child issue linked to the parent with `parentId`.
- Leave the child unassigned and in `backlog`.
- Activate it with a PATCH that sets `assigneeAgentId` and `status: "todo"`.

Complete issues explicitly:

- Do not infer completion from process exit.
- The final action is one PATCH with both `status: "done"` and a completion
  comment.
- The request must carry the Paperclip run ID for correct attribution.

## Failure Modes And Gotchas

- `HERMES_HOME` is the true local memory boundary. If it is wrong, memory
  isolation is wrong.
- Honcho is additive, not the whole memory system.
- Ownership and permissions are part of correctness, not a filesystem detail.
- Service env precedence can silently break Honcho by loading the wrong `.env`.
- Tracing and memory are different concerns; Langfuse correlation does not
  prove memory isolation.
- Passing unresolved adapter env binding objects can produce invalid runtime
  values such as `[object Object]`.
- Assignment wake paths must surface task fields into adapter config or the
  adapter can fall back to no-task heartbeat behavior.
- In the current manager/worker topology, shared home-local files mean the last
  render can win for files such as `honcho.json`.

## Extension Points

Near-term extensions should keep the module boundary intact:

- Productize per-agent Hermes homes without changing company identity.
- Formalize per-task Honcho session mapping.
- Wrap the sequence in a higher-level idempotent node/company bootstrap command.
- Add migration tooling for deliberate company moves between nodes.
- Add stronger verification around Honcho workspace and peer behavior.

Future-state extensions belong outside the current module contract until proven:

- Gateway-first Paperclip execution.
- Shared memory fabric across companies.
- Alignment logs, shared graph, and shared vector corpus promotion flows.
- Provider-swappable role cognition.
