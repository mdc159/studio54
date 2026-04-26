# Hermes Runtime

This document defines the proven Hermes boundaries on the reference node.

Primary related docs:

- Reference node target: [reference-node-target.md](reference-node-target.md)
- Memory model: [memory-model.md](memory-model.md)
- Paperclip `hermes_local` contract:
  [paperclip-hermes-local-contract.md](paperclip-hermes-local-contract.md)
- Company bootstrap path: [company-bootstrap.md](company-bootstrap.md)

## Outer Hermes

Outer Hermes is the host-native operator runtime.

Proven/current shape:

- runtime home: `/root/.hermes`
- source checkout: `/root/.hermes/hermes-agent`
- CLI shim: `/root/.local/bin/hermes`
- dashboard unit: `hermes-dashboard.service`
- dashboard port: `9119`
- private access: direct tailnet bind on the node MagicDNS hostname

Outer Hermes is independent of Paperclip company lifecycle. It is used for
operator-level work and can supervise or operate the node outside any specific
Paperclip company.

## Inner Hermes

Inner Hermes means Hermes launched by Paperclip through the `hermes_local`
adapter.

Proven/current shape:

- the `hermes` CLI exists inside the Paperclip execution environment
- Paperclip launches it from inside the Paperclip container
- each company receives its own `HERMES_HOME`
- the company home path is:
  `/paperclip/instances/<instance-id>/companies/<company-id>/hermes-home`
- provider/model settings should come from the generated company-scoped Hermes
  runtime files, not from ambient host-only state when company isolation
  matters

Inner Hermes is subordinate to Paperclip company/task state while it is running
as a Paperclip agent.

For Paperclip-assigned tasks, inner Hermes must explicitly update Paperclip
issue state. A successful Hermes process exit is not a task completion signal by
itself. The active direct-path completion action is one Paperclip PATCH that
sets `status: "done"` and includes the completion comment in the same request.

## Paperclip Boundary

Paperclip is the system of record for company state:

- companies
- agents
- org structure
- issues
- assignments
- comments/results
- approvals and budgets when used
- routines when used

Hermes memory is not the system of record for Paperclip company state. When an
inner Hermes agent works on a company task, Paperclip owns the durable company
workflow record.

Outer Hermes may supervise or initialize companies, but it should act through
Paperclip’s control surfaces for company-state mutation rather than around them.

## Memory Isolation

Hermes memory has multiple layers. The active documented model is summarized in
[memory-model.md](memory-model.md). The key local-state rule for this document
is that outer Hermes and Paperclip-internal Hermes runs must not share runtime
homes implicitly.

Outer Hermes and inner Hermes must not share runtime homes implicitly.

Rules:

- outer Hermes uses `/root/.hermes`
- each Paperclip company using `hermes_local` gets its own company-scoped
  `HERMES_HOME`
- one company must not inherit another company's memories through an ambient
  shared Hermes home
- generated company homes contain their own `.env`, `config.yaml`, `skills/`,
  `sessions/`, `logs/`, `memories/`, and `honcho.json`
- Honcho is additive to Hermes local memory rather than a replacement for it
- when enabled for an inner Hermes company, Honcho is self-hosted at the
  loopback `HONCHO_BASE_URL` and uses the Paperclip company ID as workspace

Do not point Paperclip `hermes_local` at `/root/.hermes`.

## Cross-Company Transfer

Cross-company memory transfer is explicit, not ambient.

Allowed pattern:

- a useful lesson is promoted into docs, a skill, or the shared knowledge repo
- another company later consumes that promoted artifact intentionally

Disallowed pattern:

- multiple companies silently share the same Hermes memory/profile state

## Skills Global, Memory Local

Default rule:

- skills are global by default
- company memory is local by default
- promotion from company-local knowledge to shared skill/knowledge is explicit

Examples:

- GitHub workflow skill: global
- n8n integration skill: global
- company-specific task history: local
- company operating norms: local unless deliberately promoted

## Open Questions

- The exact long-term promotion workflow from company-local learning to shared
  skill is not fully automated.
- The host-side gateway/wrapper remains a possible future hardening boundary,
  but it is not the active proven `hermes_local` contract.
- Per-task Honcho session mapping is not implemented yet.
