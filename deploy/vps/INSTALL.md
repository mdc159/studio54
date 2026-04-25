# studio54 - VPS bring-up walkthrough

This document tracks the current private-first bring-up pattern for a fresh
plain Ubuntu 24.04 VPS. It is intentionally focused on the bootstrap
contract: what the script can do, what the operator still has to do, and what
"done" looks like on a clean node.

For the concrete post-bootstrap follow-up sequence on the current test node,
see:

- [TEST_NODE_PLAN.md](TEST_NODE_PLAN.md)

## 0. Current target shape

Fresh node baseline:

- plain Ubuntu 24.04 LTS
- SSH reachable
- no one-click Docker / Paperclip / Hermes preset
- public inbound limited to `22/tcp`

Target node shape after bring-up:

- Docker substrate running from `stack/prototype-local/`
- app services bound privately on loopback
- Tailscale installed and joined
- operator surfaces published through Tailscale Serve
- Hermes installed host-native later as a separate step

## 1. Host prerequisites

Install base packages and enable Docker:

```bash
apt update
apt install -y ca-certificates curl git docker.io docker-compose-v2 ufw
systemctl enable --now docker
systemctl enable --now ssh
```

## 2. Firewall baseline

Keep the node closed by default:

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw --force enable
```

Expected result:

- public inbound is `22/tcp` only
- app services are not reachable on the public interface

## 3. Clone the repo and create the root operator env

```bash
mkdir -p /opt && cd /opt
git clone git@github.com:mdc159/studio54.git studio54-bootstrap
cd /opt/studio54-bootstrap
cp .env.example .env
```

Edit the root `.env` and set at least:

- `NODE_NAME`
- `DEPLOY_ROOT`
- `STACK_ENV_PATH`
- provider/model API keys you actually intend to use

Then project the stack env:

```bash
python3 stack/prototype-local/scripts/project_root_env.py
python3 stack/prototype-local/scripts/init_env.py
python3 stack/prototype-local/scripts/project_hermes_runtime.py
```

## 4. Bring up the substrate

```bash
cd /opt/studio54-bootstrap/stack/prototype-local
docker compose -f docker-compose.substrate.yml up -d
```

Expected local service URLs on the node:

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

## 5. Install and join Tailscale

Install:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
systemctl enable --now tailscaled
tailscale up --ssh
```

### Operator-required step

`tailscale up` will emit a login URL. The bootstrap cannot complete the
tailnet authorization itself unless you later add a reusable auth key or
API-based provisioning path.

Current operator action:

1. open the login URL from the `tailscale up` output
2. authorize the node into the intended tailnet
3. return to the shell and verify:

```bash
tailscale status
tailscale ip -4
```

This operator login step should be treated as a first-class documented
touchpoint, not hidden tribal knowledge.

## 6. Publish private operator URLs with Tailscale Serve

Example pattern:

```bash
tailscale serve --bg --https=8443 http://127.0.0.1:3100
tailscale serve --bg --https=8444 http://127.0.0.1:8080
tailscale serve --bg --https=8445 http://127.0.0.1:5678
tailscale serve --bg --https=8446 http://127.0.0.1:3000
tailscale serve --bg --https=8447 http://127.0.0.1:13000
tailscale serve --bg --https=8448 http://127.0.0.1:7474
tailscale serve --bg --https=8449 http://127.0.0.1:6333
tailscale serve --bg --https=8450 http://127.0.0.1:9011
tailscale serve --bg --https=8451 http://127.0.0.1:9010
tailscale serve --bg --https=8452 http://127.0.0.1:8188
```

Then confirm:

```bash
tailscale serve status
```

Expected private URLs follow this shape:

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

## 7. Persistence requirements

The node is not considered correctly bootstrapped unless the following survive
reboot:

- `ssh` enabled at boot
- `docker` enabled at boot
- `tailscaled` enabled at boot
- Docker services use persistent volumes and restart policies
- Tailscale Serve mappings remain present

Nothing should depend on "someone ran this command manually once" unless the
step is explicitly documented as operator-required.

## 8. Install outer Hermes host-native

Install the host prerequisites Hermes expects:

