import { describe, expect, it, vi } from "vitest";

const detectPortMock = vi.fn();

vi.mock("detect-port", () => ({
  default: detectPortMock,
}));

describe("detectListenPort", () => {
  it("checks availability on the configured host", async () => {
    detectPortMock.mockResolvedValueOnce(3100);

    const { detectListenPort } = await import("../index.js");
    const port = await detectListenPort("127.0.0.1", 3100);

    expect(port).toBe(3100);
    expect(detectPortMock).toHaveBeenCalledWith({ port: 3100, hostname: "127.0.0.1" });
  });
});
