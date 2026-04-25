# Paperclip hermes_local Contract

This document captures the proven `hermes_local` runtime contract from
`srv1264451`.

Primary related docs:

- Hermes runtime boundaries: [hermes-runtime.md](hermes-runtime.md)
- Company bootstrap path: [company-bootstrap.md](company-bootstrap.md)
- Operator runbook: [../../deploy/vps/INSTALL.md](../../deploy/vps/INSTALL.md)

## Runtime Contract

Paperclip can run Hermes through the `hermes_local` adapter when all of the
following are true.

### Hermes Exists In The Paperclip Environment

The Paperclip image must include a resolvable `hermes` CLI inside the Paperclip
execution environment.

The proven live path was:

- `/usr/local/bin/hermes -> /opt/hermes-agent/venv/bin/hermes`

Host-native Hermes alone is not enough for `hermes_local`.

### Launcher And Interpreter Permissions

Both the Hermes launcher and the Python interpreter used by the Hermes virtual
environment must be executable by the Paperclip runtime user.

The proven fix installs the Python used by the Hermes venv under `/opt` and
marks `/opt/uv-python` and `/opt/hermes-agent` readable/executable by the
Paperclip runtime user.

### Company Home Ownership

Prepared company Hermes homes must be writable by the Paperclip runtime
UID/GID.

The preparation script is:

- `stack/prototype-local/scripts/prepare_paperclip_hermes_home.py`

Default target path:

- `/paperclip/instances/<instance-id>/companies/<company-id>/hermes-home`

The script renders:

- `.env`
- `config.yaml`
- `honcho.json`
- `skills/`
- `sessions/`
- `logs/`
- `memories/`

For self-hosted Honcho, the generated `honcho.json` is profile-local under the
company `HERMES_HOME`. The proven mapping is:

- `baseUrl`: `HONCHO_BASE_URL`, defaulting to `http://127.0.0.1:18000`
- `workspace`: Paperclip company ID
- `peerName`: operator peer, defaulting to `operator-root`
- `aiPeer`: `paperclip-agent-<agent-id>` when the preparation step receives an
  agent ID

If `--agent-id` is not available at first preparation time, the script uses a
company-scoped fallback AI peer. Rerun it with `--agent-id` after agent creation
to get the final per-agent peer.

### Self-Hosted Honcho Runtime Dependency

When inner Hermes is expected to use Honcho, the Paperclip execution image must
include Hermes' Honcho provider dependency.

The intended image contract installs Hermes with the `honcho` extra so the
Paperclip runtime user's Hermes venv includes `honcho-ai`.

### Honcho Service Environment

The reference node runs self-hosted Honcho as `systemd --user` units from:

- `stack/services/honcho/honcho.service.in`
- `stack/services/honcho/honcho-deriver.service.in`

The generated service environment is:

- `/root/.config/1215-vps/honcho.env`

Honcho's module checkout can contain a developer `.env`. The service contract
sets `PYTHON_DOTENV_DISABLED=1` so the generated systemd `EnvironmentFile`
remains authoritative for database and provider settings.

### Resolved Adapter Config

Paperclip persists adapter env values as binding objects, for example:

```json
{
  "env": {
    "HERMES_HOME": {
      "type": "plain",
      "value": "/paperclip/instances/default/companies/<company-id>/hermes-home"
    }
  }
}
```

Local adapters must receive resolved runtime config, not unresolved persisted
binding objects.

Invalid observed failure shape:

- env value became `[object Object]`
- Hermes tried to use `[object Object]` as a path

The committed `heartbeat.ts` contract passes the resolved runtime config into:

- `ctx.config`
- `ctx.agent.adapterConfig`

### Assignment Wake Config

`hermes-paperclip-adapter` builds its default prompt from `ctx.config`.

For assignment wake paths, `heartbeat.ts` must surface these run fields into the
adapter config:

- `taskId`
- `taskTitle`
- `taskBody`
- `commentId`
- `wakeReason`

If these fields are only present in heartbeat context, `hermes-paperclip-adapter`
can degrade into its no-task heartbeat branch even during an issue assignment
wake.

## Known Observed Failure Modes

