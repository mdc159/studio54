# Three-Way Repo Audit — Design Spec

- **Date:** 2026-05-01
- **Author:** Mike (mdc159) + Claude
- **Status:** Approved (brainstorm phase complete; ready for implementation plan)
- **Trigger:** One-time reality check. Suspect drift between docs, code, and the live VPS; want a single comprehensive report that surfaces gaps so they can be fixed.

---

## Goal

Produce a single, comprehensive, claim-driven audit that compares what the **documents** say about Studio54 against what the **codebase** says against what the **live VPS** at `148.230.95.154` actually does — and outputs a structured ledger plus a readable summary listing every drift with a suggested fix.

The audit is one-shot but the tooling it leaves behind is reusable for future re-runs.

---

## Decisions (made during brainstorm)

| # | Axis | Choice |
|---|---|---|
| 1 | Trigger | One-time reality check (not recurring, not a CI gate) |
| 2 | Scope strategy | Claim-driven: extract verifiable claims from docs, then verify each against code and VPS |
| 3 | Workflow | Two-stage with a human review gate between extraction and verification |
| 4 | Disagreement output | Neutral 3-column ledger (`doc_says / code_says / vps_says`) plus a non-binding `suggested_fix` column based on default hierarchy `vps > code > docs` |
| 5 | VPS access | One-time dump captured to a fact file; verification runs deterministically against the dump (no live SSH during verify) |
| 6 | Claim types | Concrete (strings, numbers, IDs, paths, ports, names, versions) **plus** behavioral (testable assertions about behavior). Architectural-role claims are out of scope. |
| 7 | Document scope | All `.md` files in the repo, with each tagged `owned` (root + `docs/` + `deploy/`) or `upstream` (`modules/*`) so upstream rows can be mass-pruned at the review gate. |
| 8 | Output artifact | Structured `ledger.csv` plus a thin `summary.md`. CSV chosen for sortability and diff-friendliness. |
| 9 | Secrets policy | Two artifacts: full dump kept local-only and gitignored, redacted dump committed alongside the ledger. Redaction is regex (`*_KEY|*_SECRET|*_TOKEN|*_PASSWORD|*_PASS|*_CREDENTIAL`) plus an explicit field allowlist/denylist for known sensitive fields. |

---

## Architecture

```
                        Stage 1                        REVIEW                Stage 2                     Output
┌──────────────┐    ┌──────────────┐               ┌───────────┐         ┌──────────────┐         ┌──────────────────┐
│ Repo .md     │───▶│  Extractor   │──claims.draft │   You     │──────▶  │   Verifier   │──────▶  │ ledger.csv       │
│ files (all)  │    │  (subagents  │   .yaml ─────▶│  (prune,  │         │ (3 sources)  │         │ summary.md       │
└──────────────┘    │  fan-out per │               │   add,    │         │              │         │ vps-dump.redacted│
                    │  doc)        │               │   tag)    │         │              │         │ (committed)      │
                    └──────────────┘               └───────────┘         └──────────────┘         └──────────────────┘
                                                                              ▲
                                                                              │
                                                                  ┌───────────┴────────────┐
                                                                  │   VPS dump (one shot)  │ ◀── ssh Studio54
                                                                  │   • full → local only  │
                                                                  │   • redacted → committed│
                                                                  └────────────────────────┘
```

### Components

1. **Extractor.** Driver script enumerates a scope manifest (every `.md` in the repo, owner-tagged) and dispatches one Sonnet subagent per file. Each subagent emits a YAML stream of claims. Concurrency capped at ~10. Output: `.audit-local/claims.draft.yaml`.
2. **Review gate.** Human reviews the draft, prunes false positives, retags, edits `expected_value` where extraction was wrong, adds missed claims. Output: `docs/audits/2026-05-01-three-way/claims.curated.yaml`.
3. **VPS dumper.** Single SSH session captures runtime state into `.audit-local/vps-dump.full.json` (mode 600, gitignored), then writes a redacted copy to `docs/audits/2026-05-01-three-way/vps-dump.redacted.json`.
4. **Verifier.** For each curated claim, runs three resolvers concurrently (doc, code, vps), records all three values, and classifies the row.
5. **Reporter.** Writes `ledger.csv` and `summary.md`.

### Key principle

The VPS dump is the audit's frozen-in-time view of reality. Verification is deterministic against the dump; re-running the report does not re-probe the VPS. The dump itself becomes part of the audit artifact.

---

## Stage 1 — Extract → review → curate

### Scope manifest

A JSON file listing every `.md` in the repo with an owner tag:

