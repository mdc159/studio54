# Canonical Architecture

This directory is the preferred starting point for operators and agents working
on the current Studio54 node architecture.

It is a synthesis layer. It explains what is active now, what is being
productized next, and how the proven Paperclip/Hermes/Honcho work maps into the
longer-horizon architecture without treating future-state design as already
implemented.

## Reading Order

1. [Current contract](current-contract.md)
2. [Bootstrap module](bootstrap-module.md)
3. [Layer map](layer-map.md)
4. [Node growth and isolation](node-growth-and-isolation.md)
5. [Future fabric mapping](future-fabric-mapping.md)
6. Detailed references as needed

## Three-Layer Frame

### 1. Current Contract

This is what is proven and should be treated as active operator guidance today.

The current Paperclip execution path is direct per-company `hermes_local`, with
company-scoped `HERMES_HOME`, self-hosted Honcho as an additive memory layer,
and explicit Paperclip issue completion.

Start with:

- [Current contract](current-contract.md)
- [Paperclip hermes_local contract](../paperclip-hermes-local-contract.md)
- [Company bootstrap](../company-bootstrap.md)

### 2. Near-Term Productization

This is the reusable module and operational shape that should be hardened into
repeatable node/company bring-up.

The main productization unit is the direct Paperclip/Hermes company bootstrap
module.

Start with:

- [Bootstrap module](bootstrap-module.md)
- [Node growth and isolation](node-growth-and-isolation.md)
- [Reference node target](../reference-node-target.md)
- [Operator install runbook](../../../deploy/vps/INSTALL.md)

### 3. Long-Term Memory Fabric

This is the larger architecture direction: shared continuity, explicit
promotion, future shared graph/vector layers, and broader role cognition.

These ideas are useful for planning, but they are not the active Paperclip
execution contract unless a current contract doc says so.

Start with:

- [Layer map](layer-map.md)
- [Future fabric mapping](future-fabric-mapping.md)
- [Honcho memory topology](../honcho-memory-topology.md)
- [North star](../north-star.md)

## Active Reference Docs

Use these for detailed contracts and proof history:

- [Paperclip hermes_local contract](../paperclip-hermes-local-contract.md)
- [Company bootstrap](../company-bootstrap.md)
- [Honcho memory topology](../honcho-memory-topology.md)
- [Reference node target](../reference-node-target.md)
- [Operator install runbook](../../../deploy/vps/INSTALL.md)
