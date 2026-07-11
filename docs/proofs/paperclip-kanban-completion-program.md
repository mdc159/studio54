# Paperclip Completion Proof Program (Hermes Kanban Coordinated)

Status: implementation-ready design; **read-only only until a separately approved canary**.

## 1. Decision and scope

Use Hermes Kanban as the durable experiment coordinator and Paperclip 0.3.1 as the system of record for company structure, goals, projects, issues, approvals, agent runs, and terminal issue state. n8n may transport events, retry deterministic delivery, and collect evidence, but may not decide, approve, retry autonomous business work, or mark Paperclip work complete.

The existing fleet counts (17 proof companies, 24 `hermes_local` agents, 49 issues) are a dated 2026-07-11 read-only operator observation, not yet a repository-owned proof artifact. Stage K00 must refresh them into the redacted baseline inventory before any mutation. The observed fleet is baseline evidence, not a mutation target. The first mutation must occur in one newly created canary company after a human approves a canary manifest. Existing companies and issues remain read-only throughout the pilot.

### Completion claim

The program may claim “Paperclip completion proof” only when one canary company demonstrates all of the following in a single evidence bundle:

1. a valid CEO-led reporting tree;
2. a goal and project linked to useful 1215 work;
3. an approval request that prevents execution before approval and permits it after approval;
4. company-to-company and agent-to-agent memory isolation;
5. process restart and bounded retry without duplicate side effects;
6. worker child and manager parent issues explicitly reach `done` with correctly attributed comments;
7. every required identifier and artifact is machine-verifiable.

## 2. Safety gates and immutable canary manifest

No live write is authorized by this document. Before execution, an operator must approve a manifest containing:

```yaml
schemaVersion: studio54.paperclip-canary.v1
paperclipBaseUrl: http://127.0.0.1:3100
companyName: 1215 Completion Canary <timestamp>
newCompanyOnly: true
allowedExistingCompanyIds: []
maxAgents: 4
maxIssues: 12
maxRunsPerIssue: 3
monthlyBudgetCents: 0
repo: /root/repos/studio54
workspaceMode: dedicated-git-worktree
allowedMutationPaths:
  - docs/proofs/pilot-output/**
forbiddenActions:
  - delete_company
  - mutate_existing_company
  - merge_to_default_branch
  - publish_external
  - rotate_or_read_secrets
expiresAt: <RFC3339>
requestedBy: <operator>
approvedBy: <different-human-or-explicitly-designated-operator>
approvalId: <durable-id>
sha256: <hash-of-canonical-manifest-with-this-field-omitted>
```

Preflight must fail closed if the approval is absent/expired, the hash differs, Paperclip is not 0.3.1, the target company name already resolves to more than one company, any requested write targets an existing company, or the git worktree is not dedicated. Record baseline counts before and after; only canary-owned deltas are allowed. Cleanup is a separate approval, never an automatic finalizer.

## 3. Formal canary organization

Create exactly four agents, all direct `hermes_local`, with immutable IDs captured after creation:

```text
CEO / Pilot Sponsor                    reportsTo: null; role: CEO
└── Program Manager                    reportsTo: CEO
    ├── Proof Engineer                 reportsTo: Program Manager
    └── Independent Verifier           reportsTo: Program Manager
```

Rules:

- Exactly one CEO; only the CEO has `reportsTo = null`.
- Every non-CEO has one acyclic `reportsTo` chain terminating at the CEO.
- The verifier may not implement the artifact it verifies.
- The Program Manager creates a child in `backlog` and unassigned, then activates it with one PATCH setting `assigneeAgentId` and `status: todo`; this avoids the known create-time assignment race.
- All four agents use the canary company boundary. A role/title string alone is not proof: API state must show the reporting edges.

Create one goal, `Prove governed, restart-safe 1215 work completion`, and one project, `First productive 1215 pilot`, linked to that goal. Link every pilot issue to the project (and goal directly if the API supports it). If 0.3.1 lacks one link relation, record `UNSUPPORTED` with endpoint/status/body and use the nearest supported relation; do not silently emulate it in Kanban.

## 4. Automation boundary

