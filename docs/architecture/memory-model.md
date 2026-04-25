# Memory Model

This document captures the documented Hermes, Honcho, and Paperclip memory and
state boundaries used for Studio54 planning.

It separates documentation facts from architecture inference. Do not treat the
inferred mappings as proven runtime behavior until a dedicated verification
slice confirms them.

Primary related docs:

- Hermes runtime boundaries: [hermes-runtime.md](hermes-runtime.md)
- Paperclip `hermes_local` contract:
  [paperclip-hermes-local-contract.md](paperclip-hermes-local-contract.md)
- Company bootstrap path: [company-bootstrap.md](company-bootstrap.md)

## Hermes Documented Memory

Hermes memory is more than Honcho.

Documented Hermes memory/state layers:

- built-in persistent memory:
  - `MEMORY.md`
  - `USER.md`
- session/history storage and search in `~/.hermes/state.db`
- skills as procedural memory
- context files that shape prompts
- cached prompt layers and API-call-time runtime additions
- optional external memory providers such as Honcho
- profiles as state-directory isolation boundaries

Built-in memory:

- `MEMORY.md` stores agent/environment notes, workflows, project conventions,
  tool quirks, completed-task diary entries, and lessons learned.
- `USER.md` stores user identity, preferences, communication style, workflow
  habits, and related profile information.
- both files live under `~/.hermes/memories/` by default.
- both are injected as a frozen snapshot at session start.
- mid-session memory writes persist to disk immediately but do not update the
  already-built system prompt until a later session or prompt rebuild.

Session/history recall:

- Hermes stores session metadata, full message history, and model config in
  SQLite at `~/.hermes/state.db`.
- session search is separate from built-in memory.
- built-in memory is for critical facts that should always be in context.
- session search is for finding specific past conversations on demand.

Skills:

- skills live primarily under `~/.hermes/skills/`.
- skills are on-demand procedural knowledge.
- Hermes normally sees an index before loading full instructions.
- agent-managed skills are a way to save repeatable non-trivial workflows for
  later reuse.

Context files:

- supported context files include `.hermes.md`, `HERMES.md`, `AGENTS.md`,
  `CLAUDE.md`, `.cursorrules`, `.cursor/rules/*.mdc`, and global `SOUL.md`.
- `SOUL.md` is loaded from `HERMES_HOME` as the Hermes instance identity.
- project context is discovered from the working directory by priority.

Prompt assembly:

- cached layers include agent identity, Honcho static block when active, frozen
  `MEMORY`, frozen `USER`, skills index, context files, timestamp/session ID,
  and platform hint.
- API-call-time-only additions include ephemeral system prompts, prefill
  messages, gateway/session overlays, and later-turn Honcho recall injected into
  the current user message.

Profiles:

- a Hermes profile is a separate Hermes home directory.
- a profile has its own `config.yaml`, `.env`, `SOUL.md`, memories, sessions,
  skills, cron jobs, and state database.
- profiles isolate Hermes state.
- profiles are not filesystem sandboxes.

External providers:

- Honcho and other external providers are additive.
- built-in memory remains active alongside an external provider.
- Hermes supports only one active external provider at a time.
- provider integrations can inject context, prefetch relevant memories, sync
  turns, extract memories at session end, mirror built-in memory writes, and add
  provider-specific tools.

Honcho as a Hermes provider:

- Honcho is documented as an external provider for cross-session user modeling.
- Hermes' Honcho integration includes session-scoped context injection,
  semantic search, persistent conclusions, and dialectic reasoning.
- documented Honcho tools include `honcho_profile`, `honcho_search`,
  `honcho_context`, `honcho_reasoning`, and `honcho_conclude`.

## Honcho Documented Memory

Honcho is an open-source memory library with a managed service. It is
model/framework/architecture agnostic and is designed to maintain state about
changing entities over time.

Core primitives:

- Workspace
- Peer
- Session
- Message

Hierarchy:

- a Workspace contains Peers and Sessions
- a Peer can participate in multiple Sessions
- a Session can contain multiple Peers
- Messages are ordered within a Session and attributed to a Peer

Workspace:

- top-level isolation boundary
- can isolate applications, environments, or tenants
- authentication is scoped at the workspace level
- workspace configuration can affect peers and sessions

Peer:

- persistent entity inside a workspace
- can represent a user, agent, group, idea, or other entity
- carries reasoning across that peer's sessions
- supports cross-session representations

Session:

- temporal interaction thread or context
- can include multiple peers
- can scope task/conversation context while preserving longer-term peer
  representations
- can also be used for importing external data into a peer context

Message:

- fundamental unit of interaction
- can represent conversation turns, emails, documents, files, user actions,
  system notifications, or rich media
- stored immediately
- triggers asynchronous reasoning

Representations:

