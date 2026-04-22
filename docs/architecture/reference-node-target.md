# Donna Reference Node Target

Concrete target state for the current Donna / Studio54 VPS. This is not a new
architecture brainstorm. It is the definition of what "correct" should mean for
the existing reference node once it is stabilized enough to clone to future
sites.

Use this document as the operational target while cleaning up the live VPS and
while back-porting that shape into the repo.

Related documents:

- Current live runtime inventory:
  [donna-vps-service-map.md](donna-vps-service-map.md)
- Hermes runtime definition:
  [hermes-runtime.md](hermes-runtime.md)
- Hermes bootstrap contract:
  [hermes-bootstrap.md](hermes-bootstrap.md)
- System config map:
  [system-config-map.md](system-config-map.md)
- Operator initialization flow:
  [operator-init-flow.md](operator-init-flow.md)
- Current repo/runtime mismatch:
  [current-state.md](current-state.md)
- Long-range architecture target:
  [north-star.md](north-star.md)
- Sequenced repo roadmap:
  [roadmap.md](roadmap.md)

## Scope

This document defines the target shape for one working reference node:

- one VPS
- one deploy root
- one operator access model
- one documented service ownership model

It does not try to fully solve multi-node rollout, learning-plane automation,
or final product design. Those come after the reference node is boring and
predictable.

## Definition Of Done

Donna is considered a stabilized reference node when all of the following are
true:

1. The live runtime matches the declared runtime model.
2. Operator-only surfaces are tailnet-only by default.
3. Public surfaces are explicitly chosen and minimal.
4. Every service has one clear owner: Compose or systemd.
5. Ports, binds, healthchecks, and hostnames match documentation.
6. The repo contains enough truth to rebuild the same shape intentionally.
7. A second site could be created by changing site-specific config rather than
   reinventing topology.

## Canonical Ownership

### Repo

- Shared source of truth for service definitions, scripts, topology, and docs
- Target deploy root shape for VPS nodes
- Site-specific overlays via env/config, not ad hoc code edits

### Live node

- Current reference implementation
- Used for functional experiments with Hermes, Paperclip, n8n, and related
  workflows
- Every live fix must either be reflected back into the repo or captured as
  intentional node-local configuration

## Target Deploy Root

The VPS should converge on one canonical deploy checkout:

- `/opt/1215-vps`

This deploy root should be treated as the only active site checkout for Donna.
Other directories such as `/opt/honcho` and `/opt/honcho-self-hosted` may
remain for now, but they are not the target service ownership root and should
not be part of the steady-state deployment path unless explicitly promoted.

## Service Ownership Model

### Compose-managed

These should be owned by Docker Compose in the steady state:

- `open-webui`
- `n8n`
- `n8n-mcp`
- `broker`
- `postgres`
- `valkey`
- `minio`
- `qdrant`
- `neo4j`
- `clickhouse`
- `langfuse-web`
- `langfuse-worker`
- `paperclip`
- `comfyui`

### systemd-managed

These may remain host-managed if they truly need host-native behavior:

- `hermes-dashboard.service`

Hermes is the intentional exception to the otherwise containerized app plane. It
belongs to the host-native control plane, not the app plane.

Future host services are allowed only when there is a real host-bound reason,
not as a convenience shortcut.

## Access Model

### Tailnet-only surfaces

These are operator/admin surfaces and should default to Tailscale-only access:

- Hermes dashboard
- Paperclip
- n8n-mcp
- Langfuse
- Neo4j
- Qdrant
- MinIO console
- MinIO S3 API unless there is a specific external integration need

### Public surfaces

Only keep a surface public if there is a clear product need. The current Donna
reference node no longer requires any public HTTP application ingress.

If a future node truly needs public app ingress, add it intentionally as a
separate exposure profile rather than making it the default shape.

## Network Contracts

The reference node should have stable, documented contracts:

- Hermes dashboard:
  - app listener: `100.87.24.49:9119` on the Tailscale interface
  - private URL: `http://donna.tailfedd3b.ts.net:9119/`
- Paperclip:
  - app listener: `127.0.0.1:3100`
  - private URL: `https://donna.tailfedd3b.ts.net:8443`
- n8n:
  - app listener: `127.0.0.1:5678`
- n8n-mcp:
  - app listener: `127.0.0.1:13000 -> 3000`
- Open WebUI:
  - app listener: `127.0.0.1:8080`

The key rule is simple:

- no silent port drift
- no "pick the next free port" behavior unless explicitly intended
- no healthcheck pointing at a stale port

## Configuration Model

The repo should separate:

- shared deployment logic
- site-specific values

Site-specific values include:

- public domain
- Tailscale hostname / tailnet URL allowlists
- secrets
- optional exposure choices
- any per-site branding or naming

These should live in env/config overlays, not in copy-pasted service edits.

## Current Known Good Behaviors To Preserve

These are already working and should be preserved while refactoring:

- Paperclip is healthy on `127.0.0.1:3100`
- Paperclip tailnet URL returns `200 OK`
- Hermes tailnet URL is reachable
- Tailscale Serve provides the operator access layer for containerized services
- Hermes remains privately reachable on the tailnet through its direct MagicDNS
  bind
- SSH remains available

## Known Cleanup Targets

These are expected stabilization tasks, not signs of failure:

- document and possibly reduce the remaining host-managed units
- reconcile WSL copies and deploy checkout into a less confusing repo workflow
- decide whether Hermes should stay host-native long term
- codify Hermes as a host-native, tailnet-bound control-plane service

## Operator Rules

While stabilizing the reference node:

1. Do not make live-only fixes without recording them in repo docs or source.
2. Prefer narrowing exposure over widening it.
3. Prefer one clear ownership path over clever integration.
4. Preserve working experiments unless they directly block cleanup.
5. Use this node to discover the real runtime shape before standardizing it.

## Next Stabilization Milestones

### Milestone 1: Access sanity

- operator surfaces are reachable over Tailscale Serve
- public HTTP/HTTPS ingress is removed unless explicitly required
- stale public-route docs/comments are cleaned up

### Milestone 2: Ownership sanity

- explicit list of Compose vs systemd services
- no mystery listeners
- no unexplained host-level bridges or sidecars

### Milestone 3: Repo alignment

- repo docs match the live node
- deploy config reflects the working node shape
- second-site deployment inputs are identifiable

### Milestone 4: Clone readiness

- one documented bring-up path
- one documented env model
- one documented exposure policy
- enough confidence to stand up another site without rediscovering the topology
