Yes. The right path is not “let one smarter agent run longer.” It is to put the repo into a verifier-first workflow where agents can implement, but cannot define success by prose.

My recommendation is:

Use GitHub as the control surface, GitHub Actions as the first verifier, Codespaces or Cloud Codex as disposable implementer workbenches, and a separate clean Ubuntu VM/VPS snapshot as the real deployment verifier. Do not use Cloud Codex alone as the trust boundary. Treat Codex as a branch worker.

I cannot verify the current Cloud Codex product setup details because live web access is disabled here, but the plan below does not depend on product-specific features. It works with local Codex, Cloud Codex, Codespaces, or any agent that can edit a branch and run commands.

The repo already points in this direction. Studio54 is explicitly intended to be a repeatable private AI node built around Paperclip, Hermes, `hermes_local`, Langfuse, Open WebUI, n8n, ComfyUI, and the substrate services. It also says the repo owns the bootstrap contract, not just a pile of upstream tools.  The current install runbook already defines the fresh-node bring-up path and the direct `hermes_local` completion contract.  The cloud-agent document now captures the same lesson you learned manually: GitHub issue/PR as source of truth, Codespace as disposable workbench, GitHub Actions as repeatable verifier, and JSON/log artifacts as evidence. 

The roadmap is below.

Phase 0: Stop the bleeding and re-establish source of truth.

Goal: make `main` and the live node agree enough that future work is not built on hidden drift.

Your session log shows the agent eventually committed and pushed only the template-backed bootstrap work to `main`, while preserving unrelated dirty changes in files such as `.env.example`, `modules/hermes-paperclip-adapter/src/server/execute.ts`, and Paperclip test files. It also reports that unrelated pre-existing drift was preserved and not included.  That is useful discipline, but it leaves a risk: the live VPS may contain SCP’d runtime fixes that are not represented in the repo.

First action: create a cleanup branch from current `main`.

```bash
git fetch origin
git checkout main
git pull --ff-only
git status --short
git checkout -b chore/source-of-truth-reconcile
```

Then ask your Codex agent to do only this:

1. Compare the repo against the known live fixes from the session: comment sanitization, parent wake on child `blocked`, and stranded-parent-with-open-children recovery guard.
2. Determine whether those fixes are committed on `main`.
3. If not committed, create a narrow PR that adds only those fixes and their tests.
4. Do not touch the live VPS.
5. Do not broaden into gateway work, swarm work, generalized bootstrap, or per-agent memory homes.

Acceptance for Phase 0:

```bash
bash scripts/doctor-agent-env.sh
bash scripts/validate-repo.sh
bash scripts/simulate-vps-bootstrap.sh
python3 scripts/agent-evidence-guard.py --base-ref origin/main
git status --short
```

The final `git status` should be clean except intentional branch changes. The PR should contain proof logs, not just a summary.

Also fix stale documentation here. The README still describes PR #5 as pending, but GitHub shows PR #5 was merged on May 3, 2026.   That is small, but it matters because agent systems amplify doc drift.

Phase 1: Enforce branch-and-PR discipline.

Goal: no more agent direct-pushes to `main`.

Set branch protection on `main`:

Require pull request before merge.

Require status checks.

Require conversation resolution.

Disable force pushes.

Prefer linear history.

Require at least one human/operator review for protected paths.

Protected paths should include:

```text
.github/workflows/**
scripts/agent-evidence-guard.py
scripts/validate-repo.sh
scripts/simulate-vps-bootstrap.sh
scripts/verify-*.py
scripts/proof/**
schemas/**
deploy/vps/**
stack/prototype-local/scripts/**
modules/hermes-paperclip-adapter/**
modules/paperclip/server/src/services/heartbeat.ts
modules/paperclip/server/src/routes/issues.ts
```

Add a `CODEOWNERS` file even if you are the only owner for now:

```text
.github/workflows/                  @mdc159
scripts/agent-evidence-guard.py     @mdc159
scripts/validate-repo.sh            @mdc159
scripts/simulate-vps-bootstrap.sh   @mdc159
scripts/proof/                      @mdc159
schemas/                            @mdc159
deploy/vps/                         @mdc159
```

This is not bureaucracy. It prevents the agent from silently changing the judge.

Phase 2: Use the existing cloud-agent primitive as the default development loop.

