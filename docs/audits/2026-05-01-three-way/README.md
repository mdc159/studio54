# Three-way audit — 2026-05-01

One-time reality check comparing Studio54 docs, codebase, and the live VPS
at 148.230.95.154.

This directory is the frozen Studio54 audit result. The reusable audit tooling
has moved out of this repo into the standalone audit project, so these files
should be read as historical evidence rather than as an in-repo rerun workflow.

Files in this directory:

- `scope.manifest.json` — every .md scanned, with owner tag
- `claims.curated.yaml` — claims after human review
- `ledger.csv` — final audit ledger, one row per claim
- `summary.md` — executive summary, top drifts, fix list
- `vps-dump.redacted.json` — frozen VPS snapshot (secrets redacted)

Read `summary.md` first.
