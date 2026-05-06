# prototype-local

`prototype-local` is the first runnable local-node implementation for the 1215
architecture. It is not a throwaway dev stack. It exists to validate the
shared continuity contracts, localhost-only exposure model, and the service mix
before hardening the VPS hub.

Within the broader split model, `prototype-local` is the first proof of:

- shared core contracts
- the VPS-oriented orchestration surface
- optional `media-cpu` and `tools` role overlays

See [Deployable Unit](../../docs/architecture/deployable-unit.md) for the
repo-level assembly map: shared contracts live once, capabilities are enabled by
role overlays, and each node should select roles through a small local manifest
under `nodes/`.

The first executable seam for that model now lives in `bin/1215` (alias
`start-1215`):

```bash
./bin/1215 nodes
./bin/1215 show-node linux-prototype
./bin/1215 compose-cmd linux-prototype config
./bin/1215 compose linux-prototype up -d
```

For day-to-day lifecycle, `bin/1215` exposes unified bringup/teardown commands
for the compose-managed substrate:

```bash
./bin/1215 up       # seed .env, compose up -d --wait
./bin/1215 status   # per-service STATE / HEALTH / PORT / HINT table
./bin/1215 smoke    # exposure + canary + gate_shared_core invariants
./bin/1215 logs <service>
./bin/1215 down     # compose down (preserves volumes)
```

The thin wrappers `stack/prototype-local/scripts/launch.sh` and
`stack/prototype-local/scripts/shutdown.sh` exist as the documented entry
points for fresh clones; both delegate to `./bin/1215 up` / `./bin/1215
down`.

### Tier-0 seed (`hermes-zero`)

`./bin/1215 seed-hermes` installs a minimum-viable Hermes profile at
`/var/lib/hermes/hermes-zero/` with five stdlib-only skills
(`read-file`, `write-file`, `append-file`, `run-shell`, `git-commit`).
The seed is structurally isolated from `orchestrator-ceo` and has no
substrate dependencies, so it can run before the compose stack is even
up. See
[`docs/architecture/hermes-zero-seed.md`](../../docs/architecture/hermes-zero-seed.md)
for the design rationale, pilot runbook, and tier-1 guardrails.

Today the example node manifests all resolve through the `prototype-local`
target because this is still the first full runnable substrate. The important
part is that node selection now happens through repo-owned manifests and
role-to-profile mapping, not by hand-editing docker commands per machine.

Selected roles may also contribute compose fragments. For example, `media-cpu`
and `media-gpu` now resolve through role-specific compose files under
`stack/roles/`, which makes it possible to keep the shared stack definition
while still overriding ComfyUI runtime intent per node.

## Current runtime scope

Today the runnable `prototype-local` compose includes these repo-owned or
repo-configured local services:

- Broker API
- Postgres
- Valkey
- MinIO
- Qdrant
- Neo4j
- ClickHouse
- Langfuse
- Open WebUI
- n8n
- Paperclip
- `n8n-mcp`
- ComfyUI

It does **not** include these as compose services:

- Hermes gateway
- Honcho

Those exist as host-native service scaffolding under `stack/services/`.

`n8n-mcp`, Paperclip, and the ComfyUI media path are therefore part of the
current prototype target, while Hermes gateway and Honcho remain host-native
additions rather than compose-managed services.

## Prototype done bar

`prototype-local` should only be treated as the shared-core prototype when all
of the following are true:

- Open WebUI -> `n8n` -> broker works through authenticated API calls
- Open WebUI -> `n8n` -> ComfyUI -> MinIO -> broker artifact registration works
- `n8n-mcp` is up, authenticated, and functionally verified against local `n8n`
- Paperclip can invoke Hermes through the supported `hermes_local` CLI adapter
  with an isolated per-company `HERMES_HOME`
- Hermes uses Honcho and recalls durable memory across sessions
- fake-secret canary checks pass
- restart resilience passes without manual repair

