# Reconstruction Plan

This is the implementation path from the current segmented repo state back to
a repeatable deployable VPS unit.

## Direction

Keep the active execution path direct Paperclip `hermes_local`. Do not make
Hermes gateway the Paperclip task path until it has first-class issue, comment,
result, and proof coverage.

## Sequence

1. **Reconcile source-of-truth docs**
   - Keep `current-state.md` factual and repo-grounded.
   - Use `deployable-unit.md` as the assembly map.
   - Banner older roadmap/Phase-H/gateway-first docs as historical where they
     conflict with the direct-path contract.

2. **Fix current operator drift**
   - Align `./bin/1215 status` service ports with compose.
   - Make the Paperclip instance config contract explicit in compose or in a
     checked projection step.
   - Remove stale CLI shim names and machine-local absolute links from
     operator-facing docs.

3. **Create a first-class VPS node manifest**
   - Add a committed VPS node directory parallel to `nodes/linux-prototype`.
   - Bind target, roles, expected loopback services, tailnet exposure, and
     proof expectations.
   - Keep secrets out of the manifest.

4. **Package fresh-node host bootstrap**
   - Wrap apt prerequisites, Docker enablement, UFW baseline, Tailscale
     prerequisite checks, root `.env` projection, and compose startup behind
     idempotent scripts.
   - Keep Tailscale auth and secret values operator-owned unless a later secret
     provisioning design replaces that.

5. **Package host-native services**
   - Make outer Hermes, Honcho user units, and any Paperclip bridge setup
     rerunnable.
   - Verify Honcho uses the generated environment and shared substrate
     Postgres.
   - Keep outer Hermes state separate from Paperclip company homes.

6. **Wire company bootstrap into proof**
   - Run `./bin/1215 company bootstrap` from a known manager/worker template
     after the node is up.
   - Integrate `paperclip-coordination-proof.py` into live/staging node proof
     mode.
   - Require proof of final issue status, run attribution, no runtime-noise
     comments, and bounded child issue creation.

7. **Create a versioned deploy bundle**
   - Bundle compose files, systemd units, deploy scripts, node manifest,
     schemas, and verifier commands into a versioned release artifact.
   - The bundle is accepted only when a clean Ubuntu VM can run the installer,
     create a company, complete a manager/worker proof, and emit a passing
     `proof.json`.

## Acceptance Gates

- Simulation proof remains passing in CI.
- Local repo validation remains passing.
- A staging/live proof can show Paperclip -> Hermes -> Honcho -> Langfuse
  traceability for the direct `hermes_local` path.
- A clean-node runbook step has a corresponding idempotent script or is
  explicitly documented as operator-owned.
- No documentation claims the one-command installer exists before it does.
