# Hermes Bootstrap Contract

Concrete rebuild contract for the Hermes runtime on the Donna / Studio54
reference node.

This is not a full automation script yet. It is the defined sequence that a
fresh Ubuntu VPS would need to reproduce the current Hermes installation shape
without rediscovering it by hand.

Related documents:

- Runtime definition: [hermes-runtime.md](hermes-runtime.md)
- Live node inventory: [donna-vps-service-map.md](donna-vps-service-map.md)
- Reference-node target: [reference-node-target.md](reference-node-target.md)

## Scope

This contract covers the host-native Hermes installation only:

- source checkout
- Python runtime and virtualenv
- CLI shim
- dashboard systemd unit
- private network exposure

It does not yet attempt to automate:

- provider/model configuration
- messaging gateway configuration
- long-term profile or memory seeding
- any Paperclip-side CEO bootstrap

## Live Donna Baseline

Observed on the live reference node:

- source repo: `https://github.com/NousResearch/hermes-agent.git`
- branch: `main`
- commit at inspection time: `ff9752410a8dba62f1b246aeed9142893c75b4ba`
- checkout path: `/root/.hermes/hermes-agent`
- runtime home: `/root/.hermes`
- CLI shim: `/root/.local/bin/hermes`
- venv python: `3.11` via `uv`
- Node runtime observed: `v20.20.2`
- systemd unit: `/etc/systemd/system/hermes-dashboard.service`

The current installation is a source checkout plus local virtualenv. It is not
a distro package and not a container image.

## Required Host Prerequisites

Donna currently has these relevant host prerequisites installed:

- `git`
- `python3-venv`
- `build-essential`
- `tailscale`
- Docker packages for the broader node runtime
- Node and npm available on the host

For Hermes specifically, the critical prerequisites are:

- `git`
- a working shell environment for the target service user
- `uv`
- Python 3.11 available through `uv`
- Node/npm present for Hermes web asset builds

## Preferred Install Path

The live node is consistent with Hermes's upstream developer install flow.

Reference shape:

1. clone Hermes source into `/root/.hermes/hermes-agent`
2. create a Python 3.11 virtualenv inside that checkout
3. install Hermes into the venv from the source tree
4. expose the CLI at `/root/.local/bin/hermes`
5. manage the dashboard with `systemd`

This means the canonical on-node relationship is:

- source checkout under `/root/.hermes/hermes-agent`
- executable resolved through `/root/.local/bin/hermes`
- service owned by `systemd`, not by an interactive shell

## Rebuild Sequence

On a fresh Ubuntu VPS, the rebuild sequence should be:

1. Create the Hermes runtime directories:

```bash
mkdir -p /root/.hermes
mkdir -p /root/.local/bin
mkdir -p /var/log/hermes-dashboard
```

2. Clone the Hermes source:

```bash
git clone https://github.com/NousResearch/hermes-agent.git /root/.hermes/hermes-agent
cd /root/.hermes/hermes-agent
```

3. Install `uv` if missing:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

4. Build the Hermes venv using Python 3.11:

```bash
cd /root/.hermes/hermes-agent
./setup-hermes.sh
```

The upstream script already encodes the intended developer/server install path:

- ensures `uv` exists
- ensures Python 3.11 exists through `uv`
- creates `venv`
- installs Hermes and extras into that venv
- places a `hermes` command in `~/.local/bin`

5. Ensure the CLI shim resolves correctly:

```bash
ls -l /root/.local/bin/hermes
```

Expected shape:

- `/root/.local/bin/hermes -> /root/.hermes/hermes-agent/venv/bin/hermes`

6. Install the dashboard unit:

```ini
[Unit]
Description=Hermes Agent Web Dashboard (Donna)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
Environment=HOME=/root
Environment=PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/root/.local/bin/hermes dashboard --host donna.tailfedd3b.ts.net --port 9119 --no-open --insecure
Restart=on-failure
RestartSec=5
StandardOutput=append:/var/log/hermes-dashboard/stdout.log
StandardError=append:/var/log/hermes-dashboard/stderr.log

[Install]
WantedBy=multi-user.target
```

7. Reload and enable:

```bash
systemctl daemon-reload
systemctl enable --now hermes-dashboard.service
```

## Why The Unit Uses MagicDNS

Donna does not run Hermes on `127.0.0.1` in steady state.

Reason:

- Hermes dashboard validates the request `Host` header against the hostname it
  was bound to
- generic reverse proxying to a loopback-bound Hermes dashboard is therefore
  awkward
- binding Hermes directly to `donna.tailfedd3b.ts.net` on the Tailscale
  interface gives a private-only path that also satisfies Hermes's host-header
  checks

That is why the current contract is:

- `--host donna.tailfedd3b.ts.net`
- `--insecure`

The `--insecure` flag is required because Hermes interprets any non-loopback
bind as opt-in to broader exposure. On Donna, the real protection comes from:

- Tailscale scoping
- UFW allowing only public SSH
- no public HTTP ingress

## Known Live Quirks

These should be treated as part of the current reality, not hidden:

1. Hermes may build web assets on first dashboard start or after dependency
   changes. A freshly restarted service can take a short period before port
   `9119` begins listening.

2. The live checkout currently has minor local drift:

- modified `package-lock.json`
- extra `venv_new/` directory

That drift should not be treated as desired state for rebuilds.

3. The venv is Python 3.11 via `uv`, even though the host default `python3` is
   3.12. That version split is intentional in the current install shape and
   should be preserved unless Hermes's upstream install requirements change.

## Verification

Minimum verification after rebuild:

```bash
systemctl status hermes-dashboard.service --no-pager
ss -ltnp | grep 9119
curl -H 'Host: donna.tailfedd3b.ts.net' http://100.x.y.z:9119/
```

From a tailnet client:

```bash
curl http://donna.tailfedd3b.ts.net:9119/
```

Expected result:

- Hermes dashboard HTML is returned

## Future Repo Work

This contract is ready to be turned into repo-owned assets later:

- checked-in systemd unit template
- checked-in host bootstrap script
- idempotent Hermes install or repair script
- explicit version pinning policy for the Hermes checkout

The important sequencing rule is:

- first define the live rebuild path
- then automate that path
- do not automate an unclear path