| Concern | Authority | May do | Must not do |
|---|---|---|---|
| Hermes Kanban | execution coordination | durable DAG, dependencies, worker dispatch, heartbeats, retries, human block/unblock, evidence aggregation | impersonate Paperclip governance; infer Paperclip issue completion; use tenant as a hard security boundary |
| Paperclip | business/control-plane record | company, org tree, goals, projects, issues, assignments, approvals, run records, explicit terminal state | infer issue `done` from process exit; act as cognitive memory store |
| n8n | event/integration transport | webhook ingestion, polling where no event exists, artifact copying, notifications, deterministic delivery retries, idempotent evidence indexing | approve, retry autonomous business work, assign or close Paperclip issues, own workflow truth, contain secrets in execution logs |
| Git/worktree | productive artifact authority | isolated file changes and commit SHA | merge or publish without a later approval |
| Human operator | irreversible/governance gate | approve canary, answer blocks, approve cleanup/merge | provide approval only through transient chat without durable ID |

A Kanban board is the hard execution boundary: use a dedicated board for this program. Tenant is only a soft namespace; use `tenant=paperclip-canary-<id>` for filtering, never as the security control. Paperclip company ID and separate filesystem/Hermes homes are the actual tenant boundaries.

## 5. Kanban task DAG

Each node completes with structured metadata; parent dependencies gate promotion.

```text
K00 read-only inventory
 └─K01 canary manifest + risk review
    └─K02 HUMAN CANARY APPROVAL (blocked until approvalId supplied)
       └─K03 create canary company + four isolated agent homes
          ├─K04 create/verify reporting tree
          ├─K05 create goal/project + approval policy
          └─K06 memory sentinel setup
             K04,K05,K06 ─┐
                           ├─K07 approval-negative test (work must not start)
                           └─K08 company/agent isolation tests
             K07 ─K09 HUMAN PAPERCLIP APPROVAL ─K10 productive issue fan-out
                                                   ├─K11 engineer produces artifact
                                                   └─K12 restart/retry injection supervisor
             K11,K12 ─K13 manager verifies child, closes parent
             K08,K13 ─K14 independent evidence verification
             K14 ─K15 node-proof bundle + recommendation
```

Assignees/workspaces:

- K00/K14: `verifier`, scratch/read-only.
- K01/K03-K06/K12/K15: `ops`, dedicated persistent evidence directory.
- K07/K09/K10/K13: `program-manager`; K09 is a blocked human gate, not auto-approved.
- K11: `proof-engineer`, dedicated git worktree.
- All child tasks inherit the exact tenant and board. No worker may create an unbounded descendant; K10 may create exactly two Paperclip children.

**Proposed proof-harness policy (not verified built-in Kanban behavior):** cap dispatcher attempts at three per Kanban task with backoff 30 s, 120 s, and 480 s. The harness implementation must configure and behaviorally test these values before claiming them. A retry must inspect the prior run outcome and use the same idempotency key. `spawn_failed` is proposed to block immediately; timeout/crash may retry. The third failure blocks for human disposition. Never delete and recreate a Paperclip issue to “retry.”

**Proposed restart policy:** stop the chosen process only after its run/issue IDs and checkpoint are durable; then start it and verify the implemented dispatcher/worker recovery mechanism. Automatic stale-lease reclamation is a hypothesis to test, not a currently proven Hermes Kanban guarantee. The worker must read task/run history and resume. A resumed task must not recreate company, agent, goal, project, approval, issue, comment, or commit when its idempotency record already exists.

## 6. Productive first 1215 pilot

The canary must produce a useful, low-risk repository artifact rather than only saying “hello.” The pilot issue is:

> Generate a redacted current-state inventory for the 1215 prototype and write `docs/proofs/pilot-output/<canary-id>/current-state.md` containing service names, observed health, the canary Paperclip topology, and exact verification commands. Do not change runtime configuration or source code.

The manager parent issue owns the deliverable. It creates exactly two linked children:

1. **Engineer child:** collect allowed read-only data and write the report in a dedicated worktree; commit it on `proof/paperclip-canary-<id>`.
2. **Verifier child:** compare the report with live read-only queries, validate redaction and links, and post PASS/FAIL.

The manager may close the parent only after both children are `done`, verifier result is PASS, and the commit SHA exists. The artifact stays unmerged. This is productive because it creates a reusable operator inventory while keeping runtime mutation and default-branch risk out of scope.

