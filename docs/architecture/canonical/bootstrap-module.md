# Direct Paperclip/Hermes Bootstrap Module

This document describes the proven Paperclip/Hermes bring-up work as a
contained reusable module inside the larger architecture.

## Module Name

Direct Paperclip/Hermes company bootstrap module

## Purpose

Turn the active direct hermes_local runtime contract into a repeatable
company-launch block that can be reused on VPS nodes.

This module is not the whole architecture.

It is the reusable block that:

- creates a company execution boundary
- wires Hermes into that boundary
- prepares self-hosted Honcho integration when enabled
- validates that the lifecycle actually works

## Inputs

Operator inputs:

- Paperclip base URL / auth context
- topology:
  - one-agent
  - manager-worker
- company name
- optional company description
- model
- agent names/roles/titles when defaults are not acceptable
- validation issue title/body

Generated defaults:

- company-scoped HERMES_HOME
- `adapterConfig.env.HERMES_HOME`
- honcho.json
- validation bodies when omitted
- verification API paths in script output

## Outputs

The module produces:

- created or reused Paperclip company
- created or reused Paperclip agent(s)
- prepared company HERMES_HOME
- rendered .env, config.yaml, honcho.json
- validation issue
- bounded run proof artifacts:
  - issue ID
  - run ID
  - completion comment
  - attribution fields

## Responsibilities

The module is responsible for:

- create/reuse company
- prepare company-scoped Hermes home
- create/reuse agents
- render honcho.json
- assign active hermes_local runtime config
- create validation issue
- prove lifecycle with a bounded task

It is not responsible for:

- outer Hermes bootstrap
- gateway-first execution
- generalized company autonomy
- per-agent Hermes-home redesign
- long-term shared memory fabric

## Current Implementations

Core scripts:

- stack/prototype-local/scripts/prepare_paperclip_hermes_home.py
- stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py

Bootstrap inputs:

- stack/prototype-local/templates/paperclip-hermes-one-agent.json
- stack/prototype-local/templates/paperclip-hermes-manager-worker.json

## Supported Topologies

### One-Agent

Use when the company is a compressed single-agent org.

### Manager-Worker

Use when the company needs one delegating manager and one worker.

## Current Limitation

Manager/worker currently shares one company-scoped HERMES_HOME.

That means:

- company isolation is real
- per-agent local Hermes-home isolation is not yet implemented

Do not describe the current manager/worker shape as per-agent Hermes memory
isolation.

## Guarantees

When the module succeeds on the active direct path, it guarantees:

- the company uses direct per-company hermes_local
- the company has an explicit HERMES_HOME
- honcho.json is rendered for the company
- the validation issue is runnable
- successful bounded tasks can end done
- final completion uses one PATCH with both status and comment

## Dependencies

The module depends on:

- healthy Paperclip API
- hermes CLI inside the Paperclip execution environment
- writable company data tree owned by the Paperclip runtime UID/GID
- self-hosted Honcho when Honcho-backed memory is enabled
- correct root/env projection into generated runtime files

## Boundaries

This module owns:

- company bring-up on the active direct path
- company-local Hermes runtime preparation
- validation of the active task lifecycle

This module stops at:

- a successfully bootstrapped and validated company

Everything after that is organizational behavior, not bootstrap.

## Failure Modes

Known failure classes:

- wrong or ambient HERMES_HOME
- missing honcho-ai dependency in the runtime
- root-owned company tree
- unresolved adapter env binding objects
- assignment/task fields not reaching the adapter
- child issue create-time assignment race
- comment/wake attribution errors

See:

- [../paperclip-hermes-local-contract.md](../paperclip-hermes-local-contract.md)
- [../pitfalls-and-recoveries.md](../pitfalls-and-recoveries.md)

## Sequencing Rules Learned From Proofs

These are part of the module contract now:

1. rerender honcho.json after agent creation
2. child issue creation must be linked/unassigned first, then activated
3. issue completion must be explicit, not inferred from process exit

### Manager/Worker Sequencing Rule

To avoid the create-time assignment race:

1. create linked child with parentId
2. leave it unassigned / `backlog`
3. activate it later with one PATCH setting:
   - `assigneeAgentId`
   - status: "todo"

## Lessons Learned / Gotchas

- HERMES_HOME is the true local memory boundary
- Honcho is additive, not the whole memory system
- ownership/permissions are part of correctness
- service env precedence can silently break Honcho
- tracing and memory are different concerns

## Extension Points

Safe near-term extensions:

- template-backed bootstrap inputs
- manager/worker defaults
- richer validation harnesses
- tighter runbook/operator ergonomics

Deferred extensions:

- per-agent Hermes homes
- per-task Honcho session mapping
- broader company templates
- alignment-log / graph / vector shared organizational memory fabric

