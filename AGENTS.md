# Repository Guidelines

## Project Structure & Module Organization
`1215-vps` is a prototype-first VPS stack. Start with `docs/architecture/` for the source-of-truth design and execution order. Runtime code lives under `stack/`: `stack/control/` contains the repo-owned CLI (`start-1215` via `./bin/1215`), `stack/broker/` contains the FastAPI broker service, and `stack/prototype-local/` holds the current Docker Compose bring-up target and helper scripts. Keep new tests beside each package in `tests/`. Treat `modules/` as upstream references and avoid ad hoc edits there unless the task explicitly targets a submodule.

## Build, Test, and Development Commands
Use `uv`; do not use `pip install`.

- `uv sync --project stack/control` installs the control CLI environment.
- `uv run --project stack/control start-1215 doctor` checks local prerequisites and repo layout.
- `./bin/1215 up --target prototype-local` starts the current local stack.
- `./bin/1215 status` reports service health and drift.
- `uv run --project stack/control pytest`
- `uv run --project stack/broker pytest`
- `docker compose -f stack/prototype-local/docker-compose.substrate.yml config` validates compose changes before commit.

## Coding Style & Naming Conventions
Target Python 3.12+. Follow the existing style: 4-space indentation, type hints on public functions, standard-library imports first, and small focused modules. Use `snake_case` for Python files, functions, and tests; reserve `PascalCase` for classes only. Match the existing CLI and manifest naming patterns such as `test_cli.py`, `docker-compose.role.yml`, and `roles.env.example`. No repo-wide formatter is configured, so keep edits consistent with surrounding code and avoid unrelated reflow.

## Testing Guidelines
Pytest is the active test framework across `stack/control/`, `stack/broker/`, and `stack/services/hermes-gateway/`. Name tests `test_*.py` and prefer behavior-focused test names keyed to a command, endpoint, or lifecycle path. Add or update tests with every code change in those packages. Run the narrow project test suite first, then any relevant stack smoke path such as `./bin/1215 smoke` for lifecycle changes.

## Commit & Pull Request Guidelines
Recent history uses short, scoped subjects like `proto: ...`, `docs: ...`, and `fix: ...`; keep that pattern and write imperative summaries. PRs should explain the affected stack area, list validation commands run, and link the relevant architecture doc or issue. Include logs or screenshots only when changing operator-facing output or UI surfaces.

## Security & Configuration Tips
Do not commit live `.env` files, secrets, or machine-specific state. Use the example env files under `nodes/` and `stack/` as templates, and prefer `./bin/1215` or checked-in scripts over one-off manual commands.