The repo already has the right first primitive: `doctor-agent-env.sh`, `validate-repo.sh`, `simulate-vps-bootstrap.sh`, and `agent-evidence-guard.py`. The cloud-agent doc says the operating rule is that a PR is not ready for real VPS testing until Studio54 validation passes, VPS bootstrap simulation passes, the simulation report is attached as an Actions artifact, and you explicitly approve moving from simulation to staging/live infra. 

From now on, every Codex/local-agent task should follow this loop:

```text
GitHub issue
  -> branch
  -> narrow code/doc change
  -> local validation
  -> PR
  -> GitHub Actions validation
  -> artifact review
  -> optional staging VM proof
  -> merge
  -> optional live node promotion
```

Agent role:

Codex/local agent is the implementer.

GitHub Actions is the first verifier.

A clean VM/VPS snapshot is the deployment verifier.

You remain the live-infra approval gate.

Do not let the implementer mutate the active VPS as part of normal development. The session log shows SCP-to-live worked, but that should now be treated as emergency/prototype behavior, not the standard path. 

Phase 3: Turn the install runbook into an evidence-producing proof harness.

Goal: move from “runbook worked” to “this commit produced this machine-readable proof.”

The current VPS install runbook is a good human procedure. It starts from Ubuntu 24.04, installs prerequisites, projects runtime files from root `.env`, starts Compose, installs Tailscale, installs outer Hermes, installs Honcho, bootstraps a one-agent `hermes_local` company, and verifies Paperclip/Hermes completion through the final PATCH contract. 

Do not immediately rewrite everything into a giant installer. First add a proof harness around the existing steps.

Add:

```text
scripts/proof/collect-node-proof.py
scripts/proof/verify-node-proof.py
scripts/proof/poll-paperclip-proof.py
scripts/proof/memory-canary-proof.py
schemas/proof/node-proof.schema.json
docs/proofs/node-proof-contract.md
```

The proof bundle should land under:

```text
.artifacts/node-proof/<timestamp>/
  proof.json
  compose-config.txt
  docker-ps.json
  health.json
  paperclip-issues.json
  paperclip-runs.json
  paperclip-comments.json
  exposure-scan.json
  memory-canaries.json
  redacted-env-fingerprints.json
  logs/
```

The minimum `proof.json` should include:

```json
{
  "schemaVersion": "studio54.node-proof.v1",
  "git": {
    "repo": "mdc159/studio54",
    "sha": "...",
    "branch": "..."
  },
  "target": {
    "os": "ubuntu-24.04",
    "hostname": "...",
    "ephemeral": true
  },
  "environment": {
    "rootEnvHash": "...",
    "stackEnvHash": "...",
    "secretsRedacted": true
  },
  "compose": {
    "configRendered": true,
    "nonLoopbackBinds": []
  },
  "services": {
    "paperclip": "ok",
    "langfuse": "ok",
    "n8n": "operator_required_or_ok",
    "openWebui": "operator_required_or_ok",
    "honcho": "ok"
  },
  "paperclip": {
    "companyId": "...",
    "managerAgentId": "...",
    "workerAgentIds": ["..."],
    "oneAgentProof": "pass",
    "managerWorkerProof": "pass"
  },
  "hermes": {
    "activePath": "direct_hermes_local",
    "companyScopedHomes": true,
    "perAgentHomes": false
  },
  "memory": {
    "companyIsolation": "pass",
    "agentIsolation": "not_implemented",
    "outerHermesIsolation": "pass"
  },
  "traceability": {
    "paperclipRunId": "...",
    "hermesRunId": "...",
    "langfuseTraceId": "..."
  },
  "result": "pass"
}
```

Acceptance:

```bash
python3 scripts/proof/collect-node-proof.py --out .artifacts/node-proof/latest
python3 scripts/proof/verify-node-proof.py .artifacts/node-proof/latest/proof.json
```

The verifier must fail closed. Missing proof is failure. “Agent says it worked” is failure.

Phase 4: Split CI into three lanes.

Lane A: Fast repo validation.

Runs on every PR.

Scope:

```bash
bash scripts/validate-repo.sh
bash scripts/simulate-vps-bootstrap.sh
python3 scripts/agent-evidence-guard.py --base-ref origin/main
```

This already exists conceptually in the repo’s cloud-agent setup. 

Lane B: Staging node proof.

