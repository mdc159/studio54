# Reconstruction Forensic Brief

Date: 2026-05-06

This brief consolidates the evidence from the prior session transcript, the
live VPS, the current repo branch, and the local Ubuntu VM. It is intended as a
second-opinion packet before starting the next reconstruction pass.

## Executive Summary

The earlier work is not lost. It exists in four different forms:

- the prior session transcript, which records the final working proof and the
  commit that was pushed at that time
- the live VPS, which still has the integrated service plane and Paperclip proof
  records
- the current `development` branch, which is being converted into the
  reproducible source of truth
- a local Ubuntu VM snapshot, which can be used as a disposable staging node

The main gap is not service availability. The live VPS still shows Paperclip,
Open WebUI, n8n, n8n-mcp, broker, Langfuse, storage services, and supporting
datastores running. The main gap is reproducibility and memory correctness:
Honcho is not currently healthy on the VPS, the expected company Hermes home for
the final template proof is not present at the configured path, and the live
deployment tree is not a Git checkout.

The most direct path forward is verifier-first reconstruction: freeze the
expected end-state proof, use the VPS only as forensic evidence, use the local
VM as the clean staging target, and iterate until a fresh Ubuntu node can
reproduce the working manager/worker Paperclip + Hermes + Honcho flow.

## Evidence Sources

### Prior Session Transcript

Source file inspected:

- `/mnt/d/Users/Mike/Downloads/company.txt`

The file is 7,160 lines long. Its tail reports the final implementation slice:

- `bootstrap_paperclip_hermes_company.py` gained `--template-file <path>`
- two templates were added:
  - `stack/prototype-local/templates/paperclip-hermes-one-agent.json`
  - `stack/prototype-local/templates/paperclip-hermes-manager-worker.json`
- template validation rejects unknown or unsupported shape
- both templates use the direct `hermes_local` path and company-scoped
  `HERMES_HOME`
- the reported final commit was pushed to `main`:
  - `407e8b293c4c084afbc0bc8b94f4232a391273e2`
  - message: `Add template-backed Paperclip Hermes bootstrap`

The transcript reports a bounded live manager/worker proof on `srv1264451`:

- company: `05040f4c-b849-48f5-a2c3-ab009bf593a0`
- manager: `9f6d5c30-fec6-4029-9f97-9536b02685b4`
- worker: `4bb38c47-f6b2-4f6f-a53c-461cf323be21`
- parent issue: `TEM-1 / 0c7f650d-3fd2-44c0-92b0-8f76c0dd5eed`
- child issue: `TEM-2 / b90ae265-07fe-435e-b6a8-c4c7ea7a9c3e`

Reported result:

- parent and child ended `done`
- child had the correct `parentId`
- manager and worker runs succeeded
- comments had the correct `authorAgentId` and `createdByRunId`
- no failed worker assignment run was observed

The transcript also records that documentation still needed to mention
`--template-file` and the example templates.

### Live VPS

Host:

- public IP: `191.101.0.164`
- hostname observed: `srv1264451`
- OS/kernel observed: Ubuntu host with Linux `6.8.0-107-generic`

The VPS still has the broad integrated service plane running under Docker:

- Paperclip
- Open WebUI
- broker
- n8n
- n8n-mcp
- Langfuse web and worker
- Postgres
- Qdrant
- ClickHouse
- Neo4j
- Valkey
- MinIO
- ComfyUI

Read-only health checks passed for:

- broker `/healthz`
- Paperclip `/api/health`
- n8n-mcp `/health`
- Langfuse `/api/public/health`
- ComfyUI `/system_stats`

Tailscale Serve was configured for the operator-facing services:

- `8443 -> 127.0.0.1:3100` Paperclip
- `8444 -> 127.0.0.1:8080` Open WebUI
- `8445 -> 127.0.0.1:5678` n8n
- `8446 -> 127.0.0.1:3000` Langfuse
- `8447 -> 127.0.0.1:13000` n8n-mcp
- `8448 -> 127.0.0.1:7474` Neo4j
- `8449 -> 127.0.0.1:6333` Qdrant
- `8450 -> 127.0.0.1:9011` MinIO Console
- `8451 -> 127.0.0.1:9010` MinIO API
- `8452 -> 127.0.0.1:8188` ComfyUI

