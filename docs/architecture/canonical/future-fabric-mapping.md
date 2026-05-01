# Future Fabric Mapping

This document maps the larger research vision into the current proven
architecture without collapsing them into one.

Use it to distinguish:

- what is active now
- what current bootstrap/module work directly enables
- what is still future-state

The research note remains vision context:

- `agent-knowledge-exchange/knowledge/research/Self-Hosted Long-Horizon Memory Architecture for Three Hermes-Backed clean.md`

## Already Proven Now

| Idea | Current status | Current artifact |
| --- | --- | --- |
| direct hermes_local bootstrap module | Proven | `bootstrap_paperclip_hermes_company.py` |
| company-scoped local/private runtime memory | Proven | company-scoped HERMES_HOME |
| self-hosted Honcho as additive long-horizon layer | Proven on active path | honcho.json, host-native Honcho service |
| explicit Paperclip control-plane ownership | Proven | issue/task/comment/run contract |
| reusable one-agent and manager/worker bring-up | Proven | bootstrap script + templates |
| explicit promotion rather than ambient company bleed | Proven design rule | honcho-memory-topology.md |

## Directly Enabled By Current Module Work

| Idea | Why current work enables it | Status |
| --- | --- | --- |
| richer company templates | bootstrap interface already exists | Near-term productization |
| stronger validation harnesses | bounded validation tasks already exist | Near-term productization |
| explicit node-addition workflows | current node/company isolation rules are documented | Near-term productization |
| per-task Honcho session mapping | identity and bootstrap discipline are already in place | Next architecture slice |
| broader reusable topologies | one-agent and manager/worker are already proven | Near-term productization |

## Still Speculative / Future Work

| Idea | Why it is not current contract |
| --- | --- |
| alignment log as canonical cross-company continuity rail | not yet the active operator/runtime contract |
| shared Neo4j fact graph as organizational memory plane | not yet part of the proven company runtime path |
| shared Qdrant semantic corpus as organizational memory plane | not yet part of the proven company runtime path |
| artifact-manifest replay as canonical continuity surface | not yet implemented as active company bootstrap/runtime behavior |
| provider-swappable role cognition by node/role mix | still strategy/research layer |
| per-agent Hermes-home isolation inside manager/worker topology | deferred |
| gateway-first Paperclip execution path as active runtime | not current contract |

## Explicit Mapping

### Direct hermes_local Bootstrap Module

Map it as:

- reusable deployable block
- current near-term productization unit
- substrate that future shared-memory layers can build on

### Company-Scoped Memory Isolation

Map it as:

- current local/private layer
- active boundary that prevents ambient company bleed

### Self-Hosted Honcho

Map it as:

- current additive long-horizon layer
- not a replacement for Hermes local memory

### Alignment Log / Shared Graph / Shared Vector Corpus

Map them as:

- long-term memory fabric
- not current active operator/runtime contract

### Provider-Swappable Role Cognition

Map it as:

- research/strategy layer
- not current runtime truth

## Practical Reading Rule

If an idea changes:

- bootstrap inputs
- current company lifecycle
- direct hermes_local runtime semantics
- operator runbook steps

then it must first be stated in the active contract docs before it can be
treated as Layer 1 truth.

If it only changes:

- future shared continuity design
- provider strategy by host role
- future shared-memory publication/replay behavior

then it belongs in the future-fabric layer until proven.

