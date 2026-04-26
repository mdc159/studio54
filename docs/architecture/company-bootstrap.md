# Company Bootstrap

This document defines the minimal company bootstrap path that should eventually
be automated by outer Hermes.

It describes only the path proven or directly required by the fresh-node
`hermes_local` proofs.

Primary related docs:

- Hermes runtime boundaries: [hermes-runtime.md](hermes-runtime.md)
- Paperclip `hermes_local` contract:
  [paperclip-hermes-local-contract.md](paperclip-hermes-local-contract.md)
- Shared knowledge repo:
  [agent-knowledge-exchange.md](agent-knowledge-exchange.md)

## Minimal Path

1. Create a Paperclip company.
2. Prepare an isolated company Hermes home.
3. Create one agent using `hermes_local`.
4. Pin the model.
5. Configure `adapterConfig.env.HERMES_HOME`.
6. Create one local Paperclip issue assigned to the agent.
7. Trigger normal heartbeat adapter execution.
8. Verify the agent-authored completion comment/result.
9. Verify the issue reaches `done` through the agent's explicit final PATCH.
10. Keep one durable test company unless there is a clear reason to archive it.

## Company Creation

Create the company through Paperclip.

The first proof kept:

- company: `c754b277-80cc-47f3-8d54-90d02ff41b2d`

The second proof kept:

- company: `ab6896c0-a9a8-473d-943e-88012137055c`

These durable companies are useful for repeat runs and debugging.

## Isolated Hermes Home

Prepare the company home with:

```bash
python3 stack/prototype-local/scripts/prepare_paperclip_hermes_home.py \
  --company-id <company-id>
```

Default container-visible path:

```text
/paperclip/instances/default/companies/<company-id>/hermes-home
```

The prepared tree must be owned by the Paperclip runtime UID/GID.

The script also renders company-scoped `honcho.json`. If the first preparation
happens before the Paperclip agent exists, rerun it with `--agent-id` after
agent creation so the AI peer is `paperclip-agent-<agent-id>`.

## Agent Creation

Create one Paperclip agent with:

- adapter type: `hermes_local`
- pinned model: `google/gemini-2.5-flash`
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

Create one issue assigned to the test agent.

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

Outer Hermes should eventually drive this path as an operator workflow, but the
repo currently proves the manual/API sequence, not a finished automation.

## Open Questions

- The exact API wrapper for Big Hermes to create companies and agents is not
  finalized.
- The archival policy for old durable test companies is not finalized.
