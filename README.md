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
The current `main` branch already carries run ID correlation between
Paperclip, Hermes, and Langfuse. A separate integration branch, PR #5, is being
reviewed to incorporate the fuller Langfuse traceability knowledge, including
prompt/output capture policy and the expanded operator documentation.

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
- fuller Langfuse content capture and traceability documentation are pending in
  PR #5

PR #5 is the clean Langfuse traceability integration branch. It supersedes the
stale `langfuse-sidecar` PR and is intended to merge the additional Langfuse
knowledge into `main` after the broader Hermes/Paperclip confidence gate
completes.

## Repo Layout

| Path | Purpose |
|---|---|
| `docs/architecture/` | Canonical architecture, contracts, runbooks, current state, and integration notes. |
| `stack/prototype-local/` | Main Docker Compose substrate and bootstrap scripts for the node. |
| `stack/broker/` | Repo-owned broker API service for continuity/event coordination. |
| `stack/sql/` | Broker schema migrations. |
| `stack/topology/` | Service, target, and role declarations for repeatable node composition. |
| `stack/roles/` | Role-specific compose overlays for future specialized nodes. |
| `deploy/vps/` | VPS installation and operator runbook material. |
| `modules/` | Upstream modules used by the bootstrap: Paperclip, Hermes, Honcho, local-ai-packaged, n8n-mcp, and learning/eval references. |
| `agent-knowledge-exchange/` | Shared operational knowledge and skills used around the node. |

## Important Docs

Start here:

- [Reference Node Target](docs/architecture/reference-node-target.md) explains
  the correct private-first node shape.
- [Current State](docs/architecture/current-state.md) records what is actually
  in the repo today.
- [Paperclip `hermes_local` Contract](docs/architecture/paperclip-hermes-local-contract.md)
  defines how Paperclip runs Hermes directly.
- [Company Bootstrap](docs/architecture/company-bootstrap.md) explains the
  repeatable Paperclip company setup.
- [VPS Install Runbook](deploy/vps/INSTALL.md) is the operator-oriented setup
  path.

The fuller Langfuse integration narrative and traceability contract are pending
in PR #5. Until that branch merges, use [Current State](docs/architecture/current-state.md)
and [Paperclip `hermes_local` Contract](docs/architecture/paperclip-hermes-local-contract.md)
as the canonical docs on `main`.

Historical or aspirational design docs still exist, but the reference-node and
contract docs above are the practical starting point for current work.

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
Langfuse metadata-only tracing. PR #5 is the branch that incorporates the full
traceability work: OpenAI-compatible request messages as Langfuse generation
input, final assistant text as generation output, content-capture controls,
truncation metadata, and operator run-record expectations.

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

## Upstream Modules

The repo carries upstream projects as modules and integration inputs:

- `modules/local-ai-packaged`
- `modules/hermes-agent`
- `modules/hermes-paperclip-adapter`
- `modules/hermes-agent-self-evolution`
- `modules/autoreason`
- `modules/paperclip`
- `modules/honcho`
- `modules/n8n-mcp`

Studio54 Bootstrap is responsible for how these pieces are assembled into a
working node. Upstream modules remain their own projects; this repo defines the
deployment, contracts, and operational glue.

## Current Cleanup Goal

The immediate cleanup goal is to merge PR #5, the Langfuse traceability branch,
into one canonical branch after the broader Hermes/Paperclip test gate passes,
then retire stale sidecar state.

That should leave:

- one current `main`
- one clear Paperclip/Hermes/Langfuse traceability contract
- one repeatable bootstrap baseline for future nodes