Runs manually through `workflow_dispatch` or on a protected branch, not on every PR.

Target: a disposable Ubuntu 24.04 VM or VPS snapshot.

This should eventually run:

```bash
./bin/1215 doctor --json
./bin/1215 up --json
./bin/1215 smoke --json
python3 scripts/proof/collect-node-proof.py --out .artifacts/node-proof/latest
python3 scripts/proof/verify-node-proof.py .artifacts/node-proof/latest/proof.json
```

At first, `./bin/1215` may not exist or may not cover everything. That is fine. Wrap the current runbook steps. The install runbook itself says one open question is which parts should become one idempotent bootstrap command. 

Lane C: Live node promotion.

Manual only.

No automatic live mutation from PRs.

The live workflow should require:

1. PR merged.
2. Fast CI green.
3. Staging node proof green.
4. Human approval.
5. Backup/snapshot.
6. Apply to live.
7. Run read-only proof.
8. Save proof bundle.

Phase 5: Use Codespaces or Cloud Codex only as workbenches.

Codespaces is suitable for:

repo edits,

tests,

simulation,

proof-script development,

documentation updates,

reviewing PRs,

running Docker Compose config checks if available.

Codespaces is not the right full validator for:

systemd user services,

Tailscale login/Serve behavior,

host-network Paperclip behavior,

fresh VPS firewall posture,

live runtime ownership,

real Docker volume permission behavior,

host-native Hermes/Honcho behavior.

Cloud Codex should be treated the same way: useful implementer, not trusted verifier.

Local VM snapshot is probably your best next full-fidelity test target. You already have a local machine with Ubuntu in a VM and a clean snapshot. Use that before automating cloud VPS creation. It gives you the exact thing you were doing manually, but with rollback instead of rebuild.

Recommended environment progression:

```text
Now:
  local Codex or Cloud Codex edits branch
  GitHub Actions validates repo and simulation
  local VM snapshot validates fresh-node proof

Next:
  self-hosted GitHub Actions runner attached to a staging VM
  workflow_dispatch runs full proof and uploads artifact

Later:
  ephemeral cloud VPS provisioning through Terraform/Packer/Ansible
  automatic destroy/recreate after each proof
```

Do not start with Terraform unless you want to spend your energy on cloud plumbing. Your immediate bottleneck is verifier discipline, not infrastructure provisioning.

Phase 6: Formalize the implementer/executor/verifier roles.

Use this division:

Planner: creates the issue and acceptance criteria.

Implementer: Codex/local agent edits the branch.

Static verifier: GitHub Actions runs repo validation and simulation.

Deployment executor: clean VM or staging runner applies the branch to a fresh Ubuntu target.

Proof verifier: script validates `proof.json` and artifacts.

Human operator: approves live mutation.

The implementer may not decide success.

The executor may not edit the repo.

The verifier may not infer success from prose.

The human may override, but the override should be explicit and documented.

This matches the useful part of your manual two-agent relay. You were preventing hallucinated success by keeping yourself in the middle. The new version keeps you at the approval gate but moves the mechanical checking into scripts and artifacts.

Phase 7: Clarify active architecture before expanding it.

The repo currently has two competing pressures:

The current active path is direct per-company `hermes_local`. The README and install runbook state this clearly.  

The older roadmap still contains a gateway-heavy Phase D/E/H path. 

The current-state doc also says the host-only Hermes gateway is not implemented, no directory or daemon exists for it, and the vps-hub compose implementation is declarative rather than runnable. 

Decision: defer gateway work.

The direct `hermes_local` path is the active spine. Finish proving that first. Gateway may still be the right future boundary, but it is not the next thing to build. Building gateway now would add a second unproven execution path while the first one is not yet fully gated.

Active contract for the next few phases:

```text
Paperclip execution path: direct hermes_local
Runtime boundary: company-scoped HERMES_HOME
Gateway path: future/deferred
Per-agent memory homes: future work
Outer Hermes: separate from Paperclip-internal Hermes
Langfuse: downstream observability, not source of truth
Paperclip: company/issue/run source of truth
```

Do not claim per-agent memory isolation until it exists.

The install runbook explicitly says manager and worker currently share company-scoped `HERMES_HOME`, and per-agent homes are not implemented yet.  That means manager/worker coordination proofs are valid lifecycle proofs, not memory isolation proofs.

Phase 8: Add memory canary gates.

