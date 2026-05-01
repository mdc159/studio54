# Canonical Architecture Set

This is the preferred reading order for new operators and agents.

It sits above the detailed architecture docs as a synthesis layer. It does not
replace the detailed reference docs.

Use this set to answer three questions in order:

1. What is the current proven contract?
2. What part of the system is the reusable bootstrap/runtime module?
3. Where does the larger long-horizon architecture vision begin?

## Reading Order

1. [current-contract.md](current-contract.md)
2. [bootstrap-module.md](bootstrap-module.md)
3. [layer-map.md](layer-map.md)
4. [node-growth-and-isolation.md](node-growth-and-isolation.md)
5. [future-fabric-mapping.md](future-fabric-mapping.md)
6. detailed reference docs as needed

## How To Use This Set

### If You Need Runtime Truth

Start with:

- [current-contract.md](current-contract.md)
- [../paperclip-hermes-local-contract.md](../paperclip-hermes-local-contract.md)
- [../company-bootstrap.md](../company-bootstrap.md)

### If You Need The Reusable Bootstrap/Launch Module

Start with:

- [bootstrap-module.md](bootstrap-module.md)
- [../company-bootstrap.md](../company-bootstrap.md)
- [../../deploy/vps/INSTALL.md](../../deploy/vps/INSTALL.md)

### If You Need Memory And Isolation Rules

Start with:

- [node-growth-and-isolation.md](node-growth-and-isolation.md)
- [../honcho-memory-topology.md](../honcho-memory-topology.md)
- [../reference-node-target.md](../reference-node-target.md)

### If You Need The Larger Vision

Start with:

- [future-fabric-mapping.md](future-fabric-mapping.md)

Then read the north-star/research context:

- [../north-star.md](../north-star.md)
- `agent-knowledge-exchange/knowledge/research/Self-Hosted Long-Horizon Memory Architecture for Three Hermes-Backed clean.md`

The research note is vision context, not the active contract.

## Three-Layer Frame

The architecture is intentionally split into three layers:

### Layer 1: Current Contract

This is what is proven, documented, and reproducible now.

### Layer 2: Near-Term Productization

This is the reusable packaging of the proven pieces:

- bootstrap scripts
- templates
- manager/worker defaults
- node bring-up rules

### Layer 3: Long-Term Memory Fabric

This is the larger future architecture:

- alignment log
- shared graph/vector/artifact rails
- provider-insulated shared organizational continuity

The key rule is:

- do not treat Layer 3 vision as if it were already Layer 1 runtime truth

## Detailed Reference Docs

Active detailed references:

- [../paperclip-hermes-local-contract.md](../paperclip-hermes-local-contract.md)
- [../company-bootstrap.md](../company-bootstrap.md)
- [../honcho-memory-topology.md](../honcho-memory-topology.md)
- [../reference-node-target.md](../reference-node-target.md)
- [../../deploy/vps/INSTALL.md](../../deploy/vps/INSTALL.md)

