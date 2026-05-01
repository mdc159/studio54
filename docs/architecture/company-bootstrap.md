# Company Bootstrap

Canonical architecture entrypoint: [canonical/README.md](canonical/README.md).

This document defines the minimal company bootstrap path for the active direct
`hermes_local` Paperclip architecture.

It describes only the path proven or directly required by the fresh-node
`hermes_local` proofs.

Primary related docs:

- Hermes runtime boundaries: [hermes-runtime.md](hermes-runtime.md)
- Paperclip `hermes_local` contract:
  [paperclip-hermes-local-contract.md](paperclip-hermes-local-contract.md)
- Shared knowledge repo:
  [agent-knowledge-exchange.md](agent-knowledge-exchange.md)

## Minimal Path

The smallest reference bootstrap path is one agent:

```bash
python3 stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py \
  --company-name "<company-name>" \
  --company-description "<company-description>" \
  --agent-name "<agent-name>" \
  --agent-role general \
  --agent-title "Operator" \
  --model "<model>" \
  --issue-title "<validation-issue-title>"
```

The script performs the proven direct-path sequence:

1. Wait for Paperclip health.
2. Create or reuse a Paperclip company by exact name.
3. Prepare the isolated company Hermes home.
4. Create or reuse one agent using `hermes_local`.
5. Pin the model.
6. Configure `adapterConfig.env.HERMES_HOME`.
7. Rerender `honcho.json` with the final agent-aware AI peer.
8. Create one local Paperclip validation issue assigned to the agent.
9. Print a JSON summary with company, agent, Hermes home, Honcho peer, issue,
   and verification API paths.

The validation issue then runs through the normal assignment/heartbeat path.
A successful proof verifies:

1. The agent-authored completion comment/result exists.
2. The comment has the assigned agent as `authorAgentId`.
3. The comment has the heartbeat run as `createdByRunId`.
4. The issue reaches `done` through the agent's explicit final PATCH.
5. The company `HERMES_HOME` and `honcho.json` are company-scoped.

## Manager/Worker Path

The reusable manager/worker bootstrap path is also proven:

```bash
python3 stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py \
  --topology manager-worker \
  --company-name "<company-name>" \
  --company-description "<company-description>" \
  --manager-name "<manager-name>" \
  --manager-role general \
  --manager-title "Manager" \
  --worker-name "<worker-name>" \
  --worker-role general \
  --worker-title "Worker" \
  --model "<model>" \
  --manager-worker-issue-title "<validation-parent-title>"
```

The script creates or reuses:

- one Paperclip company
- one manager `hermes_local` agent
- one worker `hermes_local` agent
- one validation parent issue assigned to the manager

The current manager/worker runtime-home contract is company-scoped, not
per-agent. Both manager and worker use the same:

```text
/paperclip/instances/default/companies/<company-id>/hermes-home
```

This is the current practical contract for the direct path. It does not provide
per-agent Hermes memory isolation. Per-agent Hermes homes are future work.

The manager/worker validation task uses this sequencing rule for delegated
worker issues:

1. Create the child issue linked to the parent with `parentId`.
2. Leave the child in `backlog` and unassigned at creation time.
3. Activate the child with a PATCH that sets both:
   - `assigneeAgentId: <worker-agent-id>`
   - `status: "todo"`

This avoids the create-time assignment wake race observed during the first
manager/worker bootstrap proof. That failed worker run was a Paperclip embedded
Postgres setup failure while loading `pg_trgm`; it did not reach Hermes and was
not caused by Honcho or shared `HERMES_HOME`.

Clean manager/worker proof:

- company: `e8613a66-ff00-43af-b4a0-cde3a16a1bcf`
- manager: `bf391c48-bd92-40c0-808d-5e0ab6b8caa3`
- worker: `4840065d-324f-4542-b773-2f6f4cbf1c6e`
- parent: `BOOAAA-1` / `88aa3912-64a7-4935-890f-38575c10071b`
- child: `BOOAAA-2` / `c187d982-d375-4b4f-9a8f-6aab67db8828`

Confirmed:

- no failed worker assignment run
- child `parentId` was correct
- worker completed the child issue
- manager closed the parent after child completion
- parent and child ended `done`
- all observed runs settled as `succeeded`

## Company Creation

The bootstrap script creates or reuses the company through Paperclip.

If more than one company has the requested exact name, the script fails rather
than choosing a hidden duplicate.

The first proof kept:

- company: `c754b277-80cc-47f3-8d54-90d02ff41b2d`

The second proof kept:

- company: `ab6896c0-a9a8-473d-943e-88012137055c`

These durable companies are useful for repeat runs and debugging.

## Isolated Hermes Home

