# Kanban-Coordinated Paperclip Proof Program Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Replace manual human copy/paste coordination with a durable Hermes Kanban experiment graph that proves Paperclip company operation and produces evidence suitable for a production-go/no-go decision.

**Architecture:** Paperclip remains the company/accountability system under test. Hermes Kanban coordinates experiment execution on the Studio54 host, and existing repo-owned proof scripts collect evidence. n8n is introduced only after the underlying Paperclip/Hermes behavior is green, then owns deterministic triggers, callbacks, retries, and artifact routing. All mutation is fail-closed behind an explicit canary approval; plan generation and inventory are read-only by default.

**Canonical experiment specification:** [Paperclip Completion Proof Program](../proofs/paperclip-kanban-completion-program.md). This implementation plan sequences code and validation work; if a detail differs, the canonical proof specification wins.

**Tech Stack:** Hermes Agent Kanban, Paperclip 0.3.1, direct `hermes_local`, Python 3.12+, `uv`, existing Studio54 proof scripts, JSON proof artifacts, optional n8n after core proofs pass.

---

## Scope and invariants

- Preserve every Studio54 service; this program does not deprecate Paperclip, Kanban, or n8n.
- Never use a Kanban card as evidence that a Paperclip mutation or delivery occurred.
- Never use Hermes process exit as evidence that a Paperclip issue completed.
- Keep outer/operator Hermes separate from every Paperclip company `HERMES_HOME`.
- Do not share one `kanban.db` across nodes.
- Treat Kanban tenants as soft namespaces, not security boundaries.
- Do not create a live company, agent, goal, routine, approval, or issue without an explicit canary authorization naming the company and mutation budget.
- Do not publish, contact talent, spend funds, or perform public/irreversible actions in this proof program.
- Store no credentials, raw `.env` values, private runtime dumps, or unrestricted memory exports in artifacts.

## Proof stages

| Stage | Purpose | Mutation allowed? | Exit condition |
|---|---|---:|---|
| 0 | Generate plan and inspect capabilities | No | Valid DAG and prerequisites report |
| 1 | Inventory preserved proof estate | No | Counts and historical fixtures classified |
| 2 | Bootstrap disposable formal-org canary | Yes, separately approved | One CEO/manager/worker tree exists |
| 3 | Prove delegation and completion | Yes, within canary | Parent/child issues complete with attribution |
| 4 | Prove approvals and blocked recovery | Yes, within canary | Approval and unblock paths produce evidence |
| 5 | Prove memory and workspace isolation | Read-only probes after setup | Outer/company and company/company canaries pass |
| 6 | Prove restart/retry/idempotency | Controlled canary only | No duplicate children or side effects |
| 7 | Run productive 1215 research-only pilot | Separately approved | Useful artifact accepted; no publication |
| 8 | Add n8n deterministic routing | Separately approved | Retry/dedupe/approval boundary proven |

### Task 1: Add the canonical orchestration responsibility document

**Objective:** Record why Paperclip, Kanban, and n8n remain in the Studio54 node and identify their non-overlapping authorities.

**Files:**
- Create: `docs/architecture/orchestration-responsibility-model.md`
- Modify: `README.md`
- Modify: `docs/architecture/full-operation-roadmap.md`

**Steps:**

1. Document Paperclip as company/governance state, Kanban as host-local durable agent execution, and n8n as deterministic integration.
2. Document Donna as an external portfolio/fleet governor rather than a cross-company Paperclip agent.
3. Record current live evidence and historical proof caveats without embedding credentials or sensitive host data.
4. Link the new document from the README and current roadmap.
5. Run `git diff --check` and the repository safety scan.

### Task 2: Add a read-only experiment-plan generator

**Objective:** Produce a deterministic JSON DAG that can be translated into Kanban cards without mutating Kanban or Paperclip.

**Files:**
- Create: `scripts/proof/plan-paperclip-kanban-proof.py`
- Test: `stack/control/tests/test_paperclip_proof_plan.py`

**Step 1: Write failing tests**

Tests must verify:

- schema is `studio54.paperclip-kanban-proof-plan.v1`;
- default mode is `read-only`;
- every task has an ID, title, assignee role, parents, mutation class, acceptance criteria, and evidence requirements;
- the graph is acyclic;
- every parent ID exists;
- mutation tasks are blocked by an approval-gate parent;
- no task contains credentials or live company IDs;
- the final synthesis depends on every terminal proof lane.

**Step 2: Run test and observe failure**

```bash
uv run --project stack/control --extra dev pytest stack/control/tests/test_paperclip_proof_plan.py -q
```

Expected: FAIL because the generator does not yet exist.

**Step 3: Implement the generator**

The script must:

- use only the Python standard library;
- emit JSON to stdout by default;
- optionally write to `--output`;
- accept `--mode read-only|canary`;
- require `--approved-company`, a `--mutation-budget` of at least 12, a durable `--approval-id`, a 64-hex `--manifest-sha256`, and a future RFC3339 `--approval-expires-at` for canary mode;
- calculate the twelve bounded planned mutations and reject under-budget plans;
- never call Paperclip, Kanban, n8n, Docker, or a network endpoint;
- return non-zero for invalid canary arguments;
- include explicit `humanApprovalRequired` metadata on mutation tasks.

**Step 4: Run focused tests**

```bash
uv run --project stack/control --extra dev pytest stack/control/tests/test_paperclip_proof_plan.py -q
```

Expected: PASS.

### Task 3: Expose plan generation through the Studio54 CLI