## Bring-up

Initialize a local env file first:

```bash
python3 stack/prototype-local/scripts/init_env.py
```

This renders `stack/prototype-local/.env` with local-only secrets, composes
`HONCHO_DB_CONNECTION_URI` from `HONCHO_DB_PASSWORD`, leaves provider/API keys
blank for explicit operator input, preserves existing secret values on
re-renders so mounted runtime state does not drift, and keeps the committed
[stack/prototype-local/.env.example](.env.example)
as the repo contract.

Then bring the stack up:

```bash
./bin/1215 up --target prototype-local
./bin/1215 status --target prototype-local
curl http://127.0.0.1:8090/healthz
```

All currently implemented ports bind to `127.0.0.1` only in this slice.

After the containers are up, complete operator-owned first login for the UI
surfaces:

1. open Open WebUI and create the initial admin account manually
2. open `n8n` and create the initial owner/admin account manually
3. generate the `n8n` API key inside `n8n` if `n8n-mcp` needs it
4. paste that key into the ignored `stack/prototype-local/.env`
5. if you want the repo-owned follow-on scripts to authenticate on your behalf,
   also place your chosen Open WebUI and `n8n` login values into the ignored
   `.env`

Then run the repo-owned follow-on wiring:

```bash
python3 stack/prototype-local/scripts/bootstrap_n8n.py
python3 stack/prototype-local/scripts/sync_openwebui_functions.py
python3 stack/prototype-local/scripts/test_openwebui_n8n_broker.py
```

Important: the current `bootstrap_n8n.py` and `sync_openwebui_functions.py`
scripts now default to reusing an operator-created account. Direct owner/admin
seeding is a legacy helper path behind explicit flags (`--seed-owner`,
`--seed-admin`). The intended flow is operator-owned first login, followed by
workflow/function wiring.

To verify host-native Honcho and Hermes memory provider wiring after the
compose substrate is running:

```bash
python3 stack/prototype-local/scripts/setup_hermes_honcho_paperclip.py
```

This script:

- expects the compose substrate Postgres and host-native Honcho service path
- verifies Honcho API/deriver availability on `127.0.0.1:18000`
- configures Hermes to use Honcho memory and a selectable model
- runs an optional Hermes/Honcho cross-session memory smoke test

### Paperclip instance contract

Donna's reference-node contract expects a real Paperclip instance config file
at:

- `/paperclip/instances/default/config.json`

Tracked template:

- [paperclip.instance.config.json.example](paperclip.instance.config.json.example)

The reference node should not rely on an absent `PAPERCLIP_CONFIG` target plus
Paperclip's internal missing-file fallback behavior.

These follow-on scripts are intended to wire repo-owned workflows and function
state after the operator has claimed ownership in the UI:

- verify or reuse the local `n8n` owner/project state
- import the repo-owned `n8n` credentials and workflow JSON
- activate the expected webhook workflows
- ensure the local `langfuse` database exists before Langfuse services start
- verify or reuse the local Open WebUI admin state
- upsert the repo-owned Open WebUI function models and verify they appear in
  `/api/models`

## Entry points

Current local entry points for the validated prototype path:

- Broker API: `http://127.0.0.1:8090`
- Open WebUI UI/API: `http://127.0.0.1:8080`
- n8n UI/API: `http://127.0.0.1:5678`
- Prototype `n8n` webhook: `http://127.0.0.1:5678/webhook/prototype-postgres-tables`
- MinIO S3 API: `http://127.0.0.1:9010`
- MinIO Console: `http://127.0.0.1:9011`
- Prototype MinIO webhook: `http://127.0.0.1:5678/webhook/prototype-minio-buckets`
- `n8n-mcp` HTTP server: `http://127.0.0.1:13000`
- ComfyUI UI/API: `http://127.0.0.1:8188`

Repo-owned workflow and function artifacts:

- Open WebUI pipe: [stack/prototype-local/open-webui/functions/prototype_n8n_pipe.py](open-webui/functions/prototype_n8n_pipe.py)
- Open WebUI ComfyUI pipe: [stack/prototype-local/open-webui/functions/prototype_comfyui_pipe.py](open-webui/functions/prototype_comfyui_pipe.py)
- Open WebUI -> `n8n` -> broker smoke test: [stack/prototype-local/scripts/test_openwebui_n8n_broker.py](scripts/test_openwebui_n8n_broker.py)
- n8n manual smoke workflow: [stack/prototype-local/n8n/Get_Prototype_Postgres_Tables.json](n8n/Get_Prototype_Postgres_Tables.json)
- n8n webhook smoke workflow: [stack/prototype-local/n8n/Get_Prototype_Postgres_Tables_Webhook.json](n8n/Get_Prototype_Postgres_Tables_Webhook.json)
- n8n MinIO webhook smoke workflow: [stack/prototype-local/n8n/List_Prototype_Minio_Buckets_Webhook.json](n8n/List_Prototype_Minio_Buckets_Webhook.json)
- n8n ComfyUI smoke workflow: [stack/prototype-local/n8n/Get_Prototype_ComfyUI_System_Stats_Webhook.json](n8n/Get_Prototype_ComfyUI_System_Stats_Webhook.json)
- n8n ComfyUI SD1.5 queue workflow: [stack/prototype-local/n8n/Queue_Prototype_ComfyUI_SD15_Webhook.json](n8n/Queue_Prototype_ComfyUI_SD15_Webhook.json)
- n8n ComfyUI SD1.5 artifact workflow: [stack/prototype-local/n8n/Generate_Prototype_ComfyUI_SD15_Artifact_Webhook.json](n8n/Generate_Prototype_ComfyUI_SD15_Artifact_Webhook.json)

The currently validated E2E path is:

1. Open WebUI `pipe` model `prototype_n8n_pipe`
2. `POST` request to the local `n8n` webhook
3. `n8n` upserts the broker node, upserts the continuity session, starts and completes a broker run, and records a `workflow.completed` broker event
4. `n8n` queries Postgres and returns both the table summary and continuity IDs
5. assistant response returned through Open WebUI `/api/chat/completions`

The currently validated media/storage path is:

1. `n8n` runs with local `ffmpeg` and `ffprobe` available in the container
2. MinIO exposes `artifacts` and `langfuse` buckets on the local Docker network
3. `n8n` S3 credential `Prototype Local MinIO` points at `http://minio:9000`
4. `GET /webhook/prototype-minio-buckets` returns the live MinIO bucket list
5. `shared-data-init` prepares `/data/shared/prototype-media` so containerized
   media workflows can write artifacts before upload
6. `n8n` widens `N8N_RESTRICT_FILE_ACCESS_TO` to include `/data/shared`
7. `n8n` sets `N8N_BLOCK_FILE_ACCESS_TO_N8N_FILES=false` so `Read Binary File`
   can consume media generated under `~/.n8n-files/prototype-media` before S3
   upload

## Media surfaces

The intended split is:

- ComfyUI: media generation surface
- `n8n` + `ffmpeg`: orchestration, transcoding, thumbnails, muxing, and post-processing
- MinIO: durable local artifact exchange instead of opaque Docker-volume-only handoff

This prevents generation, processing, and storage from collapsing into a single
tool boundary.

## n8n-mcp profile

The compose file currently defines `n8n-mcp` under the `tools` profile. For the
prototype done bar, `n8n-mcp` should be started and validated whenever the
local stack is exercised as the shared-core prototype:

```bash
docker compose --env-file stack/prototype-local/.env \
  -f stack/prototype-local/docker-compose.substrate.yml \
  --profile tools up -d n8n-mcp
```

Current local assumptions:

