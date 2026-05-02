# Three-way audit — 2026-05-01

One-time reality check comparing Studio54 docs, codebase, and the live VPS
at 148.230.95.154. Tooling lives in `/audit/`; design lives in
`/docs/superpowers/specs/2026-05-01-three-way-audit-design.md`.

Files in this directory:

- `scope.manifest.json` — every .md scanned, with owner tag
- `claims.curated.yaml` — claims after human review
- `ledger.csv` — final audit ledger, one row per claim
- `summary.md` — executive summary, top drifts, fix list
- `vps-dump.redacted.json` — frozen VPS snapshot (secrets redacted)

Read `summary.md` first.