## 7. Experiment matrix and acceptance criteria

| ID | Experiment | Injection/action | PASS criteria | Required evidence |
|---|---|---|---|---|
| E00 | Baseline protection | read-only inventory of 17/24/49 baseline | baseline IDs/counts recorded; no writes; post-run existing-object diff empty | requests log, before/after snapshot |
| E01 | Org hierarchy | create four agents and reporting edges | one CEO/root; three valid edges; no cycle/orphan; API reads match diagram | agent JSON and graph check |
| E02 | Goal/project | create and link one of each | non-null IDs; project linked to goal; pilot issues linked to project or explicit 0.3.1 `UNSUPPORTED` proof | API JSON/status bodies |
| E03 | Approval deny | assign productive work before approval | no agent run, checkout, file, or comment during a 2× heartbeat interval; issue remains gated | approval/issue/run timeline |
| E04 | Approval allow | human approves once | approval actor/time recorded; exactly one execution begins after approval | approval JSON and timestamps |
| E05 | Company isolation | seed nonce A in canary A, query from disposable canary B | B cannot retrieve A nonce from local files, Hermes search, session DB, or Honcho workspace | hashed sentinels and query results |
| E06 | Agent isolation | distinct manager/engineer nonces | separate per-agent `HERMES_HOME`, state DB, memories, sessions, Honcho peer; cross-query returns no foreign nonce | paths, ownership/mode, peer config, hashes |
| E07 | Paperclip restart | restart Paperclip after checkpoint | service recovers; IDs/status/comments persist; no duplicate issue/run/comment | health timeline and object snapshots |
| E08 | Kanban dispatcher restart | kill dispatcher with K11 leased | stale lease reclaimed; prior outcome visible; same task resumes; one artifact commit | Kanban task/run history |
| E09 | Worker crash/retry | terminate worker after temp file, before commit/PATCH | bounded retry resumes; one final commit; one terminal comment; attempts ≤3 | PIDs/exit, run history, git log |
| E10 | n8n outage | stop/disable evidence relay temporarily | core work continues; queued event later delivered once; no state decision changes | n8n executions and idempotency keys |
| E11 | Issue completion | execute final run-scoped PATCH | child and parent `done`; each terminal comment authored by assignee and `createdByRunId`; process success alone never counted | issue/comment/run JSON |
| E12 | Run identity | inspect direct run | `PAPERCLIP_RUN_ID == HERMES_RUN_ID == LANGFUSE_TRACE_ID` when Langfuse available; otherwise trace explicitly SKIP | IDs and trace lookup |
| E13 | Runaway prevention | observe two heartbeat intervals after done | no extra runs/comments/children; exactly two manager-created children | quiet-period snapshots |
| E14 | Artifact quality | independent verifier checks report | commands reproducible, redaction PASS, required sections present, commit reachable, default branch unchanged | verifier report and SHA |

Global acceptance: E00-E11, E13, and E14 must PASS. E12 may SKIP only for unavailable Langfuse with reason. `UNKNOWN` or undocumented `UNSUPPORTED` fails. Zero secret values may appear in artifacts. Baseline existing objects must have zero mutations. No more than 4 agents, 12 issues, or 3 attempts per issue.

## 8. Memory isolation contract

The current shared company-home manager/worker topology is insufficient for an **agent-isolation** claim. For this canary, provision:

```text
/paperclip/instances/default/companies/<company-id>/agents/<agent-id>/hermes-home
```

Each home contains independent `.env`, `config.yaml`, `honcho.json`, `state.db`, `memories/`, `sessions/`, `skills/`, and logs, owned by the Paperclip runtime UID/GID. Every agent’s persisted adapter binding resolves `HERMES_HOME` to its own path. Honcho uses workspace `<company-id>` and `aiPeer=paperclip-agent-<agent-id>`; a second disposable company uses a different workspace. Shared skills may be copied from an immutable seed, not mounted writable across agents.

Sentinels are random values generated for the test, stored only as SHA-256 in the final bundle. Test local memory, session search, and Honcho separately. “Prompt did not mention it” is not proof of isolation. Because Hermes profiles are not filesystem sandboxes, also prove path ownership and ensure the pilot allowlist prevents writes outside its worktree/evidence/home paths.

