# Agent Knowledge Exchange

This document defines how the shared knowledge repo fits into Studio54
operations.

Repository:

- `mdc159/agent-knowledge-exchange`

Known local clone path on VPS nodes:

- `/opt/agent-knowledge-exchange`

Known node-local secret loader:

- `/root/.config/agent-knowledge-exchange/env`

## Purpose

The knowledge repo is for reusable operational knowledge that should survive
one agent session, one node, or one company.

It is not the runtime system of record. Paperclip remains the system of record
for company issues, agents, comments, and workflow state.

## What Belongs There

Use the knowledge repo for:

- reusable setup findings
- installation notes
- postmortems
- cross-node operational lessons
- stable runbooks
- skill promotion notes
- durable documentation that multiple agents should be able to discover

Example from the fresh-node work:

- Paperclip can run `hermes_local` only if Hermes exists inside the Paperclip
  execution environment.
- Company Hermes homes must be owned by the Paperclip runtime UID/GID.
- Local adapters must receive resolved runtime config, not persisted binding
  objects.

## What Does Not Belong There

Do not use the knowledge repo as:

- a replacement for Paperclip issue state
- a live task queue
- a secret store
- a database backup
- an unfiltered dump of runtime logs
- a place for company-private memory unless it has been intentionally promoted

## Issues vs PRs

Use issues for:

- coordination
- findings that need follow-up
- open questions
- requests for consolidation
- proof summaries

Use PRs for:

- durable docs changes
- runbook updates
- reviewed knowledge additions
- cross-linked operational notes

Observed example:

- issue #6 captured the fresh-node `hermes_local` proof and the second proof
  update.
- PaperHermes PR #4 captured Paperclip installation/access notes.

## Backups vs Runtime State

The knowledge repo can preserve operational knowledge. It is not a live backup
of Paperclip, Hermes, databases, or volumes.

Backups must preserve runtime state through the appropriate storage layer:

- Docker volumes
- database backups
- filesystem snapshots
- Paperclip exports if/when used

The knowledge repo can document how backups work, but it does not replace them.

## Bot Token Model

Known proven pattern:

- each node has a local clone at `/opt/agent-knowledge-exchange`
- each node has a local secret loader at
  `/root/.config/agent-knowledge-exchange/env`
- nodes have distinct git identities:
  - `PaperHermes`
  - `Donna`
  - `FreshHermes`

The working model is fine-grained bot access per agent/node, loaded locally on
the node instead of committed into the repo.

Current required repository permissions:

- `Contents`: read/write
- `Issues`: read/write
- `Pull requests`: read/write
- `Metadata`: read-only

Do not use this repo as a reason to distribute a broad personal token.

Open questions:

- token rotation procedure
- whether each long-lived agent should always have a distinct GitHub identity

## Promotion Rules

Default rule:

- company memory is local
- skills and stable operational knowledge can become global
- promotion must be explicit

Promotion path:

1. discover a finding during a company or node run
2. record immediate technical state in the relevant repo/handoff if it changes
   runtime contract
3. distill reusable operational knowledge
4. add it to `agent-knowledge-exchange` as an issue comment, issue, or PR
5. convert repeatable behavior into a skill only after it is stable enough to
   reuse

Do not promote raw company/task memory just because it exists.

## Relationship To Studio54 Docs

Studio54 docs are the source for this repo's node architecture and runbooks.

`agent-knowledge-exchange` is the shared cross-agent knowledge layer. When a
finding changes the Studio54 runtime contract, update Studio54 docs. When a
finding is reusable across operators, nodes, or future companies, promote the
distilled lesson to the knowledge repo.