- **`owned`**: `README.md`, `STATE.md`, `AGENTS.md`, all of `docs/**`, all of `deploy/**`
- **`upstream`**: everything under `modules/**` (Honcho, n8n-mcp, paperclip, autoreason, hermes-agent, hermes-paperclip-adapter, local-ai-packaged, n8n-skills, hermes-agent-self-evolution)

Generated by a small `find . -name '*.md'` walk plus a path-prefix classifier.

### Extractor mechanics

The driver fans out one subagent per file. Subagent prompt is tight:

> Read this doc. Emit YAML — one entry per **concrete fact** (string, number, ID, path, port, container name, service name, version, command name, env var name, file existence) or **behavioral assertion** (X auto-creates Y on Z; running command W produces output V; service Q depends on R). Skip philosophy, motivation, rationale, and anything you'd have to infer. Cite line numbers exactly.

Concurrency cap: 10. Runs in the background while other work happens.

### Per-claim YAML schema

```yaml
- id: c-0042
  source_file: STATE.md
  source_line: 11
  owner: owned                        # owned | upstream
  claim_type: concrete                # concrete | behavioral
  subtype: container_count            # free-form tag (port, path, env_var, service_name, etc.)
  claim_text: "14 containers running, all healthy"
  expected_value: 14
  verifiable_by: [vps]                # subset of [doc, code, vps]
  probe: null                         # optional probe spec for behavioral claims
```

### Merge

Driver concatenates all YAML streams and dedupes by `(claim_text, expected_value)` with a `seen_in: [files...]` array so the same claim across multiple docs becomes one row.

### Review gate

The reviewer (Mike) reads `claims.draft.yaml` and either: prunes a row (`status: pruned`), retags `claim_type`, edits `expected_value` where extraction was wrong, or adds rows the extractor missed. Saves as `claims.curated.yaml`. **No verification runs until the reviewer signs off.**

---

## Stage 2 — Dump → verify → report

### VPS dump

Single SSH session driven by `audit/dump_vps.sh`. Captures, in one logical sweep, with `dump_started_at` and `dump_finished_at` timestamps:

- `docker ps -a --format '{{json .}}'` (full container inventory)
- `docker inspect` for each running container (image, ports, env, mounts, health)
- `systemctl --user list-units --state=running --no-pager`
- `ss -tlnp` (listening ports)
- File existence + `sha256sum` for key configs declared in docs (`stack/prototype-local/.env`, n8n credential dirs, etc.)
- Full content of `stack/prototype-local/.env` and any other env files referenced by claims
- `bin/1215 doctor`, `bin/1215 services`, `bin/1215 status` outputs (read-only subcommands only)
- `bin/1215 smoke` is opt-in via a flag (it is read-only on success but exercises the broker plane)
- HTTP reachability (status code only) of every URL the docs claim is up

Two outputs:

- **`.audit-local/vps-dump.full.json`** — full capture, mode 600, gitignored
- **`docs/audits/2026-05-01-three-way/vps-dump.redacted.json`** — committed, secrets replaced with `<REDACTED:keyname>` via regex (`*_KEY|*_SECRET|*_TOKEN|*_PASSWORD|*_PASS|*_CREDENTIAL`) plus an explicit field denylist for known sensitive fields (`N8N_OWNER`, OWU admin password, etc.). Reviewer eyeballs the redacted dump before it is committed.

### Verifier

For each curated claim, three resolvers run concurrently and emit a string (or `null` if not applicable):

- **doc resolver:** re-read `source_file:source_line ± 5`, confirm the claim still reads as extracted (catches extractor lossiness or doc edits during the audit)
- **code resolver:** type-dispatched. `port` → grep `*.yml *.yaml *.toml *.env *.py`; `path` → file existence check; `command` → grep `bin/`, `Makefile`, `package.json`; `env_var` → grep for the var name; `behavioral` → run the `probe` from the curated claim if present, else mark `UNVERIFIABLE_AGAINST_CODE`
- **vps resolver:** matches the claim against `vps-dump.full.json` by container name, port, file path, env key, command output, etc.

A small classifier per row computes `status`:

- All resolvers agree → `MATCH`
- Any resolver disagrees → `DRIFT`
- One or more resolvers can't probe → `UNVERIFIABLE` (sub-status `partial_match` if the probable sources do agree)
- Code/VPS confirms but doc was the source of an outdated value → `DRIFT_DOC_STALE`

### Suggested-fix column

Default hierarchy `vps > code > docs`: when DRIFT, the suggestion reads "update `<source_file>:<line>` to match `<vps_says>`". Reviewer overrides per-row during triage.

---

## Output artifacts and layout