- `n8n-mcp` listens on `http://127.0.0.1:13000`
- it reaches local `n8n` over the Docker network at `http://n8n:5678`
- it uses `N8N_API_KEY` from `stack/prototype-local/.env` for management tools
- it uses `N8N_MCP_AUTH_TOKEN` for HTTP-mode auth
- `stack/prototype-local/scripts/init_env.py` intentionally leaves
  `N8N_API_KEY` blank so a fresh local API key can be created in `n8n` and
  pasted into the ignored `.env`
- MCP clients still need to connect to it explicitly; starting the server does
  not hot-register tools into an already-running Codex session

Important behavior:

- `n8n-mcp` helps with discovery, schema-aware authoring, and workflow
  management
- it does **not** register missing runtime nodes inside the `n8n` process
- if a node is absent from the active `n8n` runtime catalog, `n8n-mcp` will
  not make that workflow executable by itself

### n8n media notes

The local `n8n` image is built from [stack/prototype-local/n8n/Dockerfile](n8n/Dockerfile).
It copies static `ffmpeg` and `ffprobe` binaries into the official `n8n`
image. This is intentional: the current hardened `n8n` image in this stack does
not include `apk`, so `apk add --no-cache ffmpeg` is not a valid local fix.

The base `n8n` image is pinned through `N8N_BASE_IMAGE` in
`stack/prototype-local/.env`. The compose default is `n8nio/n8n:2.3.6`, and the
env value remains the operator-controlled place to freeze or advance the n8n
runtime.

### Langfuse tracing notes

Current Donna model-call tracing is emitted caller-side from the Hermes
runtime. It does not depend on OpenRouter observability forwarding, and the
first slice intentionally omits prompt/output capture.

Active Donna target:

- Operator URL: `https://donna.tailfedd3b.ts.net:8446/`
- In-stack URL: `http://127.0.0.1:3000`
- Project: `prototype-1215` / `1215 Continuity Plane`

For Paperclip `hermes_local` runs, the Paperclip run ID is passed through as
`PAPERCLIP_RUN_ID`, `HERMES_RUN_ID`, and `LANGFUSE_TRACE_ID`. This makes the
Paperclip run ID the Langfuse trace ID for deterministic correlation.

Filtering by run in the UI:

- Open `http://127.0.0.1:3000/project/prototype-1215/traces/<run_id>`
  to jump straight to the Hermes model-call trace for a specific Paperclip run.
- For API access, the trace endpoint is
  `GET /api/public/traces/<run_id>` and
  `GET /api/public/observations?traceId=<run_id>`.

Each OpenAI-compatible Hermes chat completion emits one Langfuse `GENERATION`
observation with conservative metadata: provider, model, base-url host,
streaming flag, status, latency, and error class when present.

If `LANGFUSE_HOST` / `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` are
absent from the Hermes runtime environment, Langfuse tracing silently no-ops
and model calls are unaffected.

### MinIO artifact notes

Buckets created automatically at startup:

- `artifacts`
- `langfuse`

Important behavior:

- Treat MinIO as the durable local artifact boundary for media workflows.
- Do not rely on container-internal output paths as the only artifact store.
- For `n8n`-local media generation, use `~/.n8n-files/prototype-media` as the
  scratch path. `n8n` 2.x blocks reads from its own files directory by default,
  so the compose stack explicitly disables that internal block for this local
  prototype.
- `N8N_RESTRICT_FILE_ACCESS_TO` uses semicolon-separated paths, not commas.
  The local stack uses `~/.n8n-files;/data/shared`.
- Reserve `/data/shared` for cross-container handoff with tools like ComfyUI or
  other media workers that should not depend on `n8n`'s private files area.
- `n8n` credential IDs are instance-local. Preserve credential names in repo
  artifacts and remap IDs at import time if a workflow references credentials.

### ComfyUI profile

The compose file currently defines `comfyui` under the `media` profile. For the
prototype done bar, the media path should be started and validated whenever the
local stack is being exercised as the shared-core prototype:

```bash
docker compose --env-file stack/prototype-local/.env \
  -f stack/prototype-local/docker-compose.substrate.yml \
  --profile media up -d comfyui
```

This keeps ComfyUI available as a first-class generator surface without making
the baseline substrate depend on a heavy GPU-oriented service.

ComfyUI model weights should live on the dedicated ComfyUI models volume, not
in MinIO as the primary runtime store. MinIO is the durable exchange layer for
generated artifacts, exports, and optional model distribution or backup.

Current local behavior:

- `prototype-local` boots ComfyUI with `--cpu` by default because this host
  does not expose an NVIDIA driver into Docker.
- That is good enough for API smoke tests and workflow wiring, but not for
  practical image generation throughput.
- When a GPU-backed host is available, remove the `--cpu` command flag or
  replace it with the appropriate device/runtime settings before treating
  ComfyUI as a production-grade generator surface.
- The ComfyUI workflows accept `comfyuiBaseUrl` in the webhook payload, so the
  generator can live on another machine such as an engineering workstation or
  remote GPU service without rewriting workflow JSON.
- Open WebUI image replies should use normal MinIO HTTP URLs instead of
  embedded `data:` payloads. That keeps chat responses small enough for the UI
  to render while preserving MinIO as the durable artifact store.
- The first SD1.5 workflow should stay small: queue a minimal prompt graph and
  return either a `promptId` or ComfyUI's checkpoint validation error. Do not
  assume a model is installed until `CheckpointLoaderSimple` exposes one.
- The next SD1.5 workflow can build on that queue path by polling
  `/history/{prompt_id}`, downloading `/view`, and uploading the finished image
  into MinIO under `prototype-comfyui/`.

## Recovery

### Open WebUI first-run admin bootstrap

If `http://127.0.0.1:8080/api/config` returns `"onboarding": true`, the first
successful `POST /api/v1/auths/signup` becomes the admin user and disables
signup afterwards.

Minimal bootstrap flow:

```bash
curl -X POST http://127.0.0.1:8080/api/v1/auths/signup \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "admin@example.local",
    "password": "replace-me",
    "name": "Admin",
    "profile_image_url": ""
  }'
```

### Open WebUI password recovery

Do not commit live passwords into the repo. Reset the local admin password in
SQLite, then sign in normally through the public API.

Generate a bcrypt hash:

```bash
python3 - <<'PY'
import bcrypt
print(bcrypt.hashpw(b'NewPassword123!', bcrypt.gensalt()).decode())
PY
```

Update the local Open WebUI auth row:

```bash
docker compose --env-file stack/prototype-local/.env \
  -f stack/prototype-local/docker-compose.substrate.yml \
  exec -T open-webui sh -lc "python - <<'PY'
import sqlite3
conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute(
    \"update auth set password=? where email=?\",
    ('<bcrypt-hash>', 'prototype-admin@example.local'),
)
conn.commit()
print(cur.rowcount)
PY"
```

Then sign in again:

```bash
curl -X POST http://127.0.0.1:8080/api/v1/auths/signin \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "prototype-admin@example.local",
    "password": "NewPassword123!"
  }'
```

### Open WebUI function import/update

Admin API endpoints used successfully against `v0.7.2`:

- `POST /api/v1/functions/create`
- `POST /api/v1/functions/id/{id}/update`
- `POST /api/v1/functions/id/{id}/toggle`
- `POST /api/v1/functions/id/{id}/valves/update`
- `GET /api/models`
- `POST /api/chat/completions`

The repo-owned sync path is:

- [stack/prototype-local/open-webui/functions/manifest.json](open-webui/functions/manifest.json)
- [stack/prototype-local/scripts/sync_openwebui_functions.py](scripts/sync_openwebui_functions.py)

Reference-node policy:

- create the first Open WebUI admin manually through the UI
- treat direct DB seeding as legacy helper behavior, not the default path

Important behavior:

- If `chat_id`, `session_id`, and `message_id` are present, Open WebUI may
  return a background task envelope instead of the final completion.
