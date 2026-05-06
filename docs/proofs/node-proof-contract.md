# Node Proof Contract

The node proof is the durable output from a verifier run against a Studio54
node. It is not an installer and not a live mutation script. It records whether
the verifier could prove the expected node shape, with enough metadata for a
human to inspect the result later.

The v1 proof file is:

```text
.artifacts/node-proof/<timestamp>/proof.json
```

The JSON schema is:

```text
schemas/proof/node-proof.schema.json
```

## Required v1 Fields

Every v1 proof must include:

- `schemaVersion`: fixed string `studio54.node-proof.v1`
- `generatedAt`: verifier timestamp in date-time format
- `git`: checked commit SHA, branch, and dirty-worktree flag
- `target`: target kind, name, host, and environment metadata
- `redaction`: whether the proof output was checked for secrets/runtime state
- `compose`: compose validation status, command, compose files, and services
- `services`: service health/status map
- `paperclip`: company, manager/worker agents, and coordination proof summary
- `hermes`: active Hermes path and run status
- `memoryIsolation`: explicit memory-isolation checks
- `traceability`: traceability status and IDs when present
- `artifacts`: supporting logs, JSON reports, or directories
- `result`: final `PASS` or `FAIL` plus a short summary

## Status Values

Most checks use one of:

- `PASS`: verifier observed the expected condition
- `FAIL`: verifier observed a broken condition
- `SKIP`: verifier did not run the check because a prerequisite was missing
- `UNKNOWN`: verifier could not determine the state

The top-level `result.status` is stricter and must be only `PASS` or `FAIL`.
Missing required fields, missing required artifacts, malformed JSON, or an
unvalidated schema version must produce `FAIL` in the future verifier.

## Traceability IDs

Traceability IDs are optional because simulation and offline proof flows may
not create a live Paperclip/Hermes/Langfuse run. When present, IDs belong under
`traceability.ids`:

- `paperclipRunId`
- `hermesRunId`
- `langfuseTraceId`
- `paperclipIssueId`

For the active direct `hermes_local` path, the expected run identity is:

```text
PAPERCLIP_RUN_ID == HERMES_RUN_ID == LANGFUSE_TRACE_ID
```

The proof contract records those IDs; later verifier scripts are responsible
for enforcing equality when the IDs are available.

## Example

```json
{
  "schemaVersion": "studio54.node-proof.v1",
  "generatedAt": "2026-05-06T09:45:00Z",
  "git": {
    "sha": "3b5cee7",
    "branch": "proof/node-proof-contract",
    "dirty": false
  },
  "target": {
    "kind": "simulation",
    "name": "simulated-vps-bootstrap",
    "host": "localhost",
    "environment": "ci"
  },
  "redaction": {
    "status": "PASS",
    "checked": true,
    "notes": []
  },
  "compose": {
    "status": "PASS",
    "command": "docker compose -f stack/prototype-local/docker-compose.substrate.yml config",
    "composeFiles": [
      "stack/prototype-local/docker-compose.substrate.yml"
    ],
    "services": [
      "postgres",
      "paperclip"
    ]
  },
  "services": {
    "paperclip": {
      "status": "PASS",
      "health": "reachable"
    },
    "hermes": {
      "status": "PASS",
      "health": "hermes_local prepared"
    }
  },
  "paperclip": {
    "status": "PASS",
    "companyId": "company-a",
    "managerAgentId": "manager-agent",
    "workerAgentIds": [
      "worker-agent"
    ],
    "proofSummary": {
      "parentIssue": "PASS",
      "childIssues": "PASS",
      "assignment": "PASS",
      "comments": "PASS",
      "finalStatus": "PASS",
      "runawayChildren": "PASS"
    }
  },
  "hermes": {
    "status": "PASS",
    "path": "hermes_local",
    "mode": "direct per-company Hermes home",
    "runIds": [
      "run-123"
    ]
  },
  "memoryIsolation": {
    "status": "PASS",
    "checks": {
      "companyHomesSeparateFromEachOther": "PASS",
      "hostHomeSeparateFromCompanies": "PASS",
      "honchoWorkspaceEqualsCompanyId": "PASS",
      "honchoAiPeerEqualsPaperclipAgentId": "PASS"
    }
  },
  "traceability": {
    "status": "PASS",
    "ids": {
      "paperclipRunId": "run-123",
      "hermesRunId": "run-123",
      "langfuseTraceId": "run-123",
      "paperclipIssueId": "issue-456"
    }
  },
  "artifacts": [
    {
      "name": "simulated-vps-bootstrap-report",
      "path": ".artifacts/vps-simulation/simulated-vps-bootstrap-report.json",
      "kind": "json"
    }
  ],
  "result": {
    "status": "PASS",
    "summary": "Simulation proof satisfied the v1 node-proof contract."
  }
}
```
