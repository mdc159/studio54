# audit/ — Three-way repo audit pipeline

Compares what the docs say about Studio54 against what the codebase says
against what the live VPS at 148.230.95.154 actually does. Spec:
`docs/superpowers/specs/2026-05-01-three-way-audit-design.md`.

## End-to-end run

    # 1. Manifest — list every .md file with owner tag
    uv run audit/manifest.py docs/audits/2026-05-01-three-way/scope.manifest.json

    # 2. Extract — fan out subagents, write draft claims to .audit-local/
    uv run audit/extract.py \
        --manifest docs/audits/2026-05-01-three-way/scope.manifest.json \
        --out .audit-local/claims.draft.yaml

    # 3. REVIEW GATE — human curates the draft, saves as:
    #    docs/audits/2026-05-01-three-way/claims.curated.yaml

    # 4. Dump — single SSH session captures full VPS state
    bash audit/dump_vps.sh .audit-local/vps-dump.full.json

    # 5. Redact — produce committable copy
    uv run audit/redact.py \
        --in .audit-local/vps-dump.full.json \
        --out docs/audits/2026-05-01-three-way/vps-dump.redacted.json

    # 6. Verify + report — produce ledger.csv and summary.md
    uv run audit/verify.py \
        --claims docs/audits/2026-05-01-three-way/claims.curated.yaml \
        --dump .audit-local/vps-dump.full.json \
        --out .audit-local/claims.verified.yaml
    uv run audit/report.py \
        --verified .audit-local/claims.verified.yaml \
        --out-dir docs/audits/2026-05-01-three-way/

## Tests

    uv run pytest audit/tests/
