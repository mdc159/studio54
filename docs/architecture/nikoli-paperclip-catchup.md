# Nikoli Paperclip Catch-up Assessment

> **Status:** read-only assessment for bringing Nikoli even with Victoria on the
> next operating layer: Paperclip company/bootstrap awareness. This is not a
> Paperclip autonomy grant, GPU authorization, or production-company launch.
>
> **Safety note:** this document intentionally omits IPs, secrets, raw `.env`
> values, invite material, raw logs, private key paths, and session databases.

## Purpose

Victoria is already the proven cloud-VPS communications persona in the
Donna/Studio54 grid. Nikoli has now reached the same transport/control tier via
Tailscale SSH, tmux, Hermes, and explicit `hermes-grid` live attach.

The next catch-up step is to make Mr. Tesla literate in the Paperclip layer:
what has already been proven with `hermes_local`, what is running on the
experimentation VPS, and what gates remain before Nikoli can safely run or
supervise a Paperclip engineering division.

## Current Equality Line

| Layer | Victoria | Nikoli / Nikolai | Current gap |
|---|---|---|---|
| Persona runtime | Existing Hermes runtime in tmux | Existing Hermes runtime in tmux | None at the transport/runtime layer |
| Studio54 topology | Enabled explicit attach | Enabled explicit attach | None for attach; both remain operator-driven |
| Direct control | Bounded one-line envelopes validated | Bounded one-line envelopes validated | None for basic sound-off |
| Evidence docs | Victoria evidence lives in AKE plus Studio54 grid docs | Nikoli node card lives in Studio54 | Nikoli needs a Paperclip/division catch-up doc |
| Productive role | Communications / operations liaison | WSL workstation / GPU-capable engineering persona | Nikoli needs an engineering/lab charter before autonomy |
| Paperclip company layer | Referenced as durable work plane | Not yet assigned a Paperclip company/division | Open design gate |

## What Studio54 Already Proves

The existing Studio54 documentation says the Paperclip direct-Hermes path is not
hypothetical:

- `docs/architecture/paperclip-hermes-local-contract.md` defines the direct
  Paperclip-to-Hermes contract.
- `docs/architecture/company-bootstrap.md` records the minimal company bootstrap
  path.
- `stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py` is the
  documented bootstrap entrypoint.
- The one-agent path is documented as proven.
- The manager/worker path is documented as proven.
- Per-company `HERMES_HOME` isolation is part of the contract.
- Honcho workspace/peer identity can be derived from the company/agent identity.
- A successful validation requires agent-authored issue completion evidence,
  heartbeat/run attribution, and issue state transition to `done`.

The important mental-model split remains:

```text
Outer/operator plane:
  Donna / Studio54 / hermes-grid / SSH / tmux / PRs / Linear

Inner company plane:
  Paperclip company / issues / agents / hermes_local / per-company HERMES_HOME
```

Live attach got Nikoli into the outer plane. The Paperclip catch-up work prepares
him for the inner company plane.

## Read-only Experimentation VPS Inventory

Donna performed a read-only reconnaissance pass against the known tailnet and
experimentation surfaces. Sensitive host coordinates are intentionally redacted.

### Tailnet reachability snapshot

| Node label | OS | Reachability | Notes |
|---|---|---|---|
| `paperclip` | Linux | online and SSH reachable with Donna key | Active experimentation host inspected read-only |
| `srv1264451` | Linux | online but Donna root SSH key rejected | Known VPS coordinate exists; do not mutate without access decision |
| `cbass-vps` | Linux | offline / SSH timeout during check | Appears inactive during this pass |
| `CBASS` | macOS | offline during check | Mac mini endpoint not online during this pass |
| `nikoli-wsl` | Linux | online | Nikoli WSL workstation already validated elsewhere |

### Active services observed on `paperclip`

Read-only SSH showed:

- Honcho stack containers up for local memory services:
  - `honcho-api-1`
  - `honcho-deriver-1`
  - `honcho-redis-1`
  - `honcho-database-1`
- Paperclip database container up:
  - `paperclip-db`
- Paperclip application plane running from `/opt/paperclip-pilot/paperclip`
  through `pnpm dev --bind lan` / server watch processes.
- Cursor remote server processes present, indicating the host has also been used
  interactively for experimentation.

No service was restarted, no container was exec-mutated beyond read-only SQL/API
inspection, and no secrets were printed.

### Paperclip database snapshot

The Paperclip database on `paperclip` contained:

| Table / entity | Observed count |
|---|---:|
| companies | 2 |
| agents | 8 |
| issues | 34 |
| issue comments | 36 |
| heartbeat runs | 67 |
| agent task sessions | 35 |