**Objective:** Give operators one repo-owned command for generating the proof graph.

**Files:**
- Modify: `stack/control/control1215/cli.py`
- Modify: `stack/control/tests/test_cli.py`

**Step 1: Add failing CLI tests**

Verify:

```text
./bin/1215 proof paperclip-plan
./bin/1215 proof paperclip-plan --mode canary \
  --approved-company <name> --mutation-budget 12 \
  --approval-id <durable-id> --manifest-sha256 <64-hex-sha256> \
  --approval-expires-at <future-rfc3339>
```

The CLI must pass arguments to the generator and return its status without executing the graph.

**Step 2: Implement the wrapper**

Add `proof paperclip-plan` beside `proof node`. Preserve `proof node` behavior.

**Step 3: Run focused tests**

```bash
uv run --project stack/control --extra dev pytest stack/control/tests/test_cli.py -q
```

Expected: PASS.

### Task 4: Extend the proof contract for the missing production gates

**Objective:** Define the evidence needed beyond the historical manager/worker issue proof.

**Files:**
- Modify: `docs/proofs/node-proof-contract.md`
- Modify later, after a separate implementation review: `schemas/proof/node-proof.schema.json`
- Modify later: `scripts/proof/verify-node-proof.py`

Add planned proof fields for:

- formal `reportsTo` org tree;
- CEO root uniqueness;
- approval request/resolution;
- blocked child and manager wake;
- company-home existence;
- company/company and outer/company isolation;
- Honcho workspace and peer mapping;
- restart/retry evidence;
- idempotent child creation;
- correlation IDs;
- redacted artifact manifest.

Do not change the v1 JSON schema casually. Either add optional backward-compatible fields or version to v2 with fixtures and migration notes.

### Task 5: Run the read-only preflight graph

**Objective:** Exercise Kanban coordination without creating any Paperclip state.

**Files/artifacts:**
- Generated: `.artifacts/paperclip-proof-plan/read-only-plan.json`
- Generated by workers: `.artifacts/paperclip-proof/<run-id>/`

Kanban graph:

```text
root: assess Paperclip production readiness
  ├── live read-only Paperclip inventory
  ├── Studio54 proof-history reconciliation
  ├── current Hermes/Kanban capability check
  ├── memory topology preflight
  └── proof-tooling preflight
        └── synthesis and canary recommendation
```

Acceptance:

- all tasks complete through Kanban tools, not manual copy/paste;
- every completion includes structured evidence;
- no Paperclip mutation appears in activity logs;
- root synthesis labels each gate GREEN, YELLOW, or RED;
- YELLOW is not presented as production health.

### Task 6: Run the approved disposable Paperclip canary

**Objective:** Prove the Paperclip company behaviors that historical fixtures did not prove.

**Prerequisite:** Explicit operator approval naming the canary company and mutation budget.

Required canary shape:

```text
Human board
└── CEO / Pilot Sponsor (reportsTo = null, role = ceo)
    └── Program Manager (reportsTo = CEO)
        ├── Proof Engineer (reportsTo = Program Manager)
        └── Independent Verifier (reportsTo = Program Manager)
```

Required tests:

1. company-scoped `HERMES_HOME` exists;
2. formal org endpoint returns one root and correct nested reports;
3. CEO strategy/approval path produces an approval record;
4. manager creates an unassigned backlog child, then activates it by PATCH;
5. worker completes child with run-scoped comment and attribution;
6. manager wakes and completes parent;
7. blocked child wakes manager and recovers after guidance;
8. duplicate request/idempotency test creates no duplicate child;
9. restart/retry preserves authoritative issue state;
10. `paperclip-coordination-proof.py` passes;
11. memory sentinels do not cross outer/company or company/company boundaries;
12. all artifacts pass redaction.

### Task 7: Run one productive 1215 research-only pilot

**Objective:** Prove business value without publication or sensitive outreach.

Suggested issue:

```text
Generate a redacted current-state inventory for the 1215 prototype in an
isolated worktree, including observed service health, canary Paperclip topology,
and exact verification commands. Do not change runtime configuration.
```

Boundaries:

- research and internal artifact only;
- no public post;
- no performer outreach;
- no fabricated testimonials or consent claims;
- human approval required before any downstream public action.

Success measures:

- operator minutes;
- assignment-to-ack latency;
- execution duration;
- duplicate count;
- retry count;
- approval latency;
- artifact completeness;
- evidence quality;
- memory-isolation result;
- reconstruction from durable state without raw transcripts.

### Task 8: Add n8n only after the core canary is green

**Objective:** Prove deterministic routing without moving reasoning or company authority into n8n.

n8n responsibilities:

- validate execution-envelope schema;
- attach idempotency key and correlation ID;
- deliver to approved intake;
- retry transient failures;
- dead-letter terminal failures;
- validate artifact manifest;
- check approval state at the mutation boundary;
- update notifications and receipts.

n8n must not:

- invent company strategy;
- grant approval;
- share company memory;
- treat webhook receipt as completion;
- publish without an approved mutation record.

## Final acceptance

The program is production-ready only when:

- formal Paperclip org hierarchy is proven;
- company memory and workspace isolation are behaviorally proven;
- approval and blocked/recovery paths are proven;
- retries are idempotent;
- Kanban runs the experiment without manual message ferrying;
- n8n performs only deterministic transport/policy work;
- every claimed success has durable evidence;
- the research-only 1215 pilot produces a useful accepted artifact;
- no RED or YELLOW gate is reported as GREEN.