Goal: make memory leakage observable.

Start with the memory boundary you actually have: company-level isolation.

Add simulation tests first:

Company A fake memory canary must not appear in Company B.

Company B fake memory canary must not appear in Company A.

Outer Hermes fake memory canary must not appear in Paperclip company Hermes.

Paperclip company fake memory canary must not appear in outer Hermes.

Honcho `workspace` must equal `companyId`.

Honcho `aiPeer` must equal `paperclip-agent-<agentId>`.

The cloud-agent simulation already verifies separate company homes, `honcho.json.workspace == companyId`, and `honcho.json.aiPeer == paperclip-agent-<agentId>`.  Extend that into explicit canary tests.

Then add live/staging tests:

Create Company A and Company B.

Write canary A into A’s accessible memory path.

Ask B to retrieve it.

Expected: failure.

Write shared company canary inside one company.

Ask manager and worker in the same company to retrieve it.

Expected under current design: visible, unless you later implement per-agent homes.

After per-agent homes exist, change expected behavior.

This is the important distinction:

```text
Current:
  company isolation should pass
  per-agent isolation should be marked not_implemented

Future:
  company isolation should pass
  per-agent isolation should pass
  explicit shared company memory should pass only through intentional channel
```

Phase 9: Convert bounded live proofs into reusable scripts.

The session log contains useful one-off pollers: checking parent, children, runs, comments, noise strings, delayed final state, and no runaway task spawning.  Do not leave that as transcript material.

Promote it into scripts:

```text
scripts/proof/paperclip_create_parent.py
scripts/proof/paperclip_poll_tree.py
scripts/proof/paperclip_verify_coordination.py
scripts/proof/paperclip_scan_comments.py
scripts/proof/paperclip_verify_attribution.py
```

Add a single command:

```bash
python3 scripts/proof/run-paperclip-coordination-proof.py \
  --company-id "$COMPANY_ID" \
  --manager-agent-id "$MANAGER_ID" \
  --worker-agent-id "$WORKER_A_ID" \
  --worker-agent-id "$WORKER_B_ID" \
  --out .artifacts/node-proof/latest/paperclip-coordination.json
```

Acceptance:

The proof must verify:

exactly two children were created,

each child has the expected `parentId`,

each child is assigned to the expected worker,

worker comments have correct `authorAgentId`,

worker comments have correct `createdByRunId`,

runtime diagnostics do not appear in ordinary issue comments,

parent is not closed before children finish,

parent wakes on child `done` or `blocked`,

parent does not wake from incidental runtime-noise comments,

no runaway child creation occurs after a quiet delay.

This turns your agent’s good manual behavior into a repeatable gate.

Phase 10: Build the operator command last, not first.

The existing repo roadmap has a Phase H for unified launch script.  That is still the right eventual user experience, but do not start by building a perfect `1215 up`.

First wrap the current runbook with proof scripts.

Then create:

```bash
./bin/1215 doctor --json
./bin/1215 env project --json
./bin/1215 stack up --json
./bin/1215 stack status --json
./bin/1215 company bootstrap --template-file ...
./bin/1215 proof node --json
./bin/1215 smoke --json
```

Only after those commands are individually stable should you collapse them into:

```bash
./bin/1215 up --target fresh-node --json
```

Acceptance for the unified command:

Run it twice on the same machine and the second run is a no-op.

Run it on a fresh snapshot and it reaches the same proof result.

Run it on a half-configured machine and it reports exactly what is missing.

Run it without secrets and it fails without printing secrets.

Run it with operator-only steps missing, such as first-owner setup, and it reports `operator_required` rather than pretending success.

Phase 11: Decide when to use the live VPS.

Use this rule:

Simulation green means the branch is eligible for staging.

Staging proof green means the branch is eligible for live.

Live proof green means the change is operationally accepted.

Do not use the live VPS as the first integration environment anymore. The session log shows the agent deployed to the active test node, rebuilt Paperclip, discovered a startup race, then continued.  That was acceptable during discovery. It should now become a controlled staging proof, not normal development.

Your local VM snapshot is the next best tool. Use it as `studio54-stage-local`.

Recommended sequence:

1. Create a clean Ubuntu 24.04 snapshot.
2. Install only SSH, Git, Docker prerequisites, or snapshot before those if you want stricter proof.
3. Add a deploy key with read-only repo access.
4. Run the install/proof harness.
5. Export `.artifacts/node-proof/latest`.
6. Revert snapshot.
7. Re-run.
8. Compare proof structure.

