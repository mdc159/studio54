# Verifier-First Executed Plan

This records the plan as it was actually executed after the original
verifier-first proposal. It intentionally differs from the original plan where
the repo had already moved ahead.

## What Was Completed

Sequential PR work landed these verifier-first pieces:

- source-of-truth doc cleanup
- CODEOWNERS and protected-path evidence visibility
- node proof schema and contract
- simulated VPS memory canaries
- Paperclip manager/worker coordination proof script
- node proof collector and verifier
- `./bin/1215 proof node --json`
- `./bin/1215 company bootstrap --template-file`

Current validation lanes:

- `Studio54 validation`
- `VPS bootstrap simulation`
- local `./bin/1215 proof node --json`

## Current Documentation Reconciliation

The documentation pass added:

- `docs/architecture/current-state.md` as the repo-grounded factual snapshot
- `docs/architecture/deployable-unit.md` as the map of how fragmented pieces
  assemble into one node
- `docs/architecture/reconstruction-plan.md` as the path back to a repeatable
  VPS deployable unit
- Mermaid diagrams for the current system, six-lane assembly flow, runtime
  layers, and proof flow

It also corrected stale operator-facing references in `README.md`,
`stack/prototype-local/README.md`, `stack/roles/README.md`,
`docs/proofs/node-proof-contract.md`, and `stack/topology/targets.json`.

## Modules Decision

The `modules/` directory is not a set of live Git submodules in the current
repo. The modules are tracked as ordinary vendored source trees. They do not
update automatically.

Current treatment:

- Keep runtime-required vendored modules until the deploy unit no longer builds
  from them.
- Do not let root-level pytest recurse into upstream module tests.
- Remove stale `.gitmodules` metadata so agents do not assume
  `git submodule update` refreshes these directories.
- Later, replace vendored runtime source with pinned images, packages, or
  explicit vendor-update scripts where practical.

Runtime-required today:

- `modules/paperclip`: Paperclip compose image build context
- `modules/honcho`: host-native Honcho install source
- `modules/hermes-agent`: Hermes runtime/probe source used by validation and
  host/runtime scripts

Mostly reference or future-facing today:

- `modules/local-ai-packaged`
- `modules/hermes-paperclip-adapter`
- `modules/hermes-agent-self-evolution`
- `modules/autoreason`
- `modules/n8n-mcp`
- `modules/n8n-skills`

## Active Architecture Contract

- Paperclip execution path: direct `hermes_local`
- Runtime boundary: company-scoped `HERMES_HOME`
- Honcho workspace: Paperclip `companyId`
- Honcho AI peer: `paperclip-agent-<agentId>`
- Gateway path: scaffolded and deferred for Paperclip task execution
- Per-agent Hermes homes: deferred
- Per-task Honcho sessions: deferred
- Langfuse: downstream observability, not source of truth
- Paperclip: company, issue, comment, and run source of truth

## Next Work

1. Add a first-class VPS node manifest.
2. Make fresh-node host bootstrap idempotent.
3. Make host-native outer Hermes and Honcho installs rerunnable.
4. Integrate live/staging Paperclip coordination proof into node proof.
5. Produce a versioned deploy bundle only after a clean Ubuntu VM can emit a
   passing live proof.
