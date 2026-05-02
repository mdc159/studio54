# Hermes Agent Backup and Restore Runbook

This runbook defines the current recovery model for Hermes-backed personas in
the Studio54 fleet: Donna as the hub/control-plane persona, Victoria as the
cloud VPS persona, Nikoli/Nikolai as the WSL workstation persona, Sam as the
mobile-edge candidate, and future Paperclip company-local Hermes agents.

The goal is fast, low-surprise recovery to a last known good state without
confusing Hermes runtime state, Honcho long-horizon memory, Paperclip company
state, or project working-tree rollback.

## Safety Classification

Hermes backups can contain live credentials. Treat every backup archive,
state snapshot, restored `.env`, `auth.json`, session database, and memory store
as secret-bearing unless proven otherwise.

Rules:

- Do not commit backup archives, state snapshots, `.env`, `auth.json`, raw
  session databases, memory stores, or raw gateway logs.
- Do not paste backup contents into GitHub, Linear, chat, docs, or model
  prompts.
- Store recovery artifacts in a private, encrypted, access-controlled location.
- Prefer redacted metadata in ledgers: path class, file names, existence,
  timestamps, sizes, and validation results.
- Rotate credentials if a backup, `.env`, auth export, token, invite URL, or key
  is exposed outside the secure host.

## Recovery Layers

Hermes has several recovery surfaces that sound similar but solve different
problems.

| Layer | Command / location | Purpose | Portable? | Notes |
|---|---|---|---|---|
| Full Hermes home backup | `hermes backup -o <zip>` | Portable backup of most of `~/.hermes` | Yes, with secrets handled carefully | Excludes Hermes source checkout and transient dirs. |
| Full Hermes import | `hermes import <zip>` | Restore full backup into `HERMES_HOME` | Yes | Overwrites target files; use a temp home for rehearsal first. |
| Quick state snapshot | `hermes backup --quick --label <label>` or `/snapshot create <label>` | Fast rollback of critical runtime state | Host-local by default | Stored under `~/.hermes/state-snapshots/`. |
| Quick state restore | `/snapshot restore <id>` | Restore critical runtime state | Host-local by default | Restart recommended after `state.db` restore. |
| Filesystem checkpoints | `--checkpoints`, `/rollback`, `~/.hermes/checkpoints/` | Roll back project file edits | No | Shadow git repos keyed to working directories; not persona backup. |
| Sessions export | `hermes sessions export <jsonl>` | Archive/audit conversation history | Yes | `state.db` is the primary session store. |
| Honcho backup | DB/volume backup of Honcho service | Restore long-horizon memory | Yes, if DB/volumes captured | Hermes backup only stores the Honcho client config. |
| Paperclip backup | Paperclip DB/volume backup | Restore company/issues/agents state | Yes, if DB/volumes captured | Hermes memory is not the Paperclip system of record. |

## What `hermes backup` Covers

`hermes backup` creates a zip archive of the Hermes home directory and performs
safe SQLite copies for `.db` files. The implementation excludes the Hermes Agent
source repo and transient files so the backup stays focused on user/runtime
state.

Expected important contents:

- `config.yaml`
- `.env`
- `auth.json`
- `state.db`
- `sessions/`
- `skills/`
- `memories/`
- `honcho.json`
- `cron/jobs.json` when present
- gateway and channel state files
- pairing data when present
- profile directories and wrapper metadata when present

Expected exclusions:

- `hermes-agent/` source checkout
- prior backups
- filesystem checkpoints
- Python caches
- SQLite sidecar files such as `*.db-wal`, `*.db-shm`, and `*.db-journal`
- runtime PID files

Restore note: the Hermes source checkout is expected to be reinstalled or
updated separately after import. A full import may restore profile metadata and
then print follow-up commands for profile gateway services.

## What Quick Snapshots Cover

Quick snapshots are the fast emergency rewind surface. Current critical state
files include:

- `state.db`
- `config.yaml`
- `.env`
- `auth.json`
- `cron/jobs.json`
- `gateway_state.json`
- `channel_directory.json`
- `processes.json`
- pairing directories/files when present

They are useful before updates, provider changes, gateway changes, pairing
changes, or other Hermes runtime state edits.

They are not a full migration artifact because they do not intentionally capture
the whole Hermes home, all skills, all caches, or external memory/database
services.

## What Files Matter for a Persona

For a host-native Hermes persona such as Donna, Victoria, or Nikoli, the fast
recovery set is:

```text
~/.hermes/config.yaml
~/.hermes/.env
~/.hermes/auth.json
~/.hermes/state.db
~/.hermes/honcho.json
~/.hermes/skills/
~/.hermes/memories/
~/.hermes/sessions/
```

If the persona receives messages or owns gateway runtime state, also capture:

```text
~/.hermes/gateway_state.json
~/.hermes/channel_directory.json
~/.hermes/pairing/
~/.hermes/platforms/pairing/
~/.hermes/cron/jobs.json
```

Important but usually reconstructable:

```text
~/.hermes/bin/
~/.hermes/hooks/
~/.hermes/.hermes_history
~/.hermes/context_length_cache.yaml
~/.hermes/models_dev_cache.json
```

Usually not migrated as canonical recovery state:

```text
~/.hermes/logs/
~/.hermes/cache/
~/.hermes/audio_cache/
~/.hermes/image_cache/
~/.hermes/checkpoints/
~/.hermes/hermes-agent/
```

## Honcho Memory Boundary

Hermes backup restores Hermes' Honcho client configuration, not the full Honcho
memory backend.

Hermes-side config lives in:

```text
~/.hermes/honcho.json
```

That file records information such as whether Honcho is enabled, the base URL,
workspace, AI peer, user peer, recall mode, and session strategy. It does not
contain the complete long-horizon memory graph/vector/database state.

For Donna's current self-hosted pattern, the actual long-horizon memory lives in
the Honcho service and its backing database/cache. Recovery therefore needs two
artifacts:

1. Hermes backup: restores local Hermes runtime, tools, sessions, configs, and
   the pointer to Honcho.
2. Honcho data backup: restores the memory service's durable database/volumes.

Do not claim a persona has been restored to its last known memory state until
both Hermes local state and Honcho backend state have been validated.

Validation checks:

```bash
hermes memory status
hermes honcho status
```

Expected validation should confirm only redacted metadata: provider, enabled
state, configured workspace, configured peers, connection status, and whether
memory calls work. Do not print API keys, raw observations, raw session dumps,
or database contents into public docs.

## Paperclip and Inner Hermes Boundary

Paperclip company-local Hermes agents are different from outer/operator Hermes.

For `hermes_local`, each Paperclip company should receive an isolated
`HERMES_HOME`. Company-local homes may contain their own:

- `.env`
- `config.yaml`
- `skills/`
- `sessions/`
- `logs/`
- `memories/`
- `honcho.json`

Paperclip remains the system of record for company state: companies, agents,
org structure, issues, assignments, comments, and completion status. A Hermes
backup alone does not restore Paperclip company state.

For a Paperclip division/company recovery, capture:

1. Paperclip database and relevant volumes.
2. Company-local Hermes homes.
3. Honcho workspace/backend state if enabled for company-local memory.
4. Adapter configuration and model/provider policy.
5. Redacted bootstrap record: company ID, agent IDs, issue IDs, and validation
   task references.

Do not point Paperclip `hermes_local` at the hub persona's `/root/.hermes`.

## Restore Rehearsal Procedure

Use a rehearsal before touching live Donna/Victoria/Nikoli state.

### 1. Create a full backup

```bash
hermes backup -o /secure/backups/hermes-<persona>-<date>.zip
```

### 2. Create a quick local snapshot before risky work

```bash
hermes backup --quick --label before-restore-drill
```

or from an interactive Hermes session:

```text
/snapshot create before-restore-drill
```

### 3. Restore into a temporary home first

