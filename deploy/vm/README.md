# VM Rehearsal Notes

Use a local Ubuntu VM as the first clean-node rehearsal target before spending
another fresh VPS on bootstrap validation.

## Why a VM first

- faster to iterate
- easier to snapshot and revert
- good enough to validate host-native Hermes + compose-managed app plane
- avoids burning time and money on early VPS resets

## Recommended baseline

- Ubuntu 24.04 LTS
- 4-8 vCPU
- 12-32 GB RAM
- 100+ GB disk
- SSH enabled
- `open-vm-tools` installed if running under VMware
- networking can be NAT if it is stable and SSH is reachable from the host

## Known-state strategy

For local VM rehearsal, snapshots are the correct reset mechanism.

Use at least two snapshots:

1. `base-os`
   - Ubuntu installed
   - updates applied
   - SSH working
   - `open-vm-tools` installed
2. `base-host-prereqs`
   - git installed
   - Docker installed and working
   - any other required host bootstrap packages installed

Then rehearse the stack bootstrap from `base-host-prereqs`.

If the rehearsal goes sideways, revert the snapshot instead of trying to
manually scrub the VM back to a clean state.

## Current intended flow

The fastest rehearsal path is the idempotent startup script:

```bash
curl -fsSL https://raw.githubusercontent.com/mdc159/studio54/main/deploy/vm/studio54-vm-startup.sh \
  -o /tmp/studio54-vm-startup.sh
sudo bash /tmp/studio54-vm-startup.sh --branch main
```

For a local development branch or copied checkout, run the checked-in script
instead:

```bash
sudo bash deploy/vm/studio54-vm-startup.sh \
  --repo https://github.com/mdc159/studio54.git \
  --branch main \
  --dir /opt/studio54-bootstrap
```

Default behavior is conservative: install host prerequisites, clone/update the
repo, create/project runtime env files, and run `./bin/1215 doctor`. It does
not start the full container stack unless requested. The script checks outbound
internet first because apt, git, uv/PyPI, and Docker image pulls all require VM
egress; SSH reachability from the host is not sufficient.

Bring the prototype stack up during a rehearsal pass:

```bash
sudo bash deploy/vm/studio54-vm-startup.sh --with-up
```

Use a destructive reset pass only after taking a VM snapshot:

```bash
sudo bash deploy/vm/studio54-vm-startup.sh --reset-stack --with-smoke
```

Manual equivalent from the repo root on the VM:

```bash
cp .env.example .env
# edit .env for node-specific values
python3 stack/prototype-local/scripts/project_root_env.py --force
```

That projects the canonical repo-root env contract into:

- `stack/prototype-local/.env`

Current reality:
- the root `.env` is the operator control file
- the stack-local `.env` is still the file consumed by Docker Compose


## VM versus fresh VPS

Use the VM to validate:

- install paths
- host-native Hermes layout
- compose bringup
- env projection
- loopback listener contracts

Use a fresh VPS later to validate:

- real remote-node bootstrap
- Tailscale join flow
- provider-specific firewall and console behavior
- final end-to-end deployment shape
