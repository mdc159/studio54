# Layer Map

The architecture is planned in three layers. Keep these layers separate when
writing docs, planning implementation, or debugging runtime behavior.

## Layer 1: Current Contract

Purpose:

- Describe what is proven and active now.
- Give operators and agents instructions they can safely follow today.

Current artifacts:

- [Current contract](current-contract.md)
- [VPS launch and company operation](vps-launch-and-company-operation.md)
- [Paperclip hermes_local contract](../paperclip-hermes-local-contract.md)
- [Company bootstrap](../company-bootstrap.md)
- [Honcho memory topology](../honcho-memory-topology.md)

Belongs here:

- Direct per-company `hermes_local`.
- Company-scoped `HERMES_HOME`.
- Self-hosted Honcho on the active path.
- One-agent and manager/worker bootstrap.
- Explicit issue completion through Paperclip.

Does not belong here:

- Gateway-first Paperclip execution.
- Per-agent Hermes homes.
- Per-task Honcho session contracts.
- Shared graph/vector fabric.

Example:

- A validation issue assigned to a `hermes_local` agent completes with one
  run-scoped PATCH containing both `status: "done"` and a completion comment.

## Layer 2: Near-Term Productization

Purpose:

- Turn the proven path into repeatable operational modules.
- Preserve active contracts while making node and company setup easier.

Current artifacts:

- [VPS launch and company operation](vps-launch-and-company-operation.md)
- [Bootstrap module](bootstrap-module.md)
- [Node growth and isolation](node-growth-and-isolation.md)
- [Reference node target](../reference-node-target.md)
- [Operator install runbook](../../../deploy/vps/INSTALL.md)

Belongs here:

- Idempotent company bootstrap.
- Stronger bootstrap verification.
- Node-addition checklists.
- Deliberate company migration workflow.
- Per-agent Hermes homes after they are implemented and proven.

Does not belong here:

- Treating research concepts as active runtime promises.
- Silent cross-company memory sharing.
- Replacing Paperclip as the issue state system of record.

Example:

- The bootstrap module prepares company memory, creates agents, renders Honcho
  config, and proves lifecycle with a bounded task.

## Layer 3: Long-Term Memory Fabric

Purpose:

- Preserve the larger architecture direction without collapsing it into the
  current implementation.
- Identify how local/private memory can later promote into shared continuity
  and learning layers.

Current artifacts:

- [Future fabric mapping](future-fabric-mapping.md)
- [North star](../north-star.md)
- [Memory model](../memory-model.md)
- [Agent knowledge exchange](../agent-knowledge-exchange.md)

Belongs here:

- Shared continuity plane.
- Alignment logs.
- Shared graph and vector corpus.
- Explicit promotion from local/private memory into shared knowledge.
- Provider-swappable role cognition and learning strategy.

Does not belong here:

- Operator instructions for the active Paperclip `hermes_local` path.
- Claims that shared fabric is already implemented.
- Implicit company or node memory federation.

Example:

- A useful lesson from a company run is promoted deliberately into shared docs or
  skills instead of being leaked through a shared runtime home.
