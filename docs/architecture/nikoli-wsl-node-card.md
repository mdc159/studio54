# Nikoli WSL Workstation Node Card

> **Status:** validated direct-control smoke; keep disabled in topology until
> Studio54 check/probe/dry-run support lands.
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
- no Studio54 topology enablement until check/probe/dry-run support exists;
- bounded one-line task envelopes for direct control;
- no prompt injection into arbitrary shells or panes.

## Studio54 Topology Recommendation

Keep Nikoli visible but disabled until grid support lands:

```json
{
  "name": "Nikolai",
  "enabled": false,
  "kind": "wsl-workstation-persona",
  "ssh_alias": "nikoli",
  "expected_tmux_session": "nikolai-hermes",
  "expected_window_label": "Nikolai",
  "notes": "Validated via Donna -> Tailscale SSH -> WSL tmux/Hermes smoke. Keep disabled until check/probe/dry-run support is implemented."
}
```

## Next Steps

1. Add Studio54 `hermes-grid` support for a disabled WSL workstation persona
   contract.
2. Add a non-mutating probe for `nikoli` that checks SSH, tmux session/window,
   Hermes presence, and GPU visibility metadata only.
3. Add dry-run attach output for Nikoli while still refusing live attach unless
   explicitly enabled.
4. Record the WSL workstation archetype beside the cloud VPS and mobile-edge
   archetypes.
5. Revoke any leaked Tailscale/admin invite or auth material from the admin
   console before treating the environment as fully clean.
