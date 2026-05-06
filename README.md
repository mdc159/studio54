# Studio54 Bootstrap

Studio54 Bootstrap is a self-contained baseline for bringing up an integrated
Hermes Agent, Paperclip company, and private local-AI service node.

The repo is designed to seed a repeatable installation that can run on its own
as a single useful VPS, or act as one node in a larger multi-node deployment.
Each node can carry a specific role, such as orchestration, media generation,
workflow automation, memory, observability, or development/testing.

This is not just a mirror of upstream projects. The repo owns the bootstrap
contract: how the services are assembled, how Hermes and Paperclip work
together, how traces are correlated, how private operator access is exposed,
and how a node can be reproduced.

## What This Repo Boots

The current node shape combines:

- **Paperclip** as the company and issue orchestration surface.
- **Hermes Agent** as the execution runtime for Paperclip-local agents.
- **`hermes_local`** as the active direct Paperclip-to-Hermes execution path.
- **Langfuse** as the downstream observability service for model-call traces.
- **Open WebUI** as a human-facing AI surface.
- **n8n** and **n8n-mcp** for workflow automation and structured workflow
  access.
- **ComfyUI** as the local media-generation worker.
- **Postgres, Valkey, MinIO, ClickHouse, Qdrant, and Neo4j** as the durable
  substrate services inherited from the local-AI packaged stack and adapted
  into this node model.
- **Broker API** as the repo-owned continuity/event plane for future
  cross-service and cross-node coordination.

The active Paperclip execution contract is direct per-company `hermes_local`.
The current `main` branch carries run ID correlation between Paperclip, Hermes,
and Langfuse, plus the Langfuse traceability contract, prompt/output capture
policy, and operator documentation merged in PR #5.

## Why It Exists

The purpose of this repo is to make a private AI company node repeatable.

The intended outcome is:

1. Start from a fresh VPS or local Linux machine.
2. Project the repo-owned environment contract.
3. Bring up the service substrate.
4. Bootstrap a Paperclip company with Hermes-capable agents.
5. Observe model behavior and failures through Langfuse.
6. Reuse the same pattern for additional nodes with different roles.

The repo should give future operators and agents a known baseline instead of a
collection of one-off setup notes.

## Current Status

The current proven target is a private-first node:

- app services bind to loopback on the node
- operator access is private, normally through Tailscale
- Paperclip runs as a containerized app-plane service
- Hermes for Paperclip tasks runs inside the Paperclip execution environment
- outer/operator Hermes remains separate from Paperclip-internal Hermes runs
- Langfuse metadata tracing is available for OpenAI-compatible Hermes model
  calls
- fuller Langfuse content capture is available behind the explicit
  `LANGFUSE_CAPTURE_CONTENT=true` opt-in

PR #5 merged the clean Langfuse traceability integration into `main` and
superseded the stale `langfuse-sidecar` PR.

## Repo Layout

| Path | Purpose |
|---|---|
| `docs/architecture/` | Canonical architecture, contracts, runbooks, current state, and integration notes. |
| `docs/audits/` | Three-way doc/code/VPS audits. Latest: [2026-05-01 summary](docs/audits/2026-05-01-three-way/summary.md). |
| `stack/prototype-local/` | Main Docker Compose substrate and bootstrap scripts for the node. |
| `stack/broker/` | Repo-owned broker API service for continuity/event coordination. |
| `stack/sql/` | Broker schema migrations. |
| `stack/topology/` | Service, target, and role declarations for repeatable node composition. |
| `stack/roles/` | Role-specific compose overlays for future specialized nodes. |
| `deploy/vps/` | VPS installation and operator runbook material. |
| `modules/` | Vendored upstream snapshots. Some are runtime inputs today; they are not live-updating Git submodules. |
| `agent-knowledge-exchange/` | Shared operational knowledge and skills used around the node. |

## Important Docs

Start here:

- [Reference Node Target](docs/architecture/reference-node-target.md) explains
  the correct private-first node shape.
- [Current State](docs/architecture/current-state.md) records what is actually
  in the repo today.
- [Deployable Unit](docs/architecture/deployable-unit.md) maps the fragmented
  runtime, workflow, company, host, and proof pieces into one node shape.
- [Reconstruction Plan](docs/architecture/reconstruction-plan.md) lists the
  implementation path back to a repeatable VPS deployable unit.
- [Paperclip `hermes_local` Contract](docs/architecture/paperclip-hermes-local-contract.md)
  defines how Paperclip runs Hermes directly.
- [Company Bootstrap](docs/architecture/company-bootstrap.md) explains the
  repeatable Paperclip company setup.
- [Remote Persona Grid](docs/architecture/remote-persona-grid.md) defines the
  Donna-controlled SSH/tmux grid for remote Hermes personas such as Victoria.
