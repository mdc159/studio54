# Hermes Runtime Definition

Concrete definition of Hermes on the Donna / Studio54 reference node.

This document is not about aspirational architecture. It defines what Hermes is
supposed to be in this system, why it is host-native, and what boundaries it is
expected to keep relative to Paperclip and the containerized stack.

Related documents:

- Live node inventory: [donna-vps-service-map.md](donna-vps-service-map.md)
- Reference-node target: [reference-node-target.md](reference-node-target.md)
- Node responsibilities: [node-roles.md](node-roles.md)
- Bootstrap contract: [hermes-bootstrap.md](hermes-bootstrap.md)
- System config map: [system-config-map.md](system-config-map.md)

## Role

Hermes is the executive agent runtime.

On this node, Hermes is intended to be:

- host-native by design
- privileged by design
- private by design
- defined, not exceptional

Hermes is not "inside" Paperclip. Paperclip is one structured orchestration
environment that Hermes may direct, but Hermes also retains independent agency
outside that environment.

In plain terms:

- Hermes is the CEO runtime
- Paperclip is the company orchestration runtime
- Hermes may govern Paperclip
- Hermes may also pursue independent work outside Paperclip

That separation is intentional and should be preserved.

## Why Hermes Is Host-Native

Hermes is expected to have machine-level operator authority. That includes work
such as:

- inspecting and operating Docker on the host
- creating or removing containers
- inspecting host filesystems and logs
- operating system services through `systemd`
- interacting with host-level sockets, runtimes, and credentials

Trying to containerize Hermes while preserving those powers would require
turning the container into a disguised host process by mounting broad host
resources, exposing Docker control, or running with privileged settings. That
would add indirection without meaningfully improving the trust boundary.

For this reason, the reference-node contract is:

- Hermes remains host-native
- containerized services reach Hermes only through explicit boundaries
- Hermes is documented as part of the host control plane, not the app plane

## Live Donna Contract

Observed live install paths on Donna:

- Binary shim: `/root/.local/bin/hermes`
- Binary target: `/root/.hermes/hermes-agent/venv/bin/hermes`
- Source checkout: `/root/.hermes/hermes-agent`
- Runtime home: `/root/.hermes`
- Service unit: `/etc/systemd/system/hermes-dashboard.service`
- Service logs: `/var/log/hermes-dashboard/`

Observed service contract:

- systemd unit name: `hermes-dashboard.service`
- service user: `root`
- dashboard command:
  `hermes dashboard --host donna.tailfedd3b.ts.net --port 9119 --no-open --insecure`
- listener: `100.87.24.49:9119` on the Tailscale interface
- private access path: `http://donna.tailfedd3b.ts.net:9119/`

The dashboard is private because:

- the service binds on the tailnet address only
- UFW exposes only `22/tcp` publicly
- the dashboard is not served through public HTTP ingress

## Host Header Constraint

Hermes dashboard validates the incoming `Host` header against the hostname it
was bound to. This matters operationally.

For Donna, that means:

- loopback bind plus generic reverse proxy is not always sufficient
- Tailscale Serve is not currently the cleanest path for Hermes
- binding Hermes directly to its MagicDNS hostname on the tailnet is the
  simplest private access contract that still satisfies Hermes's host-header
  checks

This is why Hermes differs from the containerized services, which are currently
published through Tailscale Serve.

## Authority Boundary

Hermes is allowed to exercise host-level authority. That authority is not
implicit; it should be treated as an explicit contract.

On the reference node, Hermes is intentionally allowed to:

- inspect and manage Docker workloads
- read and modify files on the host
- inspect and manage host services
- operate as a system-level executive agent

Hermes is not intended to be constrained to Paperclip's lifecycle or data model.

## Relationship To Paperclip

Paperclip is the company orchestration layer. Hermes is the executive runtime.

The intended relationship is:

- Paperclip hosts specialist workflows, operator surfaces, and company logic
- Hermes may direct or supervise Paperclip through defined interfaces
- Hermes remains operationally independent from Paperclip

The architecture should avoid two bad collapses:

1. treating Hermes as just another Paperclip worker
2. treating Paperclip as the total container for Hermes's identity and authority

The reference-node design should preserve:

- Hermes independence
- Paperclip specialization
- explicit integration points between them

## Target Repo Contract

For rebuildability, the repo should eventually define Hermes through explicit
host-bootstrap artifacts:

- deterministic install path
- deterministic runtime home
- checked-in systemd unit template
- checked-in environment/config contract
- checked-in bootstrap or repair script

The current live rebuild sequence for Donna is captured in
[hermes-bootstrap.md](hermes-bootstrap.md).

The important point is not that Hermes becomes containerized. The important
point is that Hermes becomes reproducible.

## Definition Of "Defined"

Hermes is considered defined on the reference node when all of the following are
true:

1. its install paths are known
2. its service unit is known
3. its privilege model is intentional
4. its network contract is intentional
5. its relationship to Paperclip is explicit
6. a fresh-node rebuild path can recreate it without archaeology