- Honcho's reasoned memory layer for a peer
- include conclusions, summaries, and peer cards
- reasoning can be deductive, inductive, or abductive
- background reasoning tasks update peer representations and retrieval indexes

Observation boundaries:

- `observe_me` controls whether Honcho forms a representation of a peer from
  that peer's own messages.
- `observe_others` controls whether a peer forms representations of other peers
  from observed messages.
- different peers can have different representations of the same entity.

Deployment:

- Honcho supports managed and self-hosted modes.
- self-hosting uses PostgreSQL/pgvector, Redis, an API process, and a deriver
  worker.
- the deriver is required for memory/reasoning because it processes messages
  into observations, representations, summaries, and consolidation.

## Paperclip Documented Boundary

Paperclip is the control plane for autonomous AI companies.

Documented Paperclip ownership:

- companies
- agents
- org structure
- goals
- issues/tasks
- assignments and checkout
- budgets and token spend tracking
- heartbeats
- run records
- governance

Paperclip execution boundary:

- Paperclip orchestrates agents.
- agent execution happens through adapters.
- on heartbeat, Paperclip calls the adapter's `execute()` function.
- the adapter invokes the configured runtime.
- the runtime works and reports back through Paperclip APIs.
- Paperclip records run result, costs/usage, and session state for future runs.

Paperclip is not documented as the long-term cognitive memory store for agent
runtimes. It owns control-plane and workflow state.

## Inferred Mapping For Studio54

The following mapping is inferred from product docs. It is not yet proven
runtime behavior in Studio54.

| Combined-system concept | Recommended mapping | Basis |
| --- | --- | --- |
| Company tenant | Paperclip company plus Honcho workspace | Paperclip company boundary; Honcho workspace isolation |
| Outer Hermes | Separate Hermes profile plus Honcho peer in the relevant workspace | Hermes profile isolation; Honcho peer model |
| Paperclip-internal Hermes agent | Paperclip agent using `hermes_local`; separate Hermes state; separate Honcho AI peer | Paperclip adapter model; Hermes profile/state model; Honcho peer model |
| Task memory thread | Honcho session per Paperclip issue/task | Paperclip issue as work unit; Honcho session as temporal interaction thread |
| Event/turn data | Honcho messages plus Paperclip run records/status | Honcho messages trigger reasoning; Paperclip records runs/status |
| Long-term agent/user memory | Hermes local memory plus Honcho representations | Hermes built-in memory remains active; Honcho is additive |
| Procedural know-how | Hermes skills | Hermes skills are procedural memory |
| Control/governance | Paperclip | Paperclip owns company control-plane state |

Recommended default:

- Paperclip company is the control-plane tenant.
- Honcho workspace is the memory tenant.
- each durable actor is a Honcho peer.
- each Paperclip issue/task is a candidate Honcho session.
- each heartbeat is an execution window inside the task/session, not the
  top-level memory boundary.
- Honcho should not replace Hermes local memory.

## Open Questions

These are not answered by the docs and need dedicated verification/design:

- whether Studio54 should use managed Honcho, one shared self-hosted Honcho, or
  one self-hosted Honcho deployment per company
- whether Paperclip company IDs should map one-to-one to Honcho workspace IDs
- how Paperclip agent IDs, Hermes profile/home names, and Honcho peer IDs should
  be synchronized
- whether Honcho sessions should map to issues, heartbeats, projects,
  repositories, conversations, or agent relationships
- what Paperclip should store for Hermes/Honcho session handles or memory state
- whether Paperclip should enforce memory visibility policy or only provide
  company/task context
- how to provide filesystem/process isolation, since Hermes profiles are not
  filesystem sandboxes
- how conflicts should resolve between Hermes local memory and Honcho
  representations

## Sources

- Hermes persistent memory:
  https://hermes-agent.nousresearch.com/docs/user-guide/features/memory
- Hermes skills:
  https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
- Hermes memory providers:
  https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers
- Hermes context files:
  https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files
- Hermes prompt assembly:
  https://hermes-agent.nousresearch.com/docs/developer-guide/prompt-assembly
- Hermes profiles:
  https://hermes-agent.nousresearch.com/docs/user-guide/profiles
- Honcho overview:
  https://docs.honcho.dev/v3/documentation/introduction/overview
- Honcho architecture:
  https://docs.honcho.dev/v3/documentation/core-concepts/architecture
- Honcho representations:
  https://docs.honcho.dev/v3/documentation/core-concepts/representation
- Honcho reasoning:
  https://docs.honcho.dev/v3/documentation/core-concepts/reasoning
- Paperclip overview:
  https://docs.paperclip.ing/start/what-is-paperclip
- Paperclip core concepts:
  https://docs.paperclip.ing/start/core-concepts
- Paperclip architecture:
  https://docs.paperclip.ing/start/architecture
- Paperclip adapters:
  https://docs.paperclip.ing/adapters/overview