- [Full Operation Roadmap](docs/architecture/full-operation-roadmap.md) lays out
  the path from validated agents to real work with Donna, Victoria,
  Android/Termux, Nikolai, Paperclip, and the audit ledgers.
- [Nikoli WSL Workstation Node Card](docs/architecture/nikoli-wsl-node-card.md)
  records the validated Donna -> Tailscale SSH -> WSL tmux/Hermes pattern for
  the first workstation persona.
- [Nikoli Paperclip Catch-up Assessment](docs/architecture/nikoli-paperclip-catchup.md)
  bridges Nikoli's validated live-attach state with the existing Paperclip
  `hermes_local` bootstrap research and sea-base experimentation evidence.
- [Hermes Agent Backup and Restore Runbook](docs/architecture/hermes-agent-backup-restore-runbook.md)
  defines the recovery layers for Hermes personas, Honcho memory, Paperclip
  company-local agents, snapshots, and delegated/forked agent execution modes.
- [VPS Install Runbook](deploy/vps/INSTALL.md) is the operator-oriented setup
  path.
- [Plans](docs/plans/README.md) keeps the original verifier-first plan and the
  adjusted plan that has actually been executed.

The fuller Langfuse integration narrative and traceability contract now live in
[Langfuse Integration Status](docs/architecture/langfuse-integration-status.md)
and [Langfuse Traceability](docs/architecture/langfuse-traceability.md). Use
[Current State](docs/architecture/current-state.md),
[Deployable Unit](docs/architecture/deployable-unit.md), and
[Paperclip `hermes_local` Contract](docs/architecture/paperclip-hermes-local-contract.md)
for the current execution baseline.

Historical or aspirational design docs still exist, but the reference-node and
contract docs above are the practical starting point for current work.

The [2026-05-01 three-way audit](docs/audits/2026-05-01-three-way/summary.md)
cross-checked 2258 claims extracted from all owned docs against the codebase
and a live VPS dump. Headline: 690 MATCH, 29 DRIFT, 1539 UNVERIFIABLE.
See the [ledger](docs/audits/2026-05-01-three-way/ledger.csv) for the full
per-claim breakdown and suggested fixes.

## Bootstrap Shape

At a high level, a node is prepared by:

1. Cloning this repo onto the target machine.
2. Creating the root `.env` from `.env.example`.
3. Projecting root env values into the stack-local env.
4. Starting the Docker Compose substrate under `stack/prototype-local/`.
5. Preparing Paperclip's embedded Hermes runtime.
6. Creating a Paperclip company and one or more `hermes_local` agents.
7. Running a validation issue through Paperclip and confirming run correlation.

The concrete command sequence lives in [deploy/vps/INSTALL.md](deploy/vps/INSTALL.md)
and the helper scripts under `stack/prototype-local/scripts/`.

## Traceability Direction

On the active direct `hermes_local` path, one run ID is intended to link the
stack:

- `PAPERCLIP_RUN_ID`
- `HERMES_RUN_ID`
- `LANGFUSE_TRACE_ID`

On `main`, this correlation exists for the active Paperclip/Hermes path and
Langfuse metadata tracing. The PR #5 traceability work also documents
OpenAI-compatible request messages as Langfuse generation input, final
assistant text as generation output, content-capture controls, truncation
metadata, and operator run-record expectations.

Langfuse is downstream observability. It is not the source of truth for task
state, approvals, company state, artifacts, or memory. Paperclip owns company
and issue state. Hermes owns runtime execution. Langfuse records what happened
inside model calls so debugging, evaluation, and later learning workflows have
evidence.

## Multi-Node Direction

The repeatable node is the unit of growth. A single VPS can run the full
baseline stack. A larger deployment can split responsibilities across nodes:

- orchestration and company operations
- media generation
- workflow automation
- retrieval and memory services
- observability and evaluation
- development or test nodes

The role and topology manifests under `stack/topology/` and `stack/roles/`
exist to make that split explicit over time. Today, the reference node remains
the primary proven unit.

## Vendored Modules

The repo carries upstream projects as vendored snapshots and integration
inputs. They are tracked as ordinary files in this repo, not as active Git
submodules, and they do not update automatically.

- `modules/local-ai-packaged`
- `modules/hermes-agent`
- `modules/hermes-paperclip-adapter`
- `modules/hermes-agent-self-evolution`
- `modules/autoreason`
- `modules/paperclip`
- `modules/honcho`
- `modules/n8n-mcp`

Studio54 Bootstrap is responsible for how these pieces are assembled into a
working node. Runtime-required vendored modules should eventually be replaced
with pinned images, packages, or explicit vendor-update scripts where practical.

## Current Cleanup Goal

The immediate cleanup goal is to keep `main` as the canonical baseline after
the Langfuse traceability branch merged, retire stale sidecar state, and move
new work through verifier-first PRs.

That should leave:

- one current `main`
- one clear Paperclip/Hermes/Langfuse traceability contract
- one repeatable bootstrap baseline for future nodes