Use a scratch `HERMES_HOME` rather than overwriting the live persona as the
first test.

```bash
mkdir -p /tmp/hermes-restore-drill
HERMES_HOME=/tmp/hermes-restore-drill hermes import /secure/backups/hermes-<persona>-<date>.zip --force
```

Then validate metadata only:

```bash
HERMES_HOME=/tmp/hermes-restore-drill hermes profile list
HERMES_HOME=/tmp/hermes-restore-drill hermes sessions stats
HERMES_HOME=/tmp/hermes-restore-drill hermes memory status
HERMES_HOME=/tmp/hermes-restore-drill hermes honcho status
```

If the restored profile needs live external credentials, confirm credential
presence by name/metadata only. Do not print values.

### 4. Reinstall or update Hermes source as needed

Full backups exclude the Hermes Agent source checkout. On a fresh host, install
or update Hermes separately, then import runtime state.

Expected source/runtime split:

```text
Hermes source checkout: ~/.hermes/hermes-agent
Hermes runtime home:    ~/.hermes
```

### 5. Validate attach/runtime contracts

For Studio54 personas, validate without automatic mutation first:

```bash
./bin/hermes-grid --check
./bin/hermes-grid --check --probe-remote
./bin/hermes-grid attach <Persona> --dry-run
```

Live attach remains an explicit operator action only. Restore does not grant
Paperclip autonomy, GPU permission, prompt injection, service changes, package
installs, or firewall changes.

### 6. Promote only after rehearsal passes

Only after the temporary restore validates should an operator decide whether to
restore over a live `HERMES_HOME`. Stop gateways or services first if required
by the target host's runtime model, then restore, restart, and smoke test.

Post-restore checks:

```bash
hermes status
hermes profile list
hermes sessions stats
hermes memory status
hermes honcho status
```

Gateway-bearing personas should also run a messaging/gateway smoke test through
the approved channel. Record only redacted status and message IDs in ledgers.

## Persona Recovery Checklist

### Donna / Studio54 Hub

- Restore host-native Hermes runtime state.
- Validate `config.yaml`, provider selection, toolsets, skills, and sessions.
- Validate Honcho pointer and backend state separately.
- Validate gateway state without overwriting persona-specific systemd units.
- Confirm Studio54 repo is on clean `main` or an intended branch.
- Confirm hub topology commands still pass.

### Victoria / Cloud Persona

- Restore remote Hermes home on the Victoria host or recover from host backup.
- Validate SSH alias, tmux session/window, attach wrapper, and Hermes launcher.
- Confirm communication protocol and direct-control envelope still work.
- Keep Victoria's evidence in Agent Knowledge Exchange; keep reusable pattern in
  Studio54.

### Nikoli / WSL Workstation Persona

- Restore WSL/user Hermes state only with explicit operator approval.
- Validate `ssh nikoli`, `~/.local/bin/nikolai-attach`, and
  `nikolai-hermes:Nikolai` tmux markers.
- Validate GPU visibility only as metadata unless GPU work is separately
  approved.
- Confirm Paperclip/company autonomy remains a separate lab-charter gate.

### Sam / Android Termux Mobile Edge

- Treat as mobile-edge recovery, not VPS recovery.
- Validate SSH, Python, Termux package state, tmux availability, wake/reboot
  persistence, and Tailscale reconnect behavior.
- Do not install packages, enable Termux:Boot, or promote topology without
  separate approval.

### Paperclip Company-Local Hermes

- Restore company-local `HERMES_HOME`, Paperclip DB state, and Honcho workspace
  state together.
- Validate one bounded issue/task before restoring autonomy loops.
- Require structured report-back to Donna.

## Delegation and Forking Appendix

Hermes can launch work through several mechanisms. They are not interchangeable.

