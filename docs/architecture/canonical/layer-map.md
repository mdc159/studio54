# Layer Map

This document makes the three-layer planning frame permanent.

## Layer 1: Current Contract

### Purpose

State what is proven, documented, and reproducible now.

### What Belongs Here

- active direct hermes_local runtime contract
- company-scoped HERMES_HOME
- self-hosted Honcho on the active path
- one-agent bootstrap
- manager/worker bootstrap
- comment/wake/completion semantics

### What Does Not Belong Here

- speculative provider mixes by role
- future alignment-log architecture
- unproven gateway-first execution claims

### Current Artifacts

- [current-contract.md](current-contract.md)
- [../paperclip-hermes-local-contract.md](../paperclip-hermes-local-contract.md)
- [../company-bootstrap.md](../company-bootstrap.md)
- [../honcho-memory-topology.md](../honcho-memory-topology.md)
- [../reference-node-target.md](../reference-node-target.md)

### Example

“Direct per-company hermes_local is the active execution path” belongs here.

## Layer 2: Near-Term Productization

### Purpose

Reduce the proven runtime into reusable operator-facing modules and workflows.

### What Belongs Here

- bootstrap scripts
- JSON templates
- manager/worker defaults
- node bring-up sequencing
- bounded validation tasks
- canonical doc layer for operators and agents

### What Does Not Belong Here

- general autonomy frameworks
- broad multi-node shared-memory fabric
- provider research treated as active contract

### Current Artifacts

- [bootstrap-module.md](bootstrap-module.md)
- stack/prototype-local/scripts/bootstrap_paperclip_hermes_company.py
- stack/prototype-local/templates/
- [../../deploy/vps/INSTALL.md](../../deploy/vps/INSTALL.md)

### Example

“Use --template-file with one-agent or manager-worker JSON templates” belongs
here.

## Layer 3: Long-Term Memory Fabric

### Purpose

Describe the larger architecture for shared organizational continuity across
roles, companies, and eventually nodes.

### What Belongs Here

- alignment log
- shared graph/vector/artifact rails
- provider-swappable role cognition
- explicit publication/replay contracts
- broader cross-node continuity

### What Does Not Belong Here

- active runtime claims that have not been proven
- bootstrap details that are already solved and local

### Current Artifacts

- [future-fabric-mapping.md](future-fabric-mapping.md)
- [../north-star.md](../north-star.md)
- `agent-knowledge-exchange/knowledge/research/Self-Hosted Long-Horizon Memory Architecture for Three Hermes-Backed clean.md`

### Example

“Alignment log plus shared graph/vector/artifact stores become the long-horizon
organizational memory plane” belongs here.

## Why The Separation Matters

Layer separation prevents three common mistakes:

1. treating research vision as if it were already runtime truth
2. treating bootstrap/productization work as if it were the final architecture
3. letting future-state components contaminate current operator instructions

## Practical Rule

When writing or reading architecture docs:

- Layer 1 answers: what works now
- Layer 2 answers: what we are packaging next
- Layer 3 answers: where the architecture can grow later