If per-agent home projection cannot be implemented before canary approval, E06 is a hard FAIL and the program may only claim company-scoped isolation—not completion.

## 9. Paperclip completion protocol

For every bounded issue:

1. Read issue and current run; acquire/confirm assignment.
2. Perform work and post progress at most once per meaningful checkpoint.
3. Verify output.
4. Make one final run-scoped request containing both terminal state and comment:

```json
{"status":"done","comment":"DONE: <summary>; evidence=<artifact-id>"}
```

Include an authorization bearer header (value redacted from evidence) and `X-Paperclip-Run-Id: <run-id>`. After success, stop. Do not post another comment or poll in the same run. A successful `hermes_local` exit without this PATCH is FAIL. Manager completion additionally requires all child IDs linked by `parentId`, all children `done`, and verifier PASS.

## 10. Evidence bundle and schema

Store under `.artifacts/paperclip-completion/<canary-id>/` (gitignored), with a redacted report optionally copied into the pilot output directory:

```text
manifest.yaml                 # approved manifest, no secrets
inventory-before.json
inventory-after.json
api.ndjson                    # timestamp, method, redacted URL, status, requestHash, responseArtifact
kanban.json                   # board/task/parent/run/outcome/attempt metadata
paperclip.json                # company/org/goal/project/approval/issues/comments/runs
memory-isolation.json
failure-injections.json
n8n.json
repo.json                     # base SHA, branch, commit SHA, changed paths
proof.json
sha256sums.txt
```

Minimum `proof.json` shape:

```json
{
  "schemaVersion": "studio54.paperclip-completion-proof.v1",
  "canary": {"manifestHash": "...", "approvalId": "...", "companyId": "..."},
  "baseline": {"companies": 17, "agents": 24, "issues": 49, "existingMutationCount": 0},
  "organization": {"ceoAgentId": "...", "edges": [], "acyclic": true},
  "governance": {"goalId": "...", "projectId": "...", "approvalId": "...", "deniedBeforeApproved": true},
  "kanban": {"boardId": "...", "tenant": "...", "tasks": [], "restarts": []},
  "memoryIsolation": {"company": "PASS", "agent": "PASS", "sentinelHashes": []},
  "completion": {"parentIssueId": "...", "childIssueIds": [], "terminalPatchRunIds": [], "quietPeriod": "PASS"},
  "experiments": [{"id": "E00", "status": "PASS", "artifacts": []}],
  "repo": {"baseSha": "...", "branch": "...", "commitSha": "...", "defaultBranchChanged": false},
  "redaction": {"status": "PASS", "scanner": "..."},
  "result": {"status": "PASS", "summary": "..."}
}
```

Each experiment record must include `startedAt`, `finishedAt`, actor, exact injection, expected observation, actual observation, referenced immutable IDs, artifact paths, and status (`PASS|FAIL|SKIP`). Generate checksums after redaction. Any malformed schema, missing checksum, missing required experiment, or leaked bearer/token/private key forces top-level FAIL.

## 11. Implementation slices

1. **Read-only verifier:** inventory and feature-discovery client; JSON schema; redactor; baseline diff. No mutation endpoints.
2. **Canary provisioner:** manifest/hash/approval enforcement; new-company-only idempotent creates; per-agent home projection; rollback plan (not automatic deletion).
3. **Governance adapter:** feature-detect goal/project/approval APIs; deny-before-allow assertion; durable approval IDs.
4. **Kanban launcher:** create dedicated board/DAG, exact tenant inheritance, task metadata contracts, attempt caps, lease-reclaim tests.
5. **Failure harness:** PID/container-specific stop/start with service health waits, checkpoints, and duplicate detection. Never `docker compose down -v`.
6. **Evidence collector:** read-only Paperclip/Kanban/n8n/git exports, schema validation, redaction scan, checksums, final PASS/FAIL.
7. **Approved canary:** execute only after a separate manifest approval; stop immediately on scope drift.

## 12. Stop conditions

Block the active Kanban task and require human action on: target ambiguity, duplicate company name, mutation of an existing ID, approval mismatch, agent path outside canary home, secret exposure, attempt cap, unexpected child, baseline drift, verifier conflict, or inability to restore a restarted service. Preserve artifacts and IDs; do not “clean up” evidence or broaden permissions to force a pass.