Once that works, attach the VM as a self-hosted GitHub runner for manual `workflow_dispatch`.

Phase 12: Postpone the gateway and multi-node work until these gates pass.

Do not resume gateway work, multi-node topology, swarm behavior, or generalized company autonomy until all of this is true:

`main` is protected.

Fast validation runs on every PR.

Simulation proof artifacts are uploaded.

A clean VM can produce a full node proof.

Memory canary tests distinguish company isolation from per-agent isolation.

Coordination proofs are scripted.

The direct `hermes_local` path is boring.

At that point, the gateway decision can be revisited. The gateway may still be desirable for a stronger container-to-host boundary, but it should be a later architecture branch with its own proof harness, not something mixed into the current direct-path stabilization.

Your immediate task list.

Create these GitHub issues in order:

1. `chore: reconcile live coordination hygiene fixes with main`

Confirm whether the comment sanitization, parent `blocked` wake, and stranded-parent guard are committed. Commit or revert. No live mutation.

2. `docs: mark PR #5 merged and clarify active direct hermes_local contract`

Update README/current docs so they no longer say PR #5 is pending. Make gateway explicitly deferred.

3. `ci: verify branch protection and required Studio54 gates`

Ensure GitHub Actions exist, are named predictably, and are required on `main`.

4. `proof: define node-proof JSON schema`

Add `schemas/proof/node-proof.schema.json` and `docs/proofs/node-proof-contract.md`.

5. `proof: extract Paperclip coordination poller from session transcript`

Promote the parent/child/run/comment checks into reusable scripts.

6. `proof: add memory canary simulation gate`

Extend the existing simulated VPS bootstrap to include canary checks.

7. `proof: add staging VM node-proof harness`

Run the install path against a clean Ubuntu VM snapshot and collect artifacts.

8. `bootstrap: document and validate --template-file interface`

Your session says the template-backed bootstrap was committed and pushed, but docs still needed to mention `--template-file`.  Close that gap.

9. `ops: add 1215 proof/status/smoke commands`

Wrap existing scripts. Do not attempt one giant launch command yet.

10. `architecture: per-agent Hermes home design`

Only design first. No implementation until the current company-scoped proof harness is green.

Prompt to give your Codex agent now.

Use this as the next task prompt:

```text
You are working in mdc159/studio54.

Current objective: restore source-of-truth discipline after the recent direct hermes_local Paperclip coordination work.

Do not mutate the live VPS.
Do not SSH to production.
Do not broaden into gateway work.
Do not add swarm behavior.
Do not change memory policy.
Do not refactor unrelated files.
Do not push directly to main.

Create a branch from current main.

Task:
1. Inspect whether the following coordination hygiene fixes are present on main:
   - Hermes runtime diagnostic lines are filtered out of ordinary Paperclip issue comments while preserving diagnostics in logs/run output.
   - Parent issue wakes when a child reaches coordination-relevant blocked state.
   - Stranded-work reconciliation does not mark an in-progress parent as stranded while it still has open child issues.
   - Regression tests exist for the above.
2. Inspect whether the template-backed Paperclip Hermes bootstrap commit is present and documented.
3. Inspect docs for stale statements that PR #5 / Langfuse traceability is pending even though it has merged.
4. Produce the smallest PR that reconciles source-of-truth drift.
5. Run:
   - bash scripts/doctor-agent-env.sh
   - bash scripts/validate-repo.sh
   - bash scripts/simulate-vps-bootstrap.sh
   - python3 scripts/agent-evidence-guard.py --base-ref origin/main
6. Include command outputs and any generated artifact paths in the PR body.

Acceptance:
- The repo, not the live VPS, is the source of truth.
- No live mutation occurred.
- The PR is narrow.
- All available local validation passes, or failures are reported with exact logs.
```

Bottom line.

You are not far off track. The repo has already moved toward the right model: direct `hermes_local` as the active path, simulation gates, evidence guard, and cloud-agent workbench documentation. The next correction is operational discipline: protect `main`, stop using the live VPS as the first verifier, promote the ad hoc pollers into proof scripts, and make every agent-produced change pass through GitHub Actions plus a clean VM proof before it touches live infrastructure.
