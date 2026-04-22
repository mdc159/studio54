# studio54 — VPS bring-up walkthrough

This document captures the state of the Hostinger KVM 8 (`148.230.95.154`) as
it was at the moment this repo was snapshotted out of `1215-vps`. It's
deliberately short — just enough to reconstruct the host if the snapshot
crapped out. Per-service internals live in the repo subtrees they belong to.

## 0. What's running

Host-native (systemd):

- **Hermes Agent gateway** — `~/.config/systemd/user/hermes-gateway.service`
  (installed by the hermes `install.sh` one-liner; runs as the `root` user with
  `HOME=/root`). Donna's messaging/gateway surface.
- **Hermes Agent dashboard** — `/etc/systemd/system/hermes-dashboard.service`
  (see `deploy/vps/systemd/`). Serves the web UI at `127.0.0.1:9119`,
  reachable externally as `https://brain.pimpshizzle.com` via Caddy.
- **Paperclip Caddy bridge** — `/etc/systemd/system/paperclip-bridge.service`
  (see `deploy/vps/systemd/`). socat on `172.18.0.1:3100` ->
  `127.0.0.1:3100` so Caddy can reach Paperclip without violating its
  `local_trusted` loopback contract.

Containerized (Docker Compose at `stack/prototype-local/`):

- postgres (5433), valkey, qdrant, neo4j, minio, clickhouse, broker,
  broker-bootstrap, open-webui, comfyui (CPU), n8n, n8n-mcp, langfuse-web,
  paperclip (host network), caddy.

## 1. Prereqs on a fresh Ubuntu 24.04 VPS

```bash
apt update && apt install -y docker.io docker-compose-plugin socat curl git ufw
systemctl enable --now docker
```

## 2. Firewall

```bash
bash deploy/vps/ufw-rules.sh
```

## 3. Clone + bring up the stack

```bash
mkdir -p /opt && cd /opt
git clone git@github.com:mdc159/studio54.git
cd studio54
git submodule update --init --recursive  # paperclip, hermes-agent, honcho, ...

cp stack/prototype-local/.env.example stack/prototype-local/.env
# edit .env: set DOMAIN, CADDY_EMAIL, OPENROUTER_API_KEY, and anything else
# marked TODO in .env.example

cd stack/prototype-local
docker compose -f docker-compose.substrate.yml up -d
```

## 4. Install Hermes Agent ("Donna")

Follow the upstream one-liner install (see `modules/hermes-agent/README.md`).
Then add the dashboard unit from this repo:

```bash
install -m 644 deploy/vps/systemd/hermes-dashboard.service /etc/systemd/system/
mkdir -p /var/log/hermes-dashboard
systemctl daemon-reload
systemctl enable --now hermes-dashboard.service
```

## 5. Install the Paperclip Caddy bridge

```bash
install -m 644 deploy/vps/systemd/paperclip-bridge.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now paperclip-bridge.service
```

## 6. Public URLs (existing pimpshizzle.com DNS, no registrar work)

| Subdomain | Service |
|---|---|
| `ai.pimpshizzle.com` | Open WebUI (default model: `google/gemini-2.5-flash` via OpenRouter) |
| `n8n.pimpshizzle.com` | n8n workflow editor |
| `trace.pimpshizzle.com` | Langfuse LLM observability |
| `brain.pimpshizzle.com` | Hermes Agent dashboard (Donna — API keys, skills, sessions) |
| `flow.pimpshizzle.com` | Paperclip orchestration workbench |
| `neo4j.pimpshizzle.com` | Neo4j browser |
| `minio.pimpshizzle.com` | MinIO console |
| `s3.pimpshizzle.com` | MinIO S3 API |

Apex `pimpshizzle.com` is intentionally unrouted — reserved for a future
landing page.

## 7. Security posture (prototype)

The Hermes dashboard has no password wall — anyone who hits
`brain.pimpshizzle.com` gets a live API-key management session. This is
acceptable during active prototype buildout per direct user direction
(2026-04-21: "just while we're setting things up"); it moves to tailnet-only
when Tailscale lands.

Paperclip runs in `local_trusted` mode behind the socat bridge; until its
hostname allowlist is populated via `pnpm paperclipai allowed-hostname
flow.pimpshizzle.com` (after `paperclip onboard` has been run), the route
will return 403. See `stack/prototype-local/Caddyfile` for the route
definition.
