# Operator Initialization Flow

Defines the intended first-human initialization flow for operator-owned services
on the Donna / Studio54 reference node.

This document exists because some services should be bootstrapped to a ready
state without the repo silently creating the first human owner account. The
reference node should automate infrastructure readiness, not hide operator
identity bootstrap inside generated secrets.

Related documents:

- Live node inventory: [donna-vps-service-map.md](donna-vps-service-map.md)
- Reference-node target: [reference-node-target.md](reference-node-target.md)
- Hermes bootstrap contract: [hermes-bootstrap.md](hermes-bootstrap.md)

## Principle

Automate:

- packages
- containers
- volumes
- private ingress
- health checks
- service readiness

Do not auto-own:

- the first human `n8n` account
- the first human Open WebUI admin account
- API keys that can only be created meaningfully after that human owner exists

In short:

- machine bootstrap should be reproducible
- operator identity bootstrap should be explicit and human-owned

## Services Covered

The current operator-owned initialization rule applies to:

- `n8n`
- Open WebUI

And it affects:

- `n8n-mcp`, because it depends on an `n8n` API key that is normally created
  by the operator inside the `n8n` UI

## n8n Contract

The correct `n8n` lifecycle on the reference node is:

1. deploy `n8n`
2. open the `n8n` UI
3. create the first owner/admin account manually
4. generate an API key from inside `n8n`
5. place that API key into the local runtime config
6. restart or enable dependent tooling such as `n8n-mcp`

This means the repo should not assume:

- a hidden deterministic first owner
- a pre-generated `N8N_API_KEY`
- direct database seeding of the first human identity as the default path

### What belongs in `.env`

For `n8n`, `.env` should contain:

- `N8N_ENCRYPTION_KEY`
- `N8N_USER_MANAGEMENT_JWT_SECRET`
- `N8N_MCP_AUTH_TOKEN`
- blank `N8N_API_KEY` until the operator generates one

The first-owner identity fields may exist only as optional helper fields for
legacy bootstrap tooling. They are not the preferred initialization path.

## Open WebUI Contract

The correct Open WebUI lifecycle on the reference node is:

1. deploy Open WebUI
2. open the UI
3. complete the first-run admin signup manually
4. generate any API keys from inside the UI if needed

The repo should not assume:

- a hidden deterministic first admin
- direct SQLite mutation as the default path

### What belongs in `.env`

For Open WebUI, `.env` should contain:

- image selection and general service config
- blank owner/admin identity fields by default
- blank `OPEN_WEBUI_API_KEY` unless the operator creates one

The admin identity fields may exist only as optional helper fields for legacy
bootstrap tooling. They are not the preferred initialization path.

## n8n-mcp Dependency Rule

`n8n-mcp` depends on a real `n8n` API key.

That key normally cannot exist until after:

- the operator creates the `n8n` owner/admin account
- the operator logs into the `n8n` UI
- the operator generates the key from the `n8n` settings UI

Therefore the intended initialization order is:

1. bring up `n8n`
2. operator creates the first owner
3. operator generates the API key
4. write `N8N_API_KEY` into the local env/config
5. verify or restart `n8n-mcp`

## Legacy Helper Scripts

The repo currently contains older helper scripts that can directly seed owner
or admin state:

- `stack/prototype-local/scripts/bootstrap_n8n.py`
- `stack/prototype-local/scripts/sync_openwebui_functions.py`

Those scripts should now be treated as legacy or specialized helpers, not the
default initialization path for the reference node.

Their default mental model is wrong for Donna because they collapse:

- infrastructure readiness
- first human ownership
- post-login function/workflow wiring

into one step.

The reference-node policy should keep those concerns separate.

## Definition Of Done

The operator initialization flow is considered defined when:

1. `.env.example` no longer implies hidden first-owner credentials are required
2. `init_env.py` does not auto-generate those credentials by default
3. docs describe a manual first-login flow for `n8n` and Open WebUI
4. `n8n-mcp` is documented as depending on the manually generated `n8n` API key
5. any legacy scripts are clearly marked as non-default helper paths
