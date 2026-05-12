# Studio54 local-ai bootstrap

This directory is the simplified bring-up path modeled after `modules/local-ai-packaged`:

- one operator env: repo-root `.env`
- one compose file: `stack/local-ai/docker-compose.yml`
- one launcher: `python3 stack/local-ai/start_studio54.py`
- host-side Hermes, seeded from the same `.env`
- containerized Honcho, Broker, and Paperclip

Supabase is deliberately not in the first-boot path. The shared Postgres/pgvector
container is enough for Honcho and Broker right now, and this keeps the initial
stack light. Add Supabase later only if an app requires its auth/storage APIs.

## First boot

```bash
cp stack/local-ai/.env.example .env
$EDITOR .env   # set OPENROUTER_API_KEY at minimum
python3 stack/local-ai/start_studio54.py --profile none
```

Optional UI surface:

```bash
python3 stack/local-ai/start_studio54.py --profile ui
```

The script will:

1. preserve/generate local secrets in `.env`
2. start Docker Compose under project name `studio54`
3. wait for Honcho and Paperclip health checks
4. install Hermes on the host if `hermes` is not on PATH
5. project `.env` into Hermes config/env files
6. write `honcho.json` for Hermes memory isolation
7. run a tiny Hermes OpenRouter smoke unless `--skip-hermes-smoke` is set

## Core services

| Service | URL / port | Purpose |
| --- | --- | --- |
| Postgres + pgvector | `127.0.0.1:5433` | Shared DB substrate |
| Honcho API | `http://127.0.0.1:18000` | Agent memory API |
| Honcho deriver | internal | Background memory formation |
| Broker | `http://127.0.0.1:8090` | Studio54 event/control broker |
| Paperclip | `http://127.0.0.1:3100` | AI-company control plane |
| Open WebUI | `http://127.0.0.1:8080` with `--profile ui` | Optional chat UI |

## Stop

```bash
python3 stack/local-ai/start_studio54.py --down
```

or directly:

```bash
docker compose -p studio54 --env-file .env -f stack/local-ai/docker-compose.yml down
```

## Deferred OAuth

OpenAI Codex OAuth is intentionally deferred. Once the stack is up, run the
manual flow from the host:

```bash
hermes login --provider openai-codex
```
