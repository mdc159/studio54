# Node Growth And Isolation

This document explains how to add more nodes without causing memory collision
or accidental cross-company bleed.

It summarizes the strongest active rules from
[../honcho-memory-topology.md](../honcho-memory-topology.md) in operator form.

## Core Isolation Rules

- outer Hermes is node-local
- Paperclip company memory is company-scoped
- Honcho workspace key uses companyId
- Honcho AI peer uses paperclip-agent-<agent-id>
- no company points at /root/.hermes
- no ambient cross-company sharing
- promotion is explicit
- migration between nodes is a deliberate workflow

## Current Weak Spot

Manager/worker is company-scoped, not per-agent-home isolated.

That means:

- the topology is currently safe at the company boundary
- it is not yet per-agent Hermes-home isolated inside one company

## Boundary Diagram

`mermaid
flowchart LR
    subgraph NodeA["Node A"]
        subgraph OuterA["Outer Hermes"]
            OA["/root/.hermes"]
        end
        subgraph Company1["Company 1"]
            C1H["HERMES_HOME company-1"]
            C1W["Honcho workspace = company-1"]
            C1P["AI peer = paperclip-agent-*"]
        end
    end

    subgraph NodeB["Node B"]
        subgraph OuterB["Outer Hermes"]
            OB["/root/.hermes"]
        end
        subgraph Company2["Company 2"]
            C2H["HERMES_HOME company-2"]
            C2W["Honcho workspace = company-2"]
            C2P["AI peer = paperclip-agent-*"]
        end
    end

    Shared["Future shared fabric<br/>alignment log / graph / vector / artifacts"]

    OA -. explicit promotion only .-> Shared
    C1H -. explicit promotion only .-> Shared
    OB -. explicit promotion only .-> Shared
    C2H -. explicit promotion only .-> Shared
`

Interpretation:

- each node has its own outer Hermes state
- each company has its own company-scoped Hermes home
- future shared organizational memory is not ambient runtime sharing

## Node Addition Checklist

### Add A New Outer-Hermes Node

1. install outer Hermes
2. give it its own HERMES_HOME
3. if using Honcho, point it at the node-local self-hosted Honcho service
4. name outer workspace/peer explicitly for that node
5. do not point it at any company HERMES_HOME

### Add A New Paperclip Execution Node

1. bootstrap the node as a reference node
2. install/start self-hosted Honcho on loopback
3. bring up Paperclip and direct hermes_local
4. for each company:
   - prepare company HERMES_HOME
   - render workspace = companyId
   - render `aiPeer = paperclip-agent-<agent-id>`
5. validate one bounded task

### Move A Company To Another Node

1. preserve or migrate Paperclip company state
2. preserve or migrate company HERMES_HOME
3. preserve or migrate company Honcho workspace data
4. verify agent IDs still match expected peer naming

Do not treat company movement as “just recreate the agent” unless memory
continuity loss is acceptable.

## What Not To Do

- do not point many companies at /root/.hermes
- do not let two companies share one Honcho workspace
- do not use node hostname as company identity
- do not assume Honcho replaces Hermes local memory
- do not describe manager/worker as per-agent local isolation yet
- do not silently share runtime homes across nodes

## Naming Rules

### Workspaces

- company runtime:
  - <paperclip-company-id>
- outer Hermes:
  - `node-<node-slug>-outer`

### Peers

- company AI peer:
  - paperclip-agent-<agent-id>
- outer Hermes AI peer:
  - outer-hermes-<node-slug>
- operator peer:
  - operator-root or explicit operator handle

## Promotion Rule

Local/company memory stays local by default.

Cross-company or cross-node reuse must be promoted explicitly into:

- shared skills
- shared docs
- shared knowledge repo
- future shared organizational memory substrates