```
docs/audits/2026-05-01-three-way/
├── README.md                       # index: what this is, how to read it
├── summary.md                      # executive: counts, top-10 drifts, fix list
├── claims.curated.yaml             # the curated ledger (input to verifier)
├── ledger.csv                      # final ledger, one row per claim, all columns
├── vps-dump.redacted.json          # frozen runtime snapshot (committed)
└── scope.manifest.json             # which .md files were scanned

audit/                              # tooling (committed, reusable)
├── extract.py                      # driver: subagent fan-out
├── dump_vps.sh                     # one-shot VPS capture
├── redact.py                       # full → redacted
├── verify.py                       # resolvers + classifier
└── report.py                       # ledger.csv + summary.md

.audit-local/                       # gitignored
├── claims.draft.yaml               # pre-review extractor output
└── vps-dump.full.json              # full dump, mode 600
```

`.audit-local/` is added to `.gitignore` as part of the implementation. The `audit/` directory is reusable: future audits drop a new dated folder under `docs/audits/` without touching the tooling.

### `ledger.csv` columns

`id, source_files, source_lines, owner, claim_type, subtype, claim_text, expected_value, doc_says, code_says, vps_says, status, suggested_fix, notes`

CSV chosen because it survives — sortable in any tool, diff-friendly across runs, paste-ready for spreadsheet triage.

### `summary.md` skeleton

```
# Three-way audit — 2026-05-01

- Scope: N owned docs, M upstream docs, K claims after curation
- VPS dump captured: <timestamp>
- Headline: X MATCH, Y DRIFT, Z UNVERIFIABLE

## Top drifts (sorted by impact)
1. STATE.md:11 says "14 containers running"; VPS shows 13.
2. ...

## Drift by source
- STATE.md: 4 drifts
- README.md: 2 drifts
- docs/architecture/canonical/current-contract.md: 1 drift

## Suggested fix list
... (one bullet per DRIFT row, grouped by file)
```

---

## Out of scope

- Auditing upstream module READMEs against their own upstream source repos. We extract their claims (because they appear in this repo) but do not verify whether `modules/honcho/README.md` matches the upstream Honcho project.
- Architectural-role claims ("Hermes is the tier-0 agent", "the broker is the continuity plane"). These are a separate audit.
- Behavioral claims without a probe specified. They are recorded with `status: UNVERIFIABLE` and a note suggesting how a future audit could verify them.
- Recurring schedule. The `audit/` tooling supports re-runs, but we are not automating one in this iteration.
- Re-bootstrapping the VPS to verify behavioral claims (e.g., "n8n owner is auto-created on first boot"). The dump records "owner exists: yes" rather than re-creating to verify.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Extractor hallucinates claims from prose | Review gate; subagent prompt explicitly forbids inferring; cite line numbers; reviewer can prune any row |
| Regex redaction misses a secret pattern | Allowlist + explicit field denylist on top of regex; reviewer eyeballs redacted dump before commit |
| VPS state changes mid-dump | Single SSH session, one logical capture, `dump_started_at` / `dump_finished_at` recorded; flag if delta exceeds threshold |
| Code resolver misses claims expressed in non-grep-friendly forms | Mark `UNVERIFIABLE_AGAINST_CODE` rather than fail silently; surface count in summary so reviewer can spot-check |
| Ledger too large to triage | Owner tag (`upstream`) lets reviewer mass-prune; status-based sort surfaces signal; default summary highlights top-10 drifts |
| `bin/1215 smoke` mutates state during the dump | Only read-only `1215` subcommands run by default; `smoke` is opt-in via a flag |
| Subagent fan-out token cost spikes | Concurrency cap of 10; per-subagent token cap; runs in background |

---

## Open questions deferred to implementation plan

1. **Subagent dispatch mechanism.** Use `archon-task-implementor`-style background spawns, raw `Task` calls, or a custom driver script? Implementation plan picks one.
2. **Probe spec format for behavioral claims.** YAML embedded in `claims.curated.yaml`, or a sidecar `probes/` directory? Implementation plan picks one.
3. **Exact denylist for redaction.** Generate from a first-pass scan of the full dump, then commit the denylist alongside the tooling.

---

## Success criteria

- `docs/audits/2026-05-01-three-way/ledger.csv` exists with one row per curated claim and all required columns populated.
- `docs/audits/2026-05-01-three-way/summary.md` lists every DRIFT row in the suggested fix list.
- `vps-dump.redacted.json` contains zero plaintext secret values (verified by a final regex sweep before commit).
- `.audit-local/` is gitignored and contains the full dump and draft claims.
- The `audit/` tooling can be re-run end-to-end against a fresh VPS dump and reproduce the audit deterministically (modulo VPS changes).