The final template-proof company from the transcript still exists in Paperclip:

- company: `05040f4c-b849-48f5-a2c3-ab009bf593a0`
- name: `Template File Manager Worker Proof`
- issue prefix: `TEM`
- issue counter: `2`
- status: `active`

The final proof issues still exist:

- `TEM-1`
  - id: `0c7f650d-3fd2-44c0-92b0-8f76c0dd5eed`
  - status: `done`
  - assignee: `9f6d5c30-fec6-4029-9f97-9536b02685b4`
  - parent: none
- `TEM-2`
  - id: `b90ae265-07fe-435e-b6a8-c4c7ea7a9c3e`
  - status: `done`
  - assignee: `4bb38c47-f6b2-4f6f-a53c-461cf323be21`
  - parent: `0c7f650d-3fd2-44c0-92b0-8f76c0dd5eed`

The final proof agents still exist:

- manager: `9f6d5c30-fec6-4029-9f97-9536b02685b4`
- worker: `4bb38c47-f6b2-4f6f-a53c-461cf323be21`
- both have `adapterType: hermes_local`
- both point at:
  - `/paperclip/instances/default/companies/05040f4c-b849-48f5-a2c3-ab009bf593a0/hermes-home`

Forensic mismatch:

- only three company Hermes homes were visible under
  `/paperclip/instances/default/companies`
- the final template-proof company's expected `hermes-home` path was not among
  the visible company homes
- `honcho.service` exists but was not healthy during inspection
- `http://127.0.0.1:18000/health` did not respond
- `honcho-deriver.service` was inactive/dead
- `/opt/studio54-bootstrap` exists but is not a Git checkout

This means the VPS is close to the remembered app/service state and still
contains the Paperclip proof records, but it is not a clean source-of-truth
deployment and it does not currently prove the Honcho memory layer.

### Current Repo Branch

Local branch:

- `development`

Current HEAD at the time of this brief:

- `28d2e4b8e7254b48c1de32f57cc8388ad4e6623a`

Branch relationship:

- `development` is tracking `origin/development`
- working tree was clean before this brief was added

Current repo direction already added on `development`:

- [docs/architecture/deployable-unit.md](../architecture/deployable-unit.md)
- [docs/architecture/reconstruction-plan.md](../architecture/reconstruction-plan.md)
- [docs/plans/verifier-first-original-plan.md](verifier-first-original-plan.md)
- [docs/plans/verifier-first-executed-plan.md](verifier-first-executed-plan.md)
- node proof schema/verifier/collector work
- simulation memory canaries
- `./bin/1215 proof node --json`
- `./bin/1215 company bootstrap --template-file`

The current repo is ahead of the live VPS in documentation, proof scaffolding,
and branch hygiene. The live VPS is ahead of the repo in real historical
runtime evidence.

### Local Ubuntu VM

Host:

- IP: `192.168.119.129`
- user: `mike`
- key: `/mnt/c/Users/Mike/.ssh/id_ed25519_ubuntu_vm`
- hostname: `mike-VMware-Virtual-Platform`
- OS: Ubuntu `24.04.4 LTS`

Read-only inspection found:

- Docker installed and active
- Docker Compose installed
- `mike` is in the `docker` group
- passwordless sudo is configured
- about `80G` free disk
- about `7.7G` RAM
- no running containers
- no Docker images or volumes
- no Studio54 checkout under `/home/mike` or `/opt`
- no obvious old stack state

Missing prerequisites observed:

- `uv`
- Node 20+
- npm/pnpm
- Tailscale

The VM appears to be a good clean staging node. Because a VM snapshot exists, it
can be restored repeatedly and used as the automated reconstruction loop target.

## Interpretation

The historical system got farther than the current docs alone imply. The VPS
still proves that the integrated stack shape existed:

