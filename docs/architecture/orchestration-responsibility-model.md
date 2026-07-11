# Orchestration Responsibility Model

This document is the current Studio54 contract for Paperclip, Hermes Kanban,
n8n, and the outer Donna/operator plane. It preserves the integrated node:
none of these systems is deprecated or replaced by another.

## Decision

Studio54 remains a valid node unit. Keep the complete service set and assign
one authoritative responsibility to each orchestration surface.

| Surface | Authority | Canonical state | Must not become |
|---|---|---|---|
| Donna / outer Hermes | Fleet and portfolio governance | Node policy, routing decisions, executive synthesis, escalations | A normal Paperclip agent with ambient cross-company access |
| Paperclip | Company governance and accountability | Company, goals, org tree, projects, issues, budgets, approvals, routines | A low-level API workflow engine or cross-company memory fabric |
| Hermes Kanban | Host-local durable agent execution | Task DAG, profile assignment, attempts, blocks, retries, worker evidence | A corporate org chart, portfolio authority, or cross-host SQLite mesh |
| n8n | Deterministic integration and policy execution | Trigger state, transformations, API receipts, retries, idempotent routing | An autonomous CEO or source of company approval |
| Broker/event plane | Cross-system lineage and delivery contracts | Correlation, immutable events, delivery/replay state | A substitute for company work state or private cognition |
| Human board | Consequential authority | Public, financial, legal, safety, relationship, and irreversible approvals | An invisible assumption inside agent prompts |

## Why the systems overlap without replacing each other

All three primary surfaces can display or trigger “work,” but their semantics
differ:

- A Paperclip issue records why a company needs a result and who is accountable.
- A Kanban card records which Hermes profile must execute a durable technical
  step and what evidence it returned.
- An n8n execution records which deterministic integration steps fired and
  whether transport/policy handling succeeded.

A card is not proof that an issue completed. A successful process is not proof
that an API mutation occurred. A webhook receipt is not approval. Completion
must be demonstrated at the authoritative boundary.

## Hierarchy model

Studio54 has three distinct hierarchies:

1. **Fleet hierarchy:** Mike/human board → Donna → enabled nodes/personas.
2. **Company hierarchy:** human board → company CEO → managers → workers.
3. **Execution hierarchy:** Kanban orchestrator → specialist task DAG → review
   and remediation.

```text
Mike / human board
└── Donna / external portfolio and fleet governor
    ├── 1215 Productions Paperclip company
    │   └── company CEO → managers → workers
    ├── research/incubator Paperclip company
    │   └── research director → specialists
    └── enabled Hermes nodes
        └── node-local Kanban boards → profile workers
```

Paperclip companies are peer top-level scopes. A Paperclip agent belongs to one
company, and company-agent credentials must not cross company boundaries.
Donna therefore operates outside company-local identities through board-level
or narrowly scoped portfolio integration.

## Kanban tenancy and node boundaries

Hermes Kanban is single-host by design:

- a board is a hard local boundary with its own SQLite database, workspaces,
  logs, and dispatcher context;
- a tenant is a soft string namespace within one board;
- an assignee is a local Hermes profile name;
- task links form execution dependencies, not manager ACLs;
- boards are not shared automatically across VPSs or devices.

Do not place `kanban.db` on NFS/SMB or synchronize it between nodes. Cross-node
work requires an explicit delivery service with node identity, authentication,
idempotency, acknowledgement, retries, leases/fencing, dead-letter handling,
and artifact transport.

## Current verified Studio54 state

Read-only inspection on 2026-07-11 found:

- Paperclip `0.3.1`, private/local-trusted and healthy;
- 17 preserved proof/model-comparison companies;
- 24 agents, all using `hermes_local`;
- 49 issues: 33 roots and 16 children;
- zero projects, goals, routines, and approvals;
- zero populated `reportsTo` relationships;
- zero CEO-role agents.

The estate is an integration laboratory, not an operating portfolio.

Historical manager/worker fixtures prove parent/child issue delegation:
manager-owned parents and worker-owned children completed with the expected
linkage. They do not prove a formal Paperclip reporting tree because all
inspected agents have `reportsTo = null`.

The current/proven Paperclip execution path is direct in-container
`hermes_local` with a company-scoped `HERMES_HOME`. The older host Hermes
gateway/UDS design is optional future scaffolding and must not be described as
the active company execution contract.

## Productive-work transition

Kanban can replace the historical human copy/paste relay for proof execution on
the Studio54 host:

```text
Kanban proof root
├── read-only inventory
├── formal-org canary
├── delegation/completion proof
├── approval and blocked-recovery proof
├── memory-isolation proof
├── restart/retry/idempotency proof
└── evidence synthesis
```

Kanban coordinates the experiment. Paperclip remains the system under test and
the authority for company state. Existing proof scripts audit the result. n8n
is added after the core Paperclip behavior is green, then owns deterministic
transport and policy enforcement.

The implementation-ready program is:

- [Kanban-Coordinated Paperclip Proof Program](../plans/2026-07-11-kanban-paperclip-proof-program.md)
- [Paperclip Completion Proof Program](../proofs/paperclip-kanban-completion-program.md), the detailed canary manifest, experiment matrix, memory-isolation contract, and evidence-bundle specification

## Approval boundary

Read-only inventory, plan generation, local static validation, and repository
work may run without a live mutation approval. Creating or modifying a
Paperclip company, agent, goal, project, routine, approval, or issue requires a
separately approved canary scope and mutation budget.

No proof program may publish content, contact talent, spend funds, make legal or
safety claims, or perform irreversible actions.

## First productive pilot

After the disposable formal-org canary is green, run one research-only 1215
issue: prepare an evidence-backed archive-to-campaign candidate brief. It must
produce an internal artifact only. Public action remains human-approved and out
of scope.
