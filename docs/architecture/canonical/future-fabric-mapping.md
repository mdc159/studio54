# Future Fabric Mapping

This document maps the larger memory-fabric vision onto the current proven
architecture. It does not restate the whole north-star architecture and does
not promote future work into the active contract.

## Already Proven Now

| Idea | Current mapping | Contract status |
| --- | --- | --- |
| Direct Paperclip/Hermes execution | Per-company `hermes_local` adapter path | Active |
| Company-scoped local/private memory | Company `HERMES_HOME` under the Paperclip data tree | Active |
| Self-hosted Honcho | Loopback Honcho used by inner Hermes through generated `honcho.json` | Active |
| Honcho tenant key | Paperclip `companyId` as workspace | Active |
| Honcho AI peer | `paperclip-agent-<agent-id>` for one-agent and agent-aware renders; manager/worker currently shares one home-local `honcho.json` | Active with caveat |
| One-agent bootstrap | Reusable one-agent company bootstrap proof | Active |
| Manager/worker bootstrap | Reusable manager/worker proof with shared company home | Active with caveat |
| Paperclip issue state | Explicit final PATCH with `status: "done"` and comment | Active |

## Directly Enabled By Current Module Work

| Idea | Enabled by | Status |
| --- | --- | --- |
| Reusable deployable company block | `bootstrap_paperclip_hermes_company.py` and templates | Near-term productization |
| Repeatable local memory preparation | `prepare_paperclip_hermes_home.py` | Near-term productization |
| Stronger node/company bootstrap command | Proven sequence and JSON summary output | Near-term productization |
| Per-agent Hermes homes | Current topology exposes the limitation clearly | Future implementation |
| Per-task Honcho sessions | Paperclip issue IDs provide a natural session key | Future contract |
| Deliberate company migration | Stable company IDs, homes, and workspaces define what must move | Future workflow |
| Stronger bootstrap verification | Current proof criteria define acceptance checks | Near-term productization |

## Speculative Or Future Work

| Idea | Relationship to current system | Contract status |
| --- | --- | --- |
| Alignment log | Could record promoted lessons and decisions across runs | Future fabric |
| Shared graph corpus | Could receive explicitly promoted entities/relationships | Future fabric |
| Shared vector corpus | Could receive explicitly promoted documents and memories | Future fabric |
| Provider-swappable role cognition | Strategy layer for role behavior across model/providers | Research/strategy |
| Gateway-first Paperclip execution | Existing north-star direction, not active Paperclip contract | Future execution path |
| Cross-company memory fabric | Requires explicit promotion and isolation policy | Future fabric |
| Learning plane promotion gates | Fits the north-star learning plane | Future product/strategy |

## Boundary Statement

The direct `hermes_local` bootstrap module is a reusable deployable block for
company-scoped execution. It is not the whole memory fabric.

Company-scoped `HERMES_HOME` is the current local/private layer. Self-hosted
Honcho is the current additive long-horizon layer. Alignment logs, shared graph,
shared vector corpus, and provider-swappable cognition remain future-state until
they have implementation, runtime contracts, and proofs comparable to the
current Paperclip/Hermes/Honcho path.
