import { describe, expect, it } from "vitest";

import { cleanResponse } from "../../../../hermes-paperclip-adapter/src/server/execute.js";

describe("Hermes adapter response cleaning", () => {
  it("removes runtime diagnostics without stripping task comments", () => {
    const cleaned = cleanResponse(`
⚠ No auxiliary LLM provider configured — context compression will drop middle turns without a summary. Run \`hermes setup\` or set OPENROUTER_API_KEY.
↻ Resumed session 20260426_084939_50c597 (2 user messages, 20 total messages)
PENDING: Waiting for child issue(s) to complete before closing this parent.

DONE: useful synthesis
`);

    expect(cleaned).not.toContain("No auxiliary LLM provider configured");
    expect(cleaned).not.toContain("Resumed session");
    expect(cleaned).toContain("PENDING: Waiting for child issue(s)");
    expect(cleaned).toContain("DONE: useful synthesis");
  });

  it("preserves explicit task failure summaries", () => {
    const cleaned = cleanResponse(`
⚠ No auxiliary LLM provider configured — context compression will drop middle turns without a summary.
FAILED: Could not complete the task because the required repository snapshot is missing.
`);

    expect(cleaned).toBe("FAILED: Could not complete the task because the required repository snapshot is missing.");
  });
});
