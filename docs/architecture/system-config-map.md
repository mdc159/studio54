# System Config Map

Operator map for the Donna / Studio54 reference node.

This document defines the configuration surfaces that matter for operating and
rebuilding the system. The goal is not to force every setting into one file.
The goal is to make one canonical control path obvious:

1. one canonical operator env
2. a small set of explicitly referenced non-env config surfaces
3. no mystery state mistaken for config

Related documents:

- Live runtime inventory: [donna-vps-service-map.md](donna-vps-service-map.md)
- Reference target: [reference-node-target.md](reference-node-target.md)
- Hermes runtime: [hermes-runtime.md](hermes-runtime.md)
- Hermes bootstrap: [hermes-bootstrap.md](hermes-bootstrap.md)
- Operator init flow: [operator-init-flow.md](operator-init-flow.md)

## Primary Operator Contract

The canonical operator env in the repo is now:

- `.env.example` at the repo root

Current runtime projection:

- `/opt/1215-vps/stack/prototype-local/.env` on the live VPS
- `stack/prototype-local/.env.example` as the stack-specific template

This means:

- the root `.env` contract is the first file the operator should inspect
- the stack-local `.env` remains the currently consumed compose file until the
  unified launcher/bootstrap path exists

It should remain the main home for:

- site-specific secrets
- service toggles
- bind and URL values that are expected to vary per site
- placeholders for manual-init values such as `N8N_API_KEY`
- Paperclip runtime knobs that already behave well as env vars
- pointers to Hermes and other non-env config surfaces

## Referenced Config Surfaces

Some required configuration does not belong in the canonical app-plane env.
Those surfaces should be treated as explicit references, not hidden exceptions.

### Hermes

Hermes is host-native and therefore has its own control-plane config surfaces:

- `/root/.hermes/.env`
- `/root/.hermes/config.yaml`
- `/root/.hermes/SOUL.md`
- `/root/.hermes/honcho.json`
- `/etc/systemd/system/hermes-dashboard.service`

These files belong to the Hermes control plane, not the Compose app plane.

Observed live role split on Donna:

- `/root/.hermes/.env`
  - provider and tool secrets
  - terminal runtime overrides
  - optional backend credentials
- `/root/.hermes/config.yaml`
  - Hermes runtime behavior
  - default model/provider selection
  - terminal backend defaults
  - browser, display, checkpoint, and auxiliary-provider behavior
- `/root/.hermes/SOUL.md`
  - Hermes persona and interaction style
  - prompt-layer identity, not infrastructure
- `/root/.hermes/honcho.json`
  - Honcho peer/memory integration settings
  - workspace, peer naming, cadence, and Honcho API key
- `/etc/systemd/system/hermes-dashboard.service`
  - dashboard bind host and port
  - service user
  - restart/logging policy
  - private network contract

Practical ownership rule:

- if a setting changes Hermes runtime behavior, check `config.yaml`
- if a setting is a Hermes secret or provider credential, check `.env`
- if a setting changes Hermes identity, check `SOUL.md`
- if a setting changes Hermes memory/peer topology, check `honcho.json`
- if a setting changes dashboard exposure, check the systemd unit

### Paperclip

Paperclip is mostly env-driven, but one referenced config file still matters:

- `/paperclip/instances/default/config.json`

Paperclip also consumes env from the main stack `.env` and runtime container
env, so this file should be treated as a secondary surface, not the primary
operator contract.

Tracked template for the current reference node:

- `stack/prototype-local/paperclip.instance.config.json.example`

Current Donna rule:

- `PAPERCLIP_CONFIG` should point at a real file on disk
- the reference node should not rely on Paperclip's implicit missing-file
  fallback for this path

## Runtime State, Not Config

These paths are important operationally, but they are not primary config and
should not be treated as the source of truth for rebuilds.

### Hermes runtime/state

- `/root/.hermes/state.db*`
- `/root/.hermes/sessions/`
- `/root/.hermes/memories/`
- `/root/.hermes/logs/`
- `/root/.hermes/audio_cache/`
- `/root/.hermes/image_cache/`
- `/root/.hermes/checkpoints/`
- `/root/.hermes/hermes-agent/`

### Paperclip/runtime data

- Paperclip instance and generated state under `/paperclip`
- Compose volumes such as `prototype_paperclip_data`

### Other Compose state

- Docker volumes for Postgres, MinIO, Neo4j, Qdrant, Langfuse, Open WebUI,
  n8n, and other compose-managed services

These must be backed up or recreated appropriately, but they are not the place
to discover intended system configuration.

## Live Port Map

Observed on Donna on 2026-04-22.

### Public listeners

- SSH: `0.0.0.0:22`

### Direct tailnet listener

- Hermes dashboard: `100.87.24.49:9119`

### Tailscale Serve ports

- `8443 -> http://127.0.0.1:3100` Paperclip
- `8444 -> http://127.0.0.1:8080` Open WebUI
- `8445 -> http://127.0.0.1:5678` n8n
- `8446 -> http://127.0.0.1:3000` Langfuse
- `8447 -> http://127.0.0.1:13000` n8n-mcp
- `8448 -> http://127.0.0.1:7474` Neo4j
- `8449 -> http://127.0.0.1:6333` Qdrant
- `8450 -> http://127.0.0.1:9011` MinIO Console
- `8451 -> http://127.0.0.1:9010` MinIO S3 API
- `8452 -> http://127.0.0.1:8188` ComfyUI

### Loopback-only app plane listeners

- `127.0.0.1:3000` Langfuse web
- `127.0.0.1:3030` Langfuse worker health
- `127.0.0.1:3100` Paperclip app
- `127.0.0.1:5433` Postgres
- `127.0.0.1:5678` n8n
- `127.0.0.1:6333` Qdrant HTTP
- `127.0.0.1:6334` Qdrant gRPC
- `127.0.0.1:6379` Valkey
- `127.0.0.1:7473` Neo4j HTTPS
- `127.0.0.1:7474` Neo4j HTTP
- `127.0.0.1:7687` Neo4j Bolt
- `127.0.0.1:8080` Open WebUI
- `127.0.0.1:8090` Broker
- `127.0.0.1:8123` ClickHouse HTTP
- `127.0.0.1:8188` ComfyUI
- `127.0.0.1:9000` ClickHouse native
- `127.0.0.1:9009` ClickHouse interserver
- `127.0.0.1:9010` MinIO S3 API
- `127.0.0.1:9011` MinIO Console
- `127.0.0.1:13000` n8n-mcp

## Intended Usage

The future single root system env should either contain these values directly
or point to where they are owned.

For example:

- Hermes home path
- Hermes unit path
- Hermes dashboard bind host and port
- Paperclip instance config path
- Tailscale Serve published ports
- app-plane local listener ports
- manual-init placeholders such as `N8N_API_KEY`

If a setting cannot live in the canonical env, the canonical env or its
companion docs should point to the exact file that owns it.

For Hermes specifically, the canonical system env should act as a pointer map,
not a forced replacement for all of `/root/.hermes`. A good target contract is:

- canonical env points to Hermes home, dashboard unit, and expected bind port
- Hermes `.env` continues to own Hermes-specific provider secrets
- Hermes `config.yaml` continues to own Hermes runtime behavior
- `SOUL.md` and `honcho.json` remain explicit secondary config surfaces

## Practical Rule

When operating or rebuilding the system:

1. check the repo-root canonical `.env` first
2. project the consumed app-plane values into `stack/prototype-local/.env`
3. then check this document for the referenced non-env surfaces
4. do not infer intended config from runtime state unless a documented surface
   is missing