The bootstrap script calls the lower-level preparation script before and after
agent creation:

```bash
python3 stack/prototype-local/scripts/prepare_paperclip_hermes_home.py \
  --company-id <company-id>
```

Default container-visible path:

```text
/paperclip/instances/default/companies/<company-id>/hermes-home
```

The prepared tree must be owned by the Paperclip runtime UID/GID.

The preparation script also renders company-scoped `honcho.json`. The first
preparation can happen before the Paperclip agent exists. The bootstrap script
reruns preparation with `--agent-id` after agent creation so the AI peer is:

```text
paperclip-agent-<agent-id>
```

## Agent Creation

The bootstrap script creates or reuses one Paperclip agent with:

- adapter type: `hermes_local`
- pinned model
- minimal explicit adapter env:
  - `HERMES_HOME=/paperclip/instances/default/companies/<company-id>/hermes-home`

For the minimal proof, keep adapter config narrow:

- required: `env.HERMES_HOME`
- required: pinned `model`
- optional: `cwd` only if the runtime path actually needs it

Do not add extra per-run session/config fields unless the adapter or wake path
requires them.

Do not rely on ambient host/container provider env. Provider keys should come
from the projected per-company Hermes `.env`.

## First Issue

The bootstrap script creates one validation issue assigned to the test agent.

The proof issue should ask for a minimal observable result, such as confirming:

- the active `HERMES_HOME`
- whether `config.yaml` exists
- whether `honcho.json` exists when Honcho is part of the proof

The proof should not require external repos or knowledge exchange access.

For bounded assigned work, include an explicit completion instruction: the
agent must close the issue through Paperclip after posting its final result.
The active direct-path contract is one PATCH that includes both `status: "done"`
and completion comment content. See
[paperclip-hermes-local-contract.md](paperclip-hermes-local-contract.md#task-completion-contract).

## First Execution

Trigger the normal agent execution path that causes the adapter to run.

The reusable bootstrap proof produced:

- company: `ee440385-653c-451d-9058-dc6aa76afd9f`
- agent: `fceca8ee-bbc8-45a0-a853-420a7534c1b2`
- issue: `BOO-1` / `8002bc7e-bf91-46c6-88d5-d6d111735bc3`
- run: `8a6a5f36-d582-4986-8633-a2b578bee0ff`
- comment: `a54ae77d-3fa6-4087-8968-47393c547158`

Confirmed:

- the script created the company, agent, company-scoped Hermes home, and
  validation issue
- `honcho.json` used `workspace = ee440385-653c-451d-9058-dc6aa76afd9f`
- `honcho.json` used
  `aiPeer = paperclip-agent-fceca8ee-bbc8-45a0-a853-420a7534c1b2`
- the assigned `hermes_local` run succeeded
- the useful final comment landed with correct agent/run attribution
- the issue ended `done`
- no wake-loop regression was observed after a quiet-period check

The second proof used an assignment wake through the heartbeat adapter execution
path and produced:

- run: `3a2b0317-bee0-48fb-8cb1-2b4590bb9a6f`
- comment: `5ded90f3-32a1-4a2d-867b-63d191441a4b`

## Success Criteria

A bootstrap proof is successful when:

- the heartbeat run succeeds
- the run uses `hermes_local`
- the agent-authored comment/result exists
- the comment has the assigned agent as `authorAgentId`
- the comment has the heartbeat run as `createdByRunId`
- the assigned issue ends in `done` through an explicit final PATCH from the
  agent
- the comment/result confirms the expected company `HERMES_HOME`
- `config.yaml` exists under that `HERMES_HOME`
- no ambient `/root/.hermes` memory is used for the company run

The issue/comment/result path is sufficient for the proof. The first proof does
not need routines or a broader automation loop unless that is the only wake
path available.

Paperclip does not infer task completion merely from adapter/process success.
The agent is responsible for closing the issue through the Paperclip API.

## Durable Test Companies

Keep at least one durable test company after a proof run.

Do not delete it immediately. Archive it later only if it becomes noisy or
actively blocks follow-up debugging.

## Automation Boundary

The active repo-owned reference path is
`bootstrap_paperclip_hermes_company.py`. Its proven topologies are:

- `--topology one-agent`
- `--topology manager-worker`

Older gateway-oriented bootstrap work, including `bootstrap_paperclip_ceo.py`,
is historical/optional/future-state and is not the active direct-path bootstrap
contract.

Outer Hermes may eventually drive this path as an operator workflow, but the
current active contract is the reusable host-side script plus the normal
Paperclip assignment/heartbeat execution path.

## Open Questions

- The archival policy for old durable test companies is not finalized.
- Per-agent Hermes homes for manager/worker companies are not implemented.