```bash
apt update
apt install -y build-essential python3-venv ripgrep
mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
echo 'deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main' > /etc/apt/sources.list.d/nodesource.list
apt update
apt install -y nodejs
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install Hermes under `/root/.hermes`:

```bash
mkdir -p /root/.hermes /root/.local/bin /var/log/hermes-dashboard
git clone https://github.com/NousResearch/hermes-agent.git /root/.hermes/hermes-agent
cd /root/.hermes/hermes-agent
printf 'n\n' | ./setup-hermes.sh
python3 /opt/studio54-bootstrap/stack/prototype-local/scripts/project_hermes_runtime.py
```

Expected CLI shim:

```bash
ls -l /root/.local/bin/hermes
```

Expected shape:

- `/root/.local/bin/hermes -> /root/.hermes/hermes-agent/venv/bin/hermes`
- `/root/.hermes/.env` generated from the root operator `.env`
- `/root/.hermes/config.yaml` generated from the root operator `.env`

Install the dashboard unit:

```ini
[Unit]
Description=Hermes Agent Web Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Environment=HOME=/root
Environment=PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/root/.local/bin/hermes dashboard --host <node>.tailfedd3b.ts.net --port 9119 --no-open --insecure
Restart=on-failure
RestartSec=5
StandardOutput=append:/var/log/hermes-dashboard/stdout.log
StandardError=append:/var/log/hermes-dashboard/stderr.log

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
systemctl daemon-reload
systemctl enable --now hermes-dashboard.service
```

### Operator-required step

Hermes on this node is not published through Tailscale Serve. It binds directly
to the Tailscale interface so the dashboard host-header checks remain satisfied.

That means `ufw` needs a narrow tailnet-only rule:

```bash
ufw allow in on tailscale0 to any port 9119 proto tcp
```

This does not widen the public surface. It only permits direct tailnet access
to the Hermes dashboard.

## 9. Inner Hermes isolation for Paperclip companies

`hermes_local` should not reuse the outer runtime at `/root/.hermes`.

The external `hermes-paperclip-adapter` accepts `adapterConfig.env`, so a
Paperclip agent can set `HERMES_HOME` explicitly for each company. The accepted
target path is:

- `/paperclip/instances/<instance-id>/companies/<company-id>/hermes-home`

Prepare that company-scoped runtime home with:

```bash
python3 /opt/studio54-bootstrap/stack/prototype-local/scripts/prepare_paperclip_hermes_home.py \
  --company-id <company-id>
```

That renders:

- `<hermes-home>/.env`
- `<hermes-home>/config.yaml`
- runtime directories:
  - `skills/`
  - `sessions/`
  - `logs/`
  - `memories/`

Example adapter config fragment for a Paperclip agent:

```json
{
  "env": {
    "HERMES_HOME": "/paperclip/instances/default/companies/<company-id>/hermes-home"
  }
}
```

Current supported path:

- the Paperclip image should ship a local `hermes` CLI, just as it already
  ships `codex` and `claude`
- `hermes_local` then runs Hermes directly inside the Paperclip execution
  environment
- per-company memory isolation comes from `adapterConfig.env.HERMES_HOME`
- the `hermes` launcher and its Python interpreter must be executable by the
  Paperclip runtime user, not only by `root`
- Paperclip must pass the resolved runtime adapter config into local adapters;
  persisted secret/env bindings such as `{ "type": "plain", "value": "..." }`
  are not valid process environment values
- Paperclip must surface run-scoped task fields such as `taskId`, `taskTitle`,
  `taskBody`, `commentId`, and `wakeReason` in the adapter config object for
  adapters that build prompts from `ctx.config`

Do not point Paperclip `hermes_local` at `/root/.hermes`. That would collapse
inner company memory into the outer operator runtime.

Fresh-node proof on `srv1264451`:

- company: `c754b277-80cc-47f3-8d54-90d02ff41b2d`
- agent: `d6ff8a00-730e-46fd-9d2d-124c428ab3fd`
- issue: `HER-1` / `567cdb82-6eef-412d-ae7a-230bc74f3c33`
- successful run: `f415ff0c-de15-44c7-9238-bd0d44ba5150`
- Hermes log confirmed it loaded:
  `/paperclip/instances/default/companies/c754b277-80cc-47f3-8d54-90d02ff41b2d/hermes-home/.env`

Second proof on `srv1264451` after reconciling live runtime drift:

- company: `ab6896c0-a9a8-473d-943e-88012137055c`
- agent: `8a5e57dc-ebe9-435b-a9d0-716c8826a4c6`
- issue: `HERA-1` / `6d1b1635-fb6c-45d5-b7d4-d65c113d124a`
- successful run: `3a2b0317-bee0-48fb-8cb1-2b4590bb9a6f`
- agent-authored comment:
  `DONE /paperclip/instances/default/companies/ab6896c0-a9a8-473d-943e-88012137055c/hermes-home with config.yaml existing.`
- this proof used API-persisted env binding objects and the live resolved-config
  heartbeat patch
- the default `hermes_local` prompt path exposed a separate adapter contract:
  task fields live in the heartbeat context, but `hermes-paperclip-adapter`
  reads them from `ctx.config`

Longer-term hardening option:

- a host-side gateway/wrapper remains a valid future boundary if we later want
  stricter host/container separation than the current upstream CLI adapter model

### First-start note

On first dashboard start, Hermes may run an internal `npm install` or frontend
asset build before port `9119` actually begins listening. Do not treat an
immediate connection failure in the first few seconds as a broken install.

### Verification

From the node:

```bash
systemctl status hermes-dashboard.service --no-pager
ss -ltnp | grep 9119
curl -H 'Host: <node>.tailfedd3b.ts.net' http://<tailscale-ip>:9119/
```

From a tailnet client:

```bash
curl http://<node>.tailfedd3b.ts.net:9119/
```

Expected result:

- Hermes dashboard HTML is returned

## 9. What still comes later

Still to be layered on:

- Hermes config surface definition under `/root/.hermes`
- separation between outer Hermes memory and Paperclip-internal Hermes runs
