# Paperclip hermes_local Contract

Canonical architecture entrypoint: [canonical/README.md](canonical/README.md).

This document captures the proven `hermes_local` runtime contract from
`srv1264451`.

Primary related docs:

- Canonical launch/operation map:
  [canonical/vps-launch-and-company-operation.md](canonical/vps-launch-and-company-operation.md)
- Hermes runtime boundaries: [hermes-runtime.md](hermes-runtime.md)
- Company bootstrap path: [company-bootstrap.md](company-bootstrap.md)
- Operator runbook: [../../deploy/vps/INSTALL.md](../../deploy/vps/INSTALL.md)

## Runtime Contract

Paperclip can run Hermes through the `hermes_local` adapter when all of the
following are true.

The active Paperclip execution contract is direct per-company `hermes_local`.
The 1215 Paperclip -> Hermes gateway path is optional/future-state for
Paperclip task execution until it has first-class issue/comment/result
plumbing.

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

The reference bootstrap script that drives company creation, home preparation,
agent creation, agent-aware Honcho rendering, and validation issue creation is:

- `stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py`

Proven topologies:

- `--topology one-agent`
- `--topology manager-worker`

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

For the current manager/worker bootstrap topology, manager and worker share the
same company-scoped `HERMES_HOME`. This is the current practical runtime
contract. It should not be described as per-agent Hermes memory isolation.
Per-agent Hermes homes remain future work.

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

### Task Completion Contract

Paperclip is the system of record for issue/task state. A successful
`hermes_local` process exit does not by itself mean the assigned issue is done.

For bounded assigned work, the inner Hermes agent must explicitly close the
issue through Paperclip. The proven final action is one run-scoped PATCH that
includes both:

```json
{
  "status": "done",
  "comment": "DONE: <completion summary>"
}
```

The request must include:

- `Authorization: Bearer $PAPERCLIP_API_KEY`
- `X-Paperclip-Run-Id: $PAPERCLIP_RUN_ID`

This single PATCH lets Paperclip persist the terminal issue state and create
the completion comment with the same run attribution. Paperclip should not infer
task completion merely from adapter/process success.

For Langfuse lookup, use the same Paperclip run ID. On the direct
`hermes_local` path, `PAPERCLIP_RUN_ID`, `HERMES_RUN_ID`, and
`LANGFUSE_TRACE_ID` are the same value, so the Paperclip run ID is the Langfuse
trace ID. See [Langfuse Traceability](langfuse-traceability.md) for capture
policy and trace-record expectations, and
[Langfuse Integration Status](langfuse-integration-status.md) for the broader
cleanup plan and benefits. The current Langfuse work covers direct
`hermes_local` OpenAI-compatible model-call tracing only; it is not full
Paperclip API, gateway, broker, tool-call, n8n, Honcho, or artifact tracing.

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
- A successful bounded run posted the requested issue comment but left the
  issue `in_progress` when completion was split across separate comment and
  status-update actions. The active prompt now directs the agent to complete
  with one PATCH containing both `status: "done"` and `comment`.
- A manager-created worker issue produced one fast failed assignment run when
  the child was created already assigned. The run failed during Paperclip setup
  with embedded Postgres `pg_trgm` loading, before Hermes executed. The active
  manager/worker bootstrap avoids this by creating the linked child first in
  `backlog` with no assignee, then activating it with a PATCH that sets
  `assigneeAgentId` and `status: "todo"`.

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

### Direct Completion Proof

Fresh-node direct-path completion proof on `srv1264451`:

- company: `56ef02eb-5b90-446b-bbaa-54dcfccefaf6`
- agent: `25d3a8f2-684b-4d85-a66b-639639b6b5ed`
- issue: `STU-5` / `b9b65393-85b2-43d0-a57e-80b5ac40f515`
- successful run: `5ee70dd1-064c-47d5-b934-b834c60de49a`
- agent comment: `ddea9910-29b1-4014-a3f6-3f7bad891333`

Confirmed:

- direct `hermes_local` assignment wake completed in one run
- useful issue comment was authored by the assigned agent
- `createdByRunId` matched the assignment run
- issue ended in `done`
- no direct-path wake-loop regression was observed

### Reusable One-Agent Bootstrap Proof

Fresh-node reusable bootstrap proof on `srv1264451`:

- company: `ee440385-653c-451d-9058-dc6aa76afd9f`
- agent: `fceca8ee-bbc8-45a0-a853-420a7534c1b2`
- issue: `BOO-1` / `8002bc7e-bf91-46c6-88d5-d6d111735bc3`
- successful run: `8a6a5f36-d582-4986-8633-a2b578bee0ff`
- agent comment: `a54ae77d-3fa6-4087-8968-47393c547158`

Confirmed:

- `bootstrap_paperclip_hermes_company.py` created the company, one
  `hermes_local` agent, company-scoped Hermes home, and validation issue
- the generated `honcho.json` used the Paperclip company ID as workspace
- the generated `honcho.json` used
  `aiPeer = paperclip-agent-fceca8ee-bbc8-45a0-a853-420a7534c1b2`
- the assigned run succeeded through the direct `hermes_local` path
- the final completion comment was authored by the assigned agent
- `createdByRunId` matched the assignment run
- the issue ended `done`
- no direct-path wake-loop regression was observed after a quiet-period check

### Reusable Manager/Worker Bootstrap Proof

Fresh-node reusable manager/worker bootstrap proof on `srv1264451`:

- company: `e8613a66-ff00-43af-b4a0-cde3a16a1bcf`
- manager: `bf391c48-bd92-40c0-808d-5e0ab6b8caa3`
- worker: `4840065d-324f-4542-b773-2f6f4cbf1c6e`
- parent: `BOOAAA-1` / `88aa3912-64a7-4935-890f-38575c10071b`
- child: `BOOAAA-2` / `c187d982-d375-4b4f-9a8f-6aab67db8828`

Confirmed:

- `bootstrap_paperclip_hermes_company.py --topology manager-worker` created
  the company, manager, worker, shared company-scoped Hermes home, and
  validation parent issue
- manager and worker used direct `hermes_local`
- manager and worker shared the same company-scoped `HERMES_HOME`
- the manager created exactly one linked child issue
- the child issue had the correct `parentId`
- the worker completed the child issue
- the manager closed the parent after child completion
- parent and child ended `done`
- all observed runs settled as `succeeded`
- no failed worker assignment run occurred after the create-then-activate
  sequencing rule was applied

## Verification Commands Used

Passed:

```bash
python3 -m py_compile stack/prototype-local/scripts/prepare_paperclip_hermes_home.py
python3 -m py_compile stack/prototype-local/scripts/project_hermes_runtime.py
python3 -m py_compile stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py
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
  model for stricter separation. This is optional/future-state and is not the
  active Paperclip execution contract.