| Mechanism | What it does | Context behavior | Cost/runtime note | Use when |
|---|---|---|---|---|
| `delegate_task` | Synchronous Hermes-native child agent | Parent passes explicit goal/context/toolsets; only final summary returns | Uses configured Hermes/subagent provider/model unless overridden | Parallel research/review/implementation subtasks. |
| `delegate_task` batch | Multiple child agents in parallel | Each child receives only its task context | Bounded by delegation concurrency config | Independent workstreams. |
| Leaf subagent | Default child role | Cannot delegate further | Simpler governance | Focused work. |
| Orchestrator subagent | Child that may spawn children | Still needs explicit context | More complex/costly | Large decomposition when explicitly useful. |
| `/background` | Separate background Hermes session | Independent session; result returns later | Durable within Hermes background machinery | Long task while current session stays free. |
| `/branch` or `/fork` | Branch current session | Explores alternate path from session context | Useful for speculative paths | Try an idea without polluting mainline. |
| `hermes chat --worktree` | Isolated git worktree | Separate filesystem branch for coding | Reduces repo collisions | Parallel repo work. |
| `claude -p` / `claude --print` | Non-interactive Claude Code run | Prompt in, result out | Auth/cost depends on Claude Code configuration | One-shot coding/review tasks. |
| `codex exec` | Non-interactive Codex run | Prompt in, result out | Auth/cost depends on Codex configuration/profile | One-shot coding/review tasks. |

Delegation rules for Studio54 fleet work:

- Pass all relevant context explicitly: repo path, branch, files, constraints,
  safety rules, and output format.
- Prefer leaf subagents unless there is an explicit reason to allow nested
  orchestration.
- Do not let subagents perform side effects whose success you cannot verify.
- Verify any claimed file write, PR, URL, or external mutation from the parent.
- Use bounded toolsets where possible.
- Use docs/plan-only mode for backup/restore design until an operator approves
  live restore drills.

### Cost Boundary Checks for External Coding CLIs

`claude -p` and `codex exec` are useful forked-terminal/non-interactive modes,
but their billing source depends on each CLI's local authentication and profile
configuration.

Before using one for fleet operations, record redacted metadata:

```bash
claude auth    # if supported in the installed version
codex login status || true
codex --help
```

Do not assume a command uses a subscription plan instead of API billing unless
that has been verified for the specific host/profile. If there is a budget flag
available, use it for one-shot runs where practical.

## Validation Matrix

A restore is not complete until the relevant layers validate.

| Layer | Minimal validation | Must not expose |
|---|---|---|
| Hermes runtime | `hermes status`, `hermes profile list` | `.env`, `auth.json`, provider tokens |
| Sessions | `hermes sessions stats` or redacted export metadata | raw private conversation dumps |
| Skills | `hermes skills list` or repo docs scan | private scratchpads/secrets |
| Quick snapshot | `/snapshot` list or `state-snapshots` manifest metadata | snapshot file contents |
| Honcho | `hermes honcho status`, memory smoke | raw observations, DB contents, API keys |
| Gateway | service status and message smoke | raw logs, pairing secrets, tokens |
| Studio54 topology | grid check/probe/dry-run | Tailnet IPs, raw tmux transcripts |
| Paperclip | bounded issue/task status | DB dumps, API keys, private company data |

## Recommended PR Sequence

1. **This runbook**: document the backup/restore model and delegation appendix.
2. **Dry-run inventory script**: list what would be backed up and classify
   secret-bearing surfaces without printing values.
3. **Temporary-home restore rehearsal**: restore one backup into a scratch
   `HERMES_HOME` and validate metadata only.
4. **Honcho backup runbook**: add DB/volume backup and restore procedure for
   the self-hosted Honcho stack.
5. **Per-persona recovery cards**: Donna, Victoria, Nikoli, Sam, and future
   Paperclip company-local Hermes agents.
6. **Encrypted/off-host backup automation**: only after storage location,
   retention, and credential rotation policy are explicit.

## Redaction Statement

This runbook intentionally records commands, file classes, validation patterns,
and boundaries only. It does not include raw secrets, private keys, public key
lines, Tailnet IPs, public infrastructure IPs, raw logs, raw session databases,
raw memory stores, or backup archive contents.