Companies observed by name:

- `Shizzle Site Studio`
- `Shizzle Solutions`

Agent adapter mix observed:

- `hermes_local`
- `codex_local`
- `claude_local`

Representative agent roles/titles observed:

- CEO using `hermes_local` adapter, currently error state.
- CTO using `codex_local` adapter, currently error state.
- Creative Director / Client Strategist using `hermes_local` adapter, idle.
- Frontend Marketing Engineer using `hermes_local` adapter, idle.
- Additional QA, design, engineering, and talent roles using local adapters.

Representative issue themes observed:

- company budget configuration;
- literature surveillance / survey workflows;
- evidence-package automation;
- operator verification and exception handling;
- roadmap and hiring decision-support summaries.

This confirms the sea-base host has real Paperclip company data and mixed local
adapter experimentation, not just an empty install.

## What We Learned From the Sea Base

1. **The experimentation host is useful evidence, not the canonical source.**
   It contains real Paperclip companies, agents, issues, comments, and run state,
   but Studio54 docs/scripts should remain the reusable pattern.
2. **`hermes_local` is present in live Paperclip agent records.**
   That lines up with Studio54's documented direct Hermes contract.
3. **The host is mixed-mode.**
   It has Honcho, Paperclip DB, Paperclip dev server, and Cursor experimentation.
   Treat it like a lab bench, not a clean production baseline.
4. **Some prior agents are in error state.**
   That is useful diagnostic evidence, but not something to repair inside this
   catch-up doc. Error recovery belongs in a separate bounded task.
5. **The bootstrap story should be replayed on a clean target before autonomy.**
   The sea base can teach us, but Nikoli's eventual engineering division should
   be bootstrapped from the documented script/contract with explicit validation.

## Documentation Gaps To Close

To get Nikoli even-Steven with Victoria, documentation should be squared away in
this order:

1. **Update grid/current-state docs** so they no longer imply Nikolai is disabled
   after PR #19.
2. **Keep Nikoli's node card internally consistent**: live attach is enabled for
   explicit operator commands, while Paperclip/company autonomy remains blocked.
3. **Add this catch-up assessment** as the bridge between Nikoli's node card and
   the Paperclip `hermes_local` company bootstrap docs.
4. **Create a future Nikoli Engineering Division Charter** before any autonomous
   company operation:
   - mission;
   - allowed repositories/tasks;
   - blocked operations;
   - GPU policy;
   - issue assignment rules;
   - report/sound-off schema;
   - Donna approval gates;
   - rollback/stop conditions.
5. **Create a future bootstrap replay plan** that runs the documented
   `bootstrap_paperclip_hermes_company.py` path on a chosen target and records a
   fresh validation issue.

## Recommended Next PR Sequence

### PR A — Documentation catch-up only

Scope:

- add this assessment;
- fix stale Nikoli status wording in node/grid docs;
- link the assessment from `README.md`;
- no runtime changes.

Validation:

```bash
git diff --check
./bin/hermes-grid --check
./bin/hermes-grid --check --probe-remote
./bin/hermes-grid attach Nikolai --dry-run
uv run --project stack/control pytest stack/control/tests -q
```

### PR B — Nikoli Engineering Division Charter

Scope:

- document Nikoli's engineering/lab operating contract;
- define what he may do independently, what requires Donna/Miguel approval, and
  what remains forbidden;
- include GPU and Paperclip boundaries;
- no company bootstrap yet.

### PR C — Paperclip Bootstrap Replay Plan

Scope:

- inspect the bootstrap script and current expected arguments;
- document a dry-run/replay procedure;
- choose one target and one validation issue;
- require explicit approval before creating or mutating a Paperclip company.

### PR D — Controlled bootstrap execution

Scope:

- run exactly one bootstrap replay;
- assign exactly one validation issue;
- require structured report-back to Donna;
- record sanitized evidence in Studio54 and the relevant ledger.

## Guardrails

- Do not copy `.env`, Hermes sessions, memory stores, SSH keys, or runtime DBs
  between Donna, Victoria, Nikoli, and Paperclip companies.
- Do not grant Nikoli Paperclip autonomy from live attach alone.
- Do not start GPU workloads from this workstream.
- Do not repair sea-base error-state agents unless Miguel approves a separate
  diagnostic task.
- Do not treat the lab host as production truth; extract lessons into Studio54.

## Current Recommendation

Proceed with PR A first. That gets the disco floor polished: Nikoli's docs match
his current validated access level, the sea-base experimentation evidence is
captured safely, and the next decision gate becomes crisp:

```text
Do we draft Nikoli's Engineering Division Charter next,
or do we first replay the Paperclip bootstrap path in a clean sandbox?
```