- For direct smoke tests, omit those fields and call `/api/chat/completions`
  synchronously.

### n8n recovery and import notes

Useful local runtime checks:

```bash
docker compose --env-file stack/prototype-local/.env \
  -f stack/prototype-local/docker-compose.substrate.yml ps

curl http://127.0.0.1:8090/healthz
curl -X POST http://127.0.0.1:5678/webhook/prototype-postgres-tables \
  -H 'Content-Type: application/json' \
  -d '{"chatInput":"show prototype tables","sessionId":"demo-session","messageId":"demo-message","userId":"demo-user"}'
curl http://127.0.0.1:5678/webhook/prototype-minio-buckets
```

Known gotchas already hit in this stack:

- The broker must use structured Postgres env vars, not a raw URL with an
  unescaped generated password embedded in it.
- `n8n` webhook method must match the node registration. The current prototype
  Open WebUI workflow is registered for `POST`, while the MinIO bucket smoke
  workflow is registered for `GET`.
- There is a known `n8n` API/webhook creation issue around webhook
  registration metadata. If a webhook workflow is created or mutated by API and
  does not register properly, confirm the webhook node includes a stable
  `webhookId` and that the runtime method matches the node configuration.
- The `n8n` CLI import commands require real file paths. They do not accept
  `--input=-`, so stdin-based imports fail with `ENOENT`.
- Reference-node policy is to create the first `n8n` owner manually, then
  generate the API key from inside the UI and place it into the ignored `.env`.
- The repo-owned legacy bootstrap path lives in:
  - [stack/prototype-local/n8n/credentials.manifest.json](n8n/credentials.manifest.json)
  - [stack/prototype-local/n8n/workflows.manifest.json](n8n/workflows.manifest.json)
  - [stack/prototype-local/scripts/bootstrap_n8n.py](scripts/bootstrap_n8n.py)
- Current repo-owned workflows do not require `n8n`'s Python task runner. The
  custom prototype image is intentionally limited to the static `ffmpeg` and
  `ffprobe` addition until a real Python-node requirement exists.

## Agent onboarding

When Paperclip or Hermes join the workflow layer, prefer these entry points
instead of ad hoc UI-only setup:

- Broker-facing continuity work: call the broker API on `:8090`
- Workflow automation and tool handoff: call the `n8n` webhook on `:5678`
- Human-facing agent shell: use Open WebUI on `:8080`
- Media generation: use ComfyUI on `:8188` when the `media` profile is enabled
- Durable media artifacts: use MinIO on `:9010`

Recommended onboarding pattern:

1. Keep reusable workflow logic in repo-owned `n8n` JSON under
   `stack/prototype-local/n8n/`.
2. Keep Open WebUI entry functions in repo-owned Python under
   `stack/prototype-local/open-webui/functions/`.
3. Treat Open WebUI `pipe` models as thin ingress adapters, not as the system
   of record.
4. Move durable state changes and cross-agent continuity events into the broker,
   even if the initial user hop goes through Open WebUI and `n8n`.
5. When a new workflow is meant for Hermes or Paperclip, give it a stable
   webhook path and document expected request/response fields next to the
   workflow file.

Current working example for onboarding:

- Open WebUI model id: `prototype_n8n_pipe`
- Open WebUI valve target: `http://n8n:5678/webhook/prototype-postgres-tables`
- Request field: `chatInput`
- Response behavior: summarize table list into a plain assistant reply and
  record continuity in the broker using the returned session/run/event IDs

## Notes

- The compose file uses prototype-safe defaults so it can be rendered without a
  hand-maintained `.env`.
- Do not reuse these defaults for a shared or public deployment.
- Do not commit live Open WebUI passwords, session tokens, or `n8n` API keys
  into the repo. Keep the recovery methods, not the secrets.
- The first continuity-plane artifact is repo-owned SQL under `stack/sql/broker/`.
