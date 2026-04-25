# Fresh VPS Test Node Plan

This document captures the accepted next steps for the fresh Hostinger test
node after the clean substrate bootstrap succeeded.

Current test node:

- host: `srv1264451`
- repo root: `/opt/studio54-bootstrap`
- stack status: substrate services are up through
  `stack/prototype-local/docker-compose.substrate.yml`
- public inbound: `22/tcp` only

This is not the full long-range architecture. It is the concrete plan for
turning the fresh VPS into a cloneable private-first reference node.

## Current Proven State

The following is already proven on the fresh VPS:

- plain Ubuntu 24.04 Hostinger image is a usable baseline
- Docker and Compose install cleanly
- the app-plane substrate boots from the repo on a fresh node
- the stack runs loopback-only by default
- `ufw` can remain enabled with only `22/tcp` open
- `hermes_local` now runs successfully inside Paperclip with isolated
  per-company `HERMES_HOME`
- a second `hermes_local` proof succeeded with a separate company and agent

Fresh-node proof artifacts:

- company: `c754b277-80cc-47f3-8d54-90d02ff41b2d`
- test agent: `d6ff8a00-730e-46fd-9d2d-124c428ab3fd`
- issue: `HER-1`
- confirmed runs:
  - `f415ff0c-de15-44c7-9238-bd0d44ba5150`
  - `a301c43d-29cd-4343-a75f-1297eb521e36`
  - `683f1a86-8ee7-44f3-8f34-af36c0947022`

Second proof artifacts:

- company: `ab6896c0-a9a8-473d-943e-88012137055c`
- test agent: `8a5e57dc-ebe9-435b-a9d0-716c8826a4c6`
- issue: `HERA-1` / `6d1b1635-fb6c-45d5-b7d4-d65c113d124a`
- successful run: `3a2b0317-bee0-48fb-8cb1-2b4590bb9a6f`
- agent-authored comment: `5ded90f3-32a1-4a2d-867b-63d191441a4b`

## Next Steps

### 1. Add Tailscale

Install and join Tailscale on the fresh node.

Purpose:

- private operator ingress
- no public HTTP exposure
- reproducible access model for cloned nodes

Target result:

- SSH remains available
- operator services become reachable privately over the tailnet
- operator login to the Tailscale authorization URL is documented as an
  explicit manual step

### 2. Publish operator services privately

After Tailscale is up, publish the containerized operator surfaces through
Tailscale Serve.

Expected private URLs will mirror Donna's model, but with the new node's own
MagicDNS name.

Services to publish first:

- Paperclip
- Open WebUI
- n8n
- Langfuse
- n8n-mcp
- Neo4j
- Qdrant
- MinIO console
- MinIO S3 API
- ComfyUI

Persistence requirement:

- Tailscale Serve mappings must remain present after reboot

### 3. Install outer Hermes host-native

Install the host-native Hermes runtime on the fresh node.

This is the outer Hermes:

- machine-level operator runtime
- independent of Paperclip
- private by design
- durable across company lifecycles

Target contract:

- host-native install
- systemd-managed
- private tailnet access
- its own `HERMES_HOME`
- direct dashboard bind on the node's MagicDNS hostname
- explicit `ufw` allow rule for `9119/tcp` on `tailscale0`

### 4. Separate outer Hermes from Paperclip-internal Hermes runs

This is the key memory rule.

Paperclip may use `hermes_local` as an inner company runtime, but it must not
implicitly share the outer Hermes memory/home.

Required direction:

- outer Hermes keeps its own durable memory and profile space
- each Paperclip company gets its own isolated Hermes runtime home/profile when
  `hermes_local` is used
- memory transfer between companies is explicit, not ambient
- current accepted inner-home path:
  - `/paperclip/instances/<instance-id>/companies/<company-id>/hermes-home`
- `hermes_local` can receive that through adapter config env:
  - `adapterConfig.env.HERMES_HOME=...`

Current supported path:

- the Paperclip container should carry a local `hermes` CLI
- `hermes_local` should run there with `adapterConfig.env.HERMES_HOME` pointing
  at the per-company home
- the Hermes launcher and its Python interpreter must both be executable by the
  Paperclip runtime user
- prepared company homes must be owned by the Paperclip runtime UID/GID
- Paperclip must pass resolved adapter config/env values, not unresolved
  binding objects such as `[object Object]`
- Paperclip must surface task/run fields into adapter config for adapters that
  build prompts from `ctx.config`; for `hermes_local`, this includes `taskId`,
  `taskTitle`, `taskBody`, `commentId`, and `wakeReason`
- gateway mediation remains a future hardening option, not the active contract

In plain terms:

- outer Hermes should not make new companies haunted
- new companies start fresh
- cross-company lessons can be promoted intentionally

### 5. Keep skills global, memory local

Accepted rule:

- skills are global by default
- company memory is local by default
- promotion from local knowledge to shared skill is explicit

Examples:

- `n8n` skill: shared
- GitHub skill: shared
- company operating norms: local
- company-specific task history: local

### 6. Pin important models

Model choice is part of agent identity.

For important company roles, prefer pinned models/builds over floating aliases.

Priority roles to pin:

- CEO
- CTO
- any approval-bearing or budget-bearing role

Reason:

- same role label with a different model can behave like a different employee

## Accepted Mental Model

### Outer Hermes

- host-native
- operator/executive runtime
- persistent across companies
- may supervise Paperclip
- may do work outside Paperclip

### Inner Hermes runtimes

- used by Paperclip agents through local adapters
- company-scoped
- should use isolated runtime homes/profiles
- subordinate to Paperclip company/task state while operating inside a company

### Paperclip

- system of record for company state
- owns org structure, issues, approvals, budgets, routines, and company-facing
  workflows

## Immediate Implementation Order

1. reconcile proof-driven Paperclip image/runtime changes into the repo cleanly
2. verify repo-quality checks in a usable Paperclip dev environment
3. promote the durable findings into shared knowledge and bootstrap docs
4. then decide how much of that becomes a single bootstrap script