These were observed during the fresh-node proof work:

- `hermes` was on `PATH`, but execution as the `node` user failed with
  `Permission denied` because the venv Python pointed under
  `/root/.local/share/uv/...` and `/root` was not executable by that user.
- Host-side preparation created a root-owned company tree, so agent creation
  inserted the agent row and then failed while materializing managed
  instructions.
- Persisted adapter env binding objects were passed directly to the adapter,
  causing invalid environment values such as `[object Object]`.
- Assignment wake reached the adapter, but the adapter used its no-task
  heartbeat prompt branch because task fields were not surfaced through
  `ctx.config`.
- Honcho service startup failed when the module-local `.env` overrode the
  generated systemd environment and pointed migrations at `localhost:5432`
  instead of the shared substrate Postgres on `127.0.0.1:5433`.
- Inner Hermes saw `memory.provider: honcho`, but Honcho was unusable until
  the Paperclip image's Hermes venv included `honcho-ai`.

## Proof Artifacts

### First Proof

Fresh-node proof on `srv1264451`:

- company: `c754b277-80cc-47f3-8d54-90d02ff41b2d`
- agent: `d6ff8a00-730e-46fd-9d2d-124c428ab3fd`
- issue: `HER-1`
- successful runs:
  - `f415ff0c-de15-44c7-9238-bd0d44ba5150`
  - `a301c43d-29cd-4343-a75f-1297eb521e36`
  - `683f1a86-8ee7-44f3-8f34-af36c0947022`

Confirmed:

- `hermes_local` executed inside Paperclip
- the isolated company `HERMES_HOME` was used
- agent-authored comments confirmed the isolated home and `config.yaml`

### Second Proof

Second fresh-node proof on `srv1264451`:

- company: `ab6896c0-a9a8-473d-943e-88012137055c`
- agent: `8a5e57dc-ebe9-435b-a9d0-716c8826a4c6`
- issue: `HERA-1` / `6d1b1635-fb6c-45d5-b7d4-d65c113d124a`
- successful run: `3a2b0317-bee0-48fb-8cb1-2b4590bb9a6f`
- agent comment: `5ded90f3-32a1-4a2d-867b-63d191441a4b`

Confirmed:

- repeatability with a second company/agent
- assignment wake path through the normal heartbeat adapter execution path
- API-persisted `adapterConfig.env.HERMES_HOME` binding objects work after
  Paperclip resolves runtime config for local adapters
- agent-authored comment confirmed:
  `/paperclip/instances/default/companies/ab6896c0-a9a8-473d-943e-88012137055c/hermes-home`
  and `config.yaml`

### Honcho Proof

Fresh-node Honcho proof on `srv1264451`:

- company: `029b7499-feef-4a26-8b14-b7af0c293f78`
- agent: `b8c2fd7c-eb5d-4b90-a051-ee59484fff19`
- issue: `HON-1` / `5fcd3de5-c67b-4a30-b1e1-65e884f0cd61`
- successful run: `29fad228-f49b-4bbf-a066-826138a68d7a`

Confirmed:

- inner Hermes consumed the generated company `honcho.json`
- Honcho was self-hosted at `http://127.0.0.1:18000`
- no Honcho API key or managed Honcho dependency was used
- workspace was the Paperclip company ID
- AI peer was `paperclip-agent-b8c2fd7c-eb5d-4b90-a051-ee59484fff19`
- agent-authored comment confirmed Honcho tools were active and
  `honcho_profile` succeeded

## Verification Commands Used

Passed:

```bash
python3 -m py_compile stack/prototype-local/scripts/prepare_paperclip_hermes_home.py
python3 -m py_compile stack/prototype-local/scripts/project_hermes_runtime.py
```

Passed inside the prepared Paperclip container on `srv1264451`:

```bash
pnpm --filter @paperclipai/server typecheck
```

Local WSL typecheck did not run because the local nested Paperclip package
environment was not prepared.

## Open Questions

- Whether the `hermes-paperclip-adapter` package should also be updated so it
  can read task fields from heartbeat context directly.
- Whether a future host-side wrapper/gateway should replace the in-container CLI
  model for stricter separation. This is not required for the proven contract.
