# Donna VPS Service Map

Factual inventory of the live VPS currently reachable as `Donna` / `Studio54`.
This document describes the runtime as observed on the host, not the desired
target state.

For the stabilization target this node is being cleaned toward, see
[reference-node-target.md](reference-node-target.md). For the concrete Hermes
definition on this node, see [hermes-runtime.md](hermes-runtime.md). For the
canonical config surfaces and live port map, see
[system-config-map.md](system-config-map.md).

## Runtime Ownership

- Deploy root: `/opt/1215-vps`
- Active compose project: `1215-prototype-local`
- Compose file: `/opt/1215-vps/stack/prototype-local/docker-compose.substrate.yml`
- Additional host-managed units:
  - `hermes-dashboard.service`

Retired from the live Donna runtime:

- `caddy` container
- `paperclip-bridge.service`

## Public Ingress

The VPS currently exposes only these public listener ports through UFW:

- `22/tcp` for SSH

Everything else is loopback-only or exposed privately through Tailscale Serve.

## Service Map

### Tailscale Serve

The current Donna operator access layer is Tailscale Serve on the node MagicDNS
name `donna.tailfedd3b.ts.net`.

Private URLs currently published:

- Hermes: `http://donna.tailfedd3b.ts.net:9119/`
- Paperclip: `https://donna.tailfedd3b.ts.net:8443/`
- Open WebUI: `https://donna.tailfedd3b.ts.net:8444/`
- n8n: `https://donna.tailfedd3b.ts.net:8445/`
- Langfuse: `https://donna.tailfedd3b.ts.net:8446/`
- n8n-mcp: `https://donna.tailfedd3b.ts.net:8447/`
- Neo4j: `https://donna.tailfedd3b.ts.net:8448/`
- Qdrant: `https://donna.tailfedd3b.ts.net:8449/`
- MinIO Console: `https://donna.tailfedd3b.ts.net:8450/`
- MinIO S3 API: `https://donna.tailfedd3b.ts.net:8451/`
- ComfyUI: `https://donna.tailfedd3b.ts.net:8452/`

### Hermes dashboard

- systemd unit: `hermes-dashboard.service`
- Command: `hermes dashboard --host donna.tailfedd3b.ts.net --port 9119 --no-open --insecure`
- Live listener: `100.87.24.49:9119` (via MagicDNS bind)
- Private access path: `http://donna.tailfedd3b.ts.net:9119/` directly on the tailnet interface

This is an admin-grade surface, intentionally host-native, and no longer
exposed through public ingress.

### Paperclip

- Container: `1215-prototype-local-paperclip-1`
- Network mode: `host`
- Declared container env:
  - `HOST=127.0.0.1`
  - `PORT=3100`
  - `PAPERCLIP_DEPLOYMENT_MODE=local_trusted`
- Observed app listener: `127.0.0.1:3100`

Current private access path is `https://donna.tailfedd3b.ts.net:8443/` via
Tailscale Serve.

The earlier host `socat` bridge used for Caddy ingress has been retired from
the live Donna runtime.

Root cause of the earlier `3101` drift:
Paperclip startup used `detect-port` without a host, so the bridge listener on
`172.18.0.1:3100` made it think port `3100` was busy even though the app was
binding to `127.0.0.1`. The fix is to detect collisions on the configured host
only.

### n8n

- Container: `1215-prototype-local-n8n-1`
- Listener: `127.0.0.1:5678`
- Private access path: `https://donna.tailfedd3b.ts.net:8445/`

### n8n-mcp

- Container: `1215-prototype-local-n8n-mcp-1`
- Listener: `127.0.0.1:13000 -> 3000`
- Private access path: `https://donna.tailfedd3b.ts.net:8447/`

### Open WebUI

- Container: `1215-prototype-local-open-webui-1`
- Listener: `127.0.0.1:8080`
- Private access path: `https://donna.tailfedd3b.ts.net:8444/`

### Langfuse

- Containers:
  - `1215-prototype-local-langfuse-web-1`
  - `1215-prototype-local-langfuse-worker-1`
- Listeners:
  - `127.0.0.1:3000` for web
  - `127.0.0.1:3030` for worker health
- Private access path: `https://donna.tailfedd3b.ts.net:8446/`

### Data services

- Postgres: `127.0.0.1:5433`
- ClickHouse: `127.0.0.1:8123`, `127.0.0.1:9000`, `127.0.0.1:9009`
- Qdrant: `127.0.0.1:6333`, `127.0.0.1:6334`
- Neo4j: `127.0.0.1:7473`, `127.0.0.1:7474`, `127.0.0.1:7687`
- MinIO: `127.0.0.1:9010`, `127.0.0.1:9011`
- Valkey: `127.0.0.1:6379`

Selected operator-facing services are exposed privately through Tailscale Serve.

## Risk Notes

- `hermes-dashboard.service` is intentionally host-native and now binds on the
  Tailscale interface only via MagicDNS; it is not exposed through public
  firewall rules.
- The live VPS is using `/opt/1215-vps` as the deployment root, while local WSL
  copies under `~/projects/company` are not currently Git checkouts.

## Ingress State

Current Donna ingress policy:

- Public: SSH only
- Private operator access: Tailscale Serve for containerized services, direct tailnet bind for Hermes
- Retired from live ingress: Caddy and public HTTP/HTTPS
