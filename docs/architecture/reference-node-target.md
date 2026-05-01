# Reference Node Target

Canonical architecture entrypoint: [canonical/README.md](canonical/README.md).

This is the current contract for a correct private-first Studio54 node. It is
based on the proven fresh-node behavior on `srv1264451` and the committed repo
state.

Primary related docs:

- Canonical launch/operation map:
  [canonical/vps-launch-and-company-operation.md](canonical/vps-launch-and-company-operation.md)
- Hermes runtime boundaries: [hermes-runtime.md](hermes-runtime.md)
- Memory model: [memory-model.md](memory-model.md)
- Paperclip `hermes_local` contract:
  [paperclip-hermes-local-contract.md](paperclip-hermes-local-contract.md)
- Company bootstrap path: [company-bootstrap.md](company-bootstrap.md)
- Shared knowledge repo:
  [agent-knowledge-exchange.md](agent-knowledge-exchange.md)
- Operator runbook: [../../deploy/vps/INSTALL.md](../../deploy/vps/INSTALL.md)

## Node Shape

Baseline:

- plain Ubuntu 24.04 VPS
- SSH reachable
- Docker and Compose installed
- Tailscale installed and joined
- public inbound limited to `22/tcp`
- app services bound privately on loopback
- operator access over the tailnet

Current proven fresh node:

- host: `srv1264451`
- public IP: `191.101.0.164`
- deploy checkout: `/opt/studio54-bootstrap`
- Paperclip local URL: `http://127.0.0.1:3100/`
- node-local knowledge clone: `/opt/agent-knowledge-exchange`

Correctness rule:

- host-native services belong to the operator control plane
- containerized services belong to the app plane
- loopback is the default app-plane exposure
- the tailnet is the operator ingress layer

## Ownership

### Host-Native

Host-native services are part of the operator control plane:

- `ssh`
- `docker`
- `tailscaled`
- outer Hermes dashboard: `hermes-dashboard.service`

Outer Hermes is installed under `/root/.hermes` and is intentionally separate
from Paperclip-internal Hermes runs. See
[hermes-runtime.md](hermes-runtime.md).

### Containerized

The app plane is owned by Docker Compose in
`stack/prototype-local/docker-compose.substrate.yml`.

Current service inventory:

- `postgres`
- `postgres-bootstrap`
- `valkey`
- `qdrant`
- `neo4j`
- `minio`
- `minio-init`
- `clickhouse`
- `broker`
- `broker-bootstrap`
- `shared-data-init`
- `open-webui`
- `comfyui`
- `n8n`
- `n8n-mcp`
- `langfuse-web`
- `langfuse-worker`
- `paperclip`

The Paperclip image includes the local agent CLIs needed by Paperclip adapters,
including `hermes` for the proven `hermes_local` path.

Paperclip is containerized, but it is also the execution environment for
Paperclip-local agent adapters. That means some runtime tooling, including the
proven `hermes_local` path, must exist inside the Paperclip image rather than
only on the host.

The active Paperclip execution contract is direct per-company `hermes_local`.
The 1215 Paperclip -> Hermes gateway path is optional/future-state for
Paperclip task execution on this node.

For bounded assigned work, issue completion is explicit: the inner Hermes agent
must close the issue through Paperclip with a final PATCH that includes both
`status: "done"` and a completion comment. Paperclip does not treat adapter or
process success alone as task completion.

## Exposure Contract

### Loopback

Containerized operator services bind locally on the node. Proven/declared local
service URLs:

- Paperclip: `http://127.0.0.1:3100/`
- Open WebUI: `http://127.0.0.1:8080/`
- n8n: `http://127.0.0.1:5678/`
- Langfuse: `http://127.0.0.1:3000/`
- n8n-mcp: `http://127.0.0.1:13000/health`
- Neo4j: `http://127.0.0.1:7474/`
- Qdrant: `http://127.0.0.1:6333/`
- MinIO Console: `http://127.0.0.1:9011/`
- MinIO S3 API: `http://127.0.0.1:9010/`
- ComfyUI: `http://127.0.0.1:8188/`

### Tailnet

Containerized operator services are published privately with Tailscale Serve.
The expected URL shape is:

- `https://<node>.tailfedd3b.ts.net:8443/` Paperclip
- `https://<node>.tailfedd3b.ts.net:8444/` Open WebUI
- `https://<node>.tailfedd3b.ts.net:8445/` n8n
- `https://<node>.tailfedd3b.ts.net:8446/` Langfuse
- `https://<node>.tailfedd3b.ts.net:8447/` n8n-mcp
- `https://<node>.tailfedd3b.ts.net:8448/` Neo4j
- `https://<node>.tailfedd3b.ts.net:8449/` Qdrant
- `https://<node>.tailfedd3b.ts.net:8450/` MinIO Console
- `https://<node>.tailfedd3b.ts.net:8451/` MinIO S3 API
- `https://<node>.tailfedd3b.ts.net:8452/` ComfyUI

Outer Hermes is the exception: the dashboard binds directly to the node's
MagicDNS hostname on port `9119`, with a narrow `ufw` allow rule on
`tailscale0`.

This is a deliberate exception to the general Tailscale Serve pattern because
the Hermes dashboard host-header behavior is currently satisfied by direct
tailnet binding.

### Public Internet

The reference node does not require public HTTP application ingress. Public
inbound should remain limited to `22/tcp` unless a future public surface is
explicitly added and documented.

## Persistence Expectations

The node is not correctly bootstrapped unless these survive reboot:

- `ssh` enabled
- `docker` enabled
- `tailscaled` enabled
- Docker services have persistent volumes and restart policy
- Tailscale Serve mappings remain present
- outer Hermes systemd unit remains enabled
- Paperclip volume data remains durable
- company-scoped Hermes homes remain under the Paperclip data tree

## Configuration Contract

The root `.env` is the canonical operator control surface for node-level
settings and provider/model keys.

Source-of-truth files:

- root `.env`
- root `.env.example`
- Compose file: `stack/prototype-local/docker-compose.substrate.yml`
- projection scripts in `stack/prototype-local/scripts/`
- docs in `docs/architecture/`

Generated runtime files:

- `stack/prototype-local/.env`
- `/root/.hermes/.env`
- `/root/.hermes/config.yaml`
- per-company Hermes `.env`, `config.yaml`, and `honcho.json` under:
  `/paperclip/instances/<instance-id>/companies/<company-id>/hermes-home`

Rule: edit the source-of-truth file, then regenerate runtime files. Do not
treat generated runtime files as the canonical source.

The node-local knowledge repo clone at `/opt/agent-knowledge-exchange` is not a
runtime source-of-truth file. It is a shared operational knowledge working copy.

## Open Questions

- Whether the outer Hermes checkout should be version-pinned beyond the current
  documented install path.
- Whether Tailscale authorization should remain manual or move to a reusable
  auth-key/API provisioning path.
- Which parts of the fresh-node sequence should become a single idempotent
  bootstrap command.
- Per-task Honcho session mapping.
