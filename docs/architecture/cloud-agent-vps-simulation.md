# Cloud Agent Workbench and VPS Simulation

Studio54 agents should not be trusted because they say a task is done. They earn
trust by producing repeatable artifacts from a disposable environment.

This document defines the first cloud-safe primitive block for iterative
agent work:

```text
GitHub Issue / PR = source of truth
Codespace = disposable cloud workbench
GitHub Actions = repeatable verifier
JSON/log artifacts = evidence
Donna/Miguel = merge and live-infra approval gate
```

## Why this exists

Manual copy/paste between isolated agents was painful, but it prevented a worse
failure mode: a single agent gaming its own evaluation. The same issue appears in
research/simulation work when an agent edits the judge, draws its own graphs, or
claims victory without producing tool-generated evidence.

The answer is not to trust the agent harder. The answer is to make the loop more
boring:

1. Work happens on a branch.
2. Validation runs in a clean cloud environment.
3. The verifier emits machine-readable reports and logs.
4. Protected verifier changes are visible as review items.
5. Real VPS mutation stays behind a separate explicit approval gate.

## Current gates

### `scripts/doctor-agent-env.sh`

Checks whether the workbench has the required tools without printing secrets:

- `git`
- `gh`
- `uv`
- `python3`
- `docker`
- GitHub auth state, redacted
- repo remote/status

### `scripts/validate-repo.sh`

Runs fast repo validation:

- Python syntax checks for repo-owned scripts
- `control1215` pytest suite
- Hermes Langfuse probe tests
- Paperclip package metadata smoke
- Docker Compose config rendering when Docker is available

Artifacts land under:

```text
.artifacts/agent-validation/
```

### `scripts/simulate-vps-bootstrap.sh`

Creates a disposable fake VPS root under `/tmp`, then prepares two isolated
Paperclip company Hermes homes:

```text
<pseudo-vps>/paperclip/instances/default/companies/company-a/hermes-home
<pseudo-vps>/paperclip/instances/default/companies/company-b/hermes-home
```

The simulation verifies:

- company homes do not point at host `/root/.hermes`
- company homes are separate from each other
- `config.yaml`, `.env`, and `honcho.json` exist
- `honcho.json.workspace == companyId`
- `honcho.json.aiPeer == paperclip-agent-<agentId>`
- Honcho base URL stays loopback for the simulated node

Artifacts land under:

```text
.artifacts/vps-simulation/simulated-vps-bootstrap-report.json
```

## Anti-cheat posture

The useful lesson from autonomous-research loops such as Karpathy's
`autoresearch` is not "let the agent do anything." It is the opposite:

- keep the editable surface small,
- keep the evaluator/prep path separate,
- use a fixed budget,
- use a fixed metric,
- make every run produce an artifact.

For Studio54, the initial equivalent is:

```text
Editable surface: branch code/docs under review
Evaluator surface: scripts + GitHub Actions gates
Budget: bounded CI job timeout
Metric: PASS/FAIL plus JSON evidence
Artifact: uploaded validation/simulation logs and reports
```

This is not a perfect sandbox. A sufficiently privileged contributor can edit the
workflow, test, or verifier. The first protection is visibility:

- verifier scripts are named and small,
- output is JSON/log based,
- `scripts/agent-evidence-guard.py` reports protected verifier-path changes,
- PR review should treat verifier changes and feature changes separately.

## Protected-path review policy

The repository carries `.github/CODEOWNERS` so GitHub can identify the owner for
verifier, proof, deployment, and operator-control paths. In the current
solo-owner workflow, branch protection keeps PRs and required Actions checks
enforced, but required approving review is disabled because GitHub does not
allow the PR author to approve their own PR. CODEOWNERS remains the durable
ownership map and can be re-enabled as an enforced branch-protection gate when
a second reviewer or separate bot/app author identity exists.

The advisory evidence guard treats these paths as protected review surfaces:

- GitHub workflows and CODEOWNERS
- repo validation, environment doctor, evidence guard, and simulated VPS
  verifier scripts
- proof scripts and proof schemas
- deployment/runbook scripts under `deploy/`
- the operator CLI entrypoint `bin/1215`
- the repo-owned control CLI under `stack/control/`
- prototype bootstrap scripts under `stack/prototype-local/scripts/`

When a PR touches any of those paths, `scripts/agent-evidence-guard.py` emits
`REVIEW_REQUIRED` in its JSON artifact while still exiting successfully. The
status is advisory: it does not replace branch protection, and it should be
used to make verifier or deployment-surface edits obvious in review.

Future hardening can run selected evaluators from a pinned trusted ref or a
separate evaluator repository. For now, this gate prevents the common failure
mode where an agent modifies production-ish code, changes the judge, draws its
own graph, and declares victory without a fresh, inspectable artifact.

## Operating rule

A PR is not ready for real VPS testing until:

1. `Studio54 validation` passes,
2. `VPS bootstrap simulation` passes,
3. the simulation report is attached as a GitHub Actions artifact,
4. Donna/Miguel explicitly approve moving from simulation to staging/live infra.

No cloud agent may mutate the real VPS as part of these gates.
