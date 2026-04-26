# VPS Install Runbook

This is the procedural bring-up path for a fresh private-first Studio54 node.

Architecture contracts:

- Reference node target:
  [../../docs/architecture/reference-node-target.md](../../docs/architecture/reference-node-target.md)
- Hermes runtime:
  [../../docs/architecture/hermes-runtime.md](../../docs/architecture/hermes-runtime.md)
- Paperclip `hermes_local` contract:
  [../../docs/architecture/paperclip-hermes-local-contract.md](../../docs/architecture/paperclip-hermes-local-contract.md)
- Company bootstrap:
  [../../docs/architecture/company-bootstrap.md](../../docs/architecture/company-bootstrap.md)
- Knowledge repo:
  [../../docs/architecture/agent-knowledge-exchange.md](../../docs/architecture/agent-knowledge-exchange.md)

Current proven fresh node:

- host: `srv1264451`
- public IP: `191.101.0.164`
- deploy checkout: `/opt/studio54-bootstrap`

## 1. Host Prerequisites

Start from plain Ubuntu 24.04.

```bash
apt update
apt install -y ca-certificates curl git docker.io docker-compose-v2 ufw
systemctl enable --now docker
systemctl enable --now ssh
```

## 2. Firewall Baseline

Keep public inbound closed except SSH:

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw --force enable
```

Expected:

- public inbound is `22/tcp` only
- app services are not publicly reachable

## 3. Clone Studio54

```bash
mkdir -p /opt
cd /opt
git clone git@github.com:mdc159/studio54.git studio54-bootstrap
cd /opt/studio54-bootstrap
cp .env.example .env
```

Edit the root `.env`. It is the canonical operator control surface.

Set at least:

- `NODE_NAME`
- `DEPLOY_ROOT`
- `STACK_ENV_PATH`
- provider/model API keys intended for the node
- Hermes model/provider defaults if they should differ from the template

## 4. Project Runtime Files

Generate runtime files from the root `.env`:

```bash
python3 stack/prototype-local/scripts/project_root_env.py
python3 stack/prototype-local/scripts/init_env.py
python3 stack/prototype-local/scripts/project_hermes_runtime.py
```

Generated files are not the source of truth. Edit root `.env`, then regenerate.

Generated outputs include:

- `stack/prototype-local/.env`
- `/root/.hermes/.env`
- `/root/.hermes/config.yaml`

## 5. Start The Container Stack

```bash
cd /opt/studio54-bootstrap/stack/prototype-local
docker compose -f docker-compose.substrate.yml up -d
```

Expected local service URLs:

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

## 6. Install And Join Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
systemctl enable --now tailscaled
tailscale up --ssh
```

Operator-required step:

1. open the login URL from `tailscale up`
2. authorize the node into the intended tailnet
3. verify:

```bash
tailscale status
tailscale ip -4
```

## 7. Publish Operator Services Privately

Publish containerized operator services with Tailscale Serve:

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

Verify:

```bash
tailscale serve status
```

Expected private URL shape:

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

## 8. Install Outer Hermes

Install host prerequisites:

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

Expected:

- `/root/.local/bin/hermes -> /root/.hermes/hermes-agent/venv/bin/hermes`
- `/root/.hermes/.env`
- `/root/.hermes/config.yaml`

## 9. Install Hermes Dashboard Unit

Create `/etc/systemd/system/hermes-dashboard.service`:

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

Allow direct tailnet access:

```bash
ufw allow in on tailscale0 to any port 9119 proto tcp
```

Verify:

```bash
systemctl status hermes-dashboard.service --no-pager
ss -ltnp | grep 9119
curl http://<node>.tailfedd3b.ts.net:9119/
```

## 10. Install Self-Hosted Honcho

Honcho runs host-native under `systemd --user` and listens only on loopback.
It uses the shared substrate Postgres database created by the compose
`postgres-bootstrap` service.

Install and start the units:

```bash
cd /opt/studio54-bootstrap
PATH=/root/.local/bin:$PATH bash stack/services/honcho/install.sh
systemctl --user enable --now honcho honcho-deriver
```

Verify:

```bash
systemctl --user is-active honcho honcho-deriver
curl -fsS http://127.0.0.1:18000/health
```