- Paperclip service plane
- workflow plane with Open WebUI, n8n, and n8n-mcp
- observability/support plane with Langfuse and storage services
- Paperclip manager/worker company proofs
- direct `hermes_local` execution path

The discrepancy that triggered the reproducibility pause was real:

- Paperclip agent records say company-scoped Hermes homes should exist
- Honcho was intended to back memory through `honcho.json`
- the live filesystem and service state no longer fully support that claim

Therefore the reconstruction should not start by broadening features. It should
first make the remembered working state reproducible and make the memory model
provable.

## Proposed Operating Model

Use each available resource for a different job:

- `company.txt`: historical transcript and final proof facts
- live VPS: read-only forensic reference
- `development` branch: source-of-truth implementation
- local VM: disposable staging verifier
- GitHub Actions: simulation and regression verifier

Do not hand-fix the live VPS until the VM can reproduce the node from the repo.

## Immutable End-State Proof

Before iterating on the installer, define the end-state proof contract. The
proof should fail closed and emit a machine-readable JSON artifact.

Required checks:

- Docker stack is healthy
- Paperclip is reachable
- Open WebUI is reachable
- n8n is reachable
- n8n-mcp is reachable
- Langfuse is reachable
- broker is reachable
- company bootstrap from template succeeds
- manager creates exactly one worker child issue
- worker completes the child issue
- manager completes the parent issue
- no runaway child issue creation
- no runtime-noise comments
- final comments have correct agent/run attribution when present
- company `HERMES_HOME` exists
- host Hermes home is separate from company Hermes home
- company A and company B Hermes homes are separate
- Honcho service is healthy
- `honcho.workspace == companyId`
- `honcho.aiPeer == paperclip-agent-<agentId>`
- final `proof.json` is schema-valid

This proof should be treated as the referee. Installer changes should make this
proof pass, not weaken the proof.

## Suggested Agent Roles

Multiple agents are useful only if ownership boundaries are strict:

- Forensic role:
  - read-only VPS and transcript inspection
  - exports known-good facts and mismatches
- Proof role:
  - owns schemas, verifier scripts, and expected JSON shape
  - writes the failing end-state proof before installer fixes
- Installer role:
  - owns bootstrap scripts, service installation, and idempotency
  - works only to satisfy the proof contract
- Docs role:
  - keeps runbooks and architecture docs aligned with what the proof verifies
- Reviewer/verifier role:
  - resets or uses the VM snapshot, runs the loop, and reports artifacts
  - does not edit installer logic

The proof role and installer role should remain separate so implementation work
does not quietly relax the acceptance criteria.

## Reconstruction Loop

The intended loop is:

1. Restore the local VM snapshot.
2. Clone `origin/development` onto the VM.
3. Install missing prerequisites.
4. Run repo validation and simulation proof.
5. Start the stack.
6. Install host-native Hermes and Honcho.
7. Bootstrap a manager/worker Paperclip company from template.
8. Run the staging node proof.
9. Collect `proof.json`, logs, and failure artifacts.
10. Patch the repo.
11. Repeat until the clean VM passes from scratch.

Only after the VM passes should the live VPS be rebuilt from the same branch.

## Immediate Next Steps

1. Add a sanitized VPS evidence export document or artifact from read-only API
   calls.
2. Add a staging-node proof contract that can target the local VM.
3. Make the proof fail clearly on the current clean VM.
4. Package prerequisite install and checkout setup for Ubuntu 24.04.
5. Fix Honcho health and memory mapping before expanding installer scope.
6. Integrate the template-backed manager/worker proof into the node proof.

## Decision Needed Before Implementation

The next pass should choose one of two paths:

- **Strict verifier-first:** write the staging proof first, then make the VM pass.
- **Bootstrap-first:** package the current runbook first, then add the proof.

The recommended path is strict verifier-first. The whole failure mode that led
to this pause was that working behavior existed without a durable verifier. The
VM snapshot makes the verifier-first loop practical without requiring the human
operator to act as the middle layer between agents.
