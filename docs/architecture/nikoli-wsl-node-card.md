# Nikoli WSL Workstation Node Card

> **Status:** validated direct-control smoke; Studio54 check/probe support is
> landing while live attach/topology enablement remains blocked pending explicit
> approval.
>
> **Safety note:** this document is intentionally redacted. Do not add Tailnet
> IPs, public IPs, invite tokens, private key paths, `.env` values, raw logs, or
> terminal scrollback.

## Summary

Nikoli is the first validated **WSL workstation / GPU-capable engineering
persona** in the Studio54 remote-persona grid.

The validated control path is:

```text
Donna / Studio54 cloud hub
  -> Tailscale
  -> Nikoli Ubuntu WSL2
  -> key-only OpenSSH
  -> tmux session `nikolai-hermes`
  -> tmux window `Nikolai`
  -> Hermes persona
```

This extends the grid beyond the earlier archetypes:

- Victoria: cloud VPS persona over SSH/tmux.
- Sam: Android/Termux mobile-edge persona over SSH, still lifecycle/WIP.
- Nikoli: WSL workstation persona over Tailscale SSH/tmux.

## Role

```yaml
id: nikoli-wsl
persona: Nikolai / Nikoli
role: WSL workstation / GPU-capable engineering persona
control_plane: Donna / Studio54
node_class: wsl-workstation-persona
transport: tailscale-ssh
status: validated-direct-control-smoke
topology_enabled: false
```

Nikoli is best suited for bounded local engineering work:

- code/repo work on the workstation;
- local build/prototype tasks;
- ML/CUDA/GPU environment inspection;
- controlled future GPU experiments;
- workstation capability checks and node-card reporting.

## Validated Facts

```yaml
host:
  os: Ubuntu 22.04.5 LTS
  runtime: WSL2
  distro: Ubuntu-22.04
  systemd: running

compute:
  cpu: 13th Gen Intel Core i9-13900H
  cpu_threads_visible: 20
  ram_total: 31 GiB
  swap_total: 8 GiB
  root_disk_total: 1007 GiB
  windows_c_mount_total: 1.8 TiB

gpu:
  visible: true
  device: NVIDIA GeForce RTX 4070 Laptop GPU
  vram: 8188 MiB
  driver: 591.74
  cuda_runtime_visible_via_nvidia_smi: 13.1
  nvcc: not found
  workload_started: false

dev_tools:
  python3: 3.10.12
  python: not found
  pip3: not found
  git: 2.34.1
  node: v20.20.0
  npm: 10.8.2
  docker_client: 29.3.1
  docker_engine: Docker Desktop 29.3.1
  tmux: 3.2a
  hermes: Hermes Agent v0.12.0, 2026.4.30

grid_connectivity:
  tailscale: installed and active
  tailscale_hostname: nikoli-wsl
  tailscale_ips: redacted
  ssh: active
  sshd: active
  auth: key-only Donna public key

hermes_tmux:
  session: nikolai-hermes
  window: Nikolai
  attached: false
  hermes_processes: active
```

## Direct-Control Validation

Donna validated the path with a bounded smoke prompt through tmux. Nikoli
acknowledged the route and performed no mutations.

Expected Donna-side access check:

```bash
ssh nikoli 'printf "NIKOLI_AUTH_OK\n"; hostname; whoami; uname -a'
```

Expected high-level result:

```text
NIKOLI_AUTH_OK
<WSL host label>
mdc159
Linux ... WSL2 ...
```

Expected tmux/Hermes check:

```bash
ssh nikoli 'tmux list-windows -t nikolai-hermes -F "session=#{session_name} window=#{window_name}"'
```

Expected result:

```text
session=nikolai-hermes window=Nikolai
```

## Safety Boundaries

Do not treat WSL workstation access as blanket permission to mutate local state.
Use the same ladder as the rest of the grid:

```text
discover -> check -> probe -> dry-run attach -> explicit approval -> bounded live attach -> topology enablement
```

Current boundaries:

- no public SSH exposure;
- no Windows-to-WSL port forwarding in the validated path;
- no raw Tailnet IPs in docs or ledgers;
- no `.env`, private keys, auth tokens, invite URLs, raw logs, or session DBs;
- no GPU jobs without explicit task scope;
- no Studio54 live attach/topology enablement until check/probe support passes
  and Miguel explicitly approves enablement;
- bounded one-line task envelopes for direct control;
- no prompt injection into arbitrary shells or panes.

## Studio54 Topology Recommendation

Keep Nikoli visible but disabled while grid support proves the path:

```json
{
  "name": "Nikolai",
  "enabled": false,
  "kind": "wsl-workstation-persona",
  "command": "ssh nikoli -t ~/.local/bin/nikolai-attach",
  "ssh_alias": "nikoli",
  "expected_tmux_session": "nikolai-hermes",
  "expected_window_label": "Nikolai",
  "notes": "Validated via Donna -> Tailscale SSH -> WSL tmux/Hermes smoke. Keep disabled until check/probe support passes and explicit enablement is approved."
}
```

## Next Steps

1. Run `./bin/hermes-grid --check` to verify Nikoli remains visible but
   disabled.
2. Run `./bin/hermes-grid --check --probe-remote` to verify non-mutating
   SSH/tmux/Hermes markers for Victoria and Nikoli.
3. Keep `./bin/hermes-grid attach Nikolai --dry-run` blocked while the tab is
   disabled; live attach remains a separate explicit enablement phase.
4. Record the WSL workstation archetype beside the cloud VPS and mobile-edge
   archetypes.
5. Next implementation gate: an explicit enablement PR only after Miguel
   approves live operator attach for Nikoli.