Expected:

- both units are `active`
- health returns `{"status":"ok"}`
- Honcho reads `/root/.config/1215-vps/honcho.env`
- the generated unit config disables Honcho's module-local developer `.env`
  from overriding the systemd environment

## 11. Bootstrap A One-Agent hermes_local Company

Use the reference one-agent bootstrap script for the active direct
`hermes_local` path:

```bash
cd /opt/studio54-bootstrap
python3 stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py \
  --company-name "<company-name>" \
  --company-description "<company-description>" \
  --agent-name "<agent-name>" \
  --agent-role general \
  --agent-title "Operator" \
  --model "<model>" \
  --issue-title "<validation-issue-title>"
```

For a fresh validation run, add:

```bash
--always-create-issue
```

The script:

- waits for Paperclip health
- creates or reuses a company by exact name
- prepares the company-scoped Hermes home
- creates or reuses one `hermes_local` agent
- pins the model
- configures `adapterConfig.env.HERMES_HOME`
- rerenders `honcho.json` with `aiPeer = paperclip-agent-<agent-id>`
- creates one assigned validation issue
- prints a JSON summary with company, agent, Hermes home, Honcho peer, issue,
  and verification API paths

The script prepares the Docker volume path derived from
`PAPERCLIP_CONFIG_HOST_PATH`. The corresponding container-visible Hermes home is:

```text
/paperclip/instances/default/companies/<company-id>/hermes-home
```

The prepared home includes:

- `.env`
- `config.yaml`
- `skills/`
- `sessions/`
- `logs/`
- `memories/`
- `honcho.json`

It also sets ownership for the company directory and Hermes home to the
Paperclip runtime UID/GID.

Older gateway-oriented bootstrap paths, including
`bootstrap_paperclip_ceo.py`, are historical/optional/future-state. They are
not the active direct `hermes_local` bootstrap contract.

## 12. Verify The Bootstrap Proof

The validation issue should ask the agent to confirm:

- the active `HERMES_HOME`
- whether `config.yaml` exists
- whether `honcho.json` exists
- whether the issue completed through the direct-path final PATCH contract

Verify:

- heartbeat run succeeds
- agent-authored comment/result exists
- comment has the assigned agent as `authorAgentId`
- comment has the heartbeat run as `createdByRunId`
- issue reaches `done` through the agent's explicit final PATCH
- comment confirms the isolated company `HERMES_HOME`
- comment confirms `config.yaml`
- assignment wakes surface task fields into adapter config so
  `hermes-paperclip-adapter` does not fall into its no-task heartbeat branch

Completion contract:

- Paperclip does not infer issue completion from adapter/process success.
- The agent must close the issue through Paperclip.
- The final direct-path completion action is one PATCH containing both
  `status: "done"` and the completion comment body, sent with
  `X-Paperclip-Run-Id: $PAPERCLIP_RUN_ID`.

Keep one durable test company unless there is a reason to archive it.

Known successful proof artifacts on `srv1264451`:

Reusable one-agent bootstrap proof:

- company: `ee440385-653c-451d-9058-dc6aa76afd9f`
- agent: `fceca8ee-bbc8-45a0-a853-420a7534c1b2`
- issue: `BOO-1` / `8002bc7e-bf91-46c6-88d5-d6d111735bc3`
- successful run: `8a6a5f36-d582-4986-8633-a2b578bee0ff`
- agent comment: `a54ae77d-3fa6-4087-8968-47393c547158`

First proof:

- company: `c754b277-80cc-47f3-8d54-90d02ff41b2d`
- agent: `d6ff8a00-730e-46fd-9d2d-124c428ab3fd`
- issue: `HER-1`
- successful runs:
  - `f415ff0c-de15-44c7-9238-bd0d44ba5150`
  - `a301c43d-29cd-4343-a75f-1297eb521e36`
  - `683f1a86-8ee7-44f3-8f34-af36c0947022`

Second proof:

- company: `ab6896c0-a9a8-473d-943e-88012137055c`
- agent: `8a5e57dc-ebe9-435b-a9d0-716c8826a4c6`
- issue: `HERA-1` / `6d1b1635-fb6c-45d5-b7d4-d65c113d124a`
- successful run: `3a2b0317-bee0-48fb-8cb1-2b4590bb9a6f`
- agent comment: `5ded90f3-32a1-4a2d-867b-63d191441a4b`

Direct completion proof:

- company: `56ef02eb-5b90-446b-bbaa-54dcfccefaf6`
- agent: `25d3a8f2-684b-4d85-a66b-639639b6b5ed`
- issue: `STU-5` / `b9b65393-85b2-43d0-a57e-80b5ac40f515`
- successful run: `5ee70dd1-064c-47d5-b934-b834c60de49a`
- agent comment: `ddea9910-29b1-4014-a3f6-3f7bad891333`
- result: one direct `hermes_local` assignment run posted the useful comment,
  attributed it to the agent/run, and left the issue `done`

## 13. Bootstrap A Manager/Worker hermes_local Company

Use the same bootstrap script with the proven manager/worker topology:

```bash
cd /opt/studio54-bootstrap
python3 stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py \
  --topology manager-worker \
  --company-name "<company-name>" \
  --company-description "<company-description>" \
  --manager-name "<manager-name>" \
  --manager-role general \
  --manager-title "Manager" \
  --worker-name "<worker-name>" \
  --worker-role general \
  --worker-title "Worker" \
  --model "<model>" \
  --manager-worker-issue-title "<validation-parent-title>"
```

For a fresh validation parent, add:

```bash
--always-create-issue
```

The script creates or reuses one company, one manager `hermes_local` agent, one
worker `hermes_local` agent, and one validation parent issue assigned to the
manager.

Current runtime-home caveat:

- manager and worker share the company-scoped `HERMES_HOME`
- this is the current practical contract
- per-agent Hermes homes are not implemented yet

Delegated worker issue sequencing rule:

1. create the child linked to the parent with `parentId`
2. leave it unassigned and `backlog` at creation time
3. activate it with one PATCH setting:
   - `assigneeAgentId: <worker-agent-id>`
   - `status: "todo"`

This sequencing avoids the create-time assignment wake race observed during the
first manager/worker proof. That failed run was a Paperclip embedded Postgres
setup failure while loading `pg_trgm`; it did not reach Hermes and was not a
Honcho or shared-home failure.

Clean manager/worker proof on `srv1264451`:

- company: `e8613a66-ff00-43af-b4a0-cde3a16a1bcf`
- manager: `bf391c48-bd92-40c0-808d-5e0ab6b8caa3`
- worker: `4840065d-324f-4542-b773-2f6f4cbf1c6e`
- parent: `BOOAAA-1` / `88aa3912-64a7-4935-890f-38575c10071b`
- child: `BOOAAA-2` / `c187d982-d375-4b4f-9a8f-6aab67db8828`
- result: no failed worker assignment run; child and parent ended `done`; all
  observed runs settled as `succeeded`

## 14. Sync The Knowledge Repo

Clone or update:

```bash
cd /opt
if [ ! -d agent-knowledge-exchange/.git ]; then
  git clone git@github.com:mdc159/agent-knowledge-exchange.git agent-knowledge-exchange
fi
cd /opt/agent-knowledge-exchange
git pull --ff-only
```

Use the node-local secret loader when needed:

```bash
source /root/.config/agent-knowledge-exchange/env
```

Promote reusable operational findings to the knowledge repo. Keep live runtime
state in Paperclip, Docker volumes, and service-specific storage.

Use issues for proof summaries and PRs for durable doc updates. The repo is a
shared operational knowledge layer, not a substitute for Paperclip workflow
state or infrastructure backups.

## 15. Reboot Verification

After reboot:

```bash
systemctl is-active ssh docker tailscaled hermes-dashboard.service
docker ps
tailscale serve status
curl -fsS http://127.0.0.1:3100/api/companies >/dev/null
```

Expected:

- host services are active
- container stack is up
- Tailscale Serve mappings remain present
- Paperclip responds locally
- Hermes dashboard is reachable on the tailnet

## Open Questions

- Whether Tailscale authorization should remain manual or use reusable auth-key
  provisioning.
- Which parts of this runbook should become one idempotent bootstrap command.
