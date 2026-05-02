You are extracting verifiable claims from a markdown document. Your output
will be merged into a structured ledger and verified against the codebase
and a live system. Precision matters more than recall — a missed claim is
fine, a hallucinated claim wastes the human reviewer's time.

## What is a claim

Emit one entry for each:

1. **Concrete fact:** a string, number, ID, path, port, container name,
   service name, version, command name, env var name, or file existence
   assertion.
2. **Behavioral assertion:** a testable statement of the form "X causes Y"
   or "running command Z produces output W" or "service P depends on Q".

## What is NOT a claim

Skip:
- Philosophy, motivation, rationale ("we believe in...", "the goal is...")
- Anything you'd have to infer from context
- Aspirational or future-tense statements ("will eventually...", "should...")
- Architectural-role statements ("Hermes is the tier-0 agent")

## Output format

Emit a YAML document. One entry per claim. No prose, no markdown, just YAML.

    claims:
      - source_line: 12          # 1-indexed line in the input
        claim_type: concrete     # concrete | behavioral
        subtype: port            # short tag: port, path, env_var, container_name, etc.
        claim_text: "Postgres listens on port 5432"
        expected_value: 5432
        verifiable_by: [code, vps]
        probe: null              # optional shell command for behavioral claims

If the document has no extractable claims, emit:

    claims: []

## Rules

- `source_line` must match the actual line in the input, 1-indexed.
- `expected_value` is the smallest concrete value the claim asserts (a
  number, string, bool, or short list). For behavioral claims, set it to
  the assertion's predicate (e.g., "auto-creates owner on first boot").
- `verifiable_by` lists which sources COULD verify this — `doc` (the doc
  itself), `code` (the repo), `vps` (the running system). Use your
  judgment; the human reviewer will fix mistakes.
- For `probe` on behavioral claims: only fill it in if you can write a
  short, safe, non-destructive shell command that would reveal the answer.
  Otherwise leave as null.
- Do NOT emit `id`, `owner`, `source_file`, or `seen_in` — the driver
  fills those in.
