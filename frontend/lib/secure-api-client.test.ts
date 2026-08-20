import { afterEach, describe, expect, it, vi } from "vitest";

import { SecureAPIClient } from "./secure-api-client";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("SecureAPIClient.checkHealth", () => {
  it("accepts a healthy response from the focused same-origin route", async () => {
    const health = {
      status: "healthy",
      version: "1.0.0",
      timestamp: "2026-08-20T00:00:00Z",
    };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(health), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(new SecureAPIClient().checkHealth()).resolves.toEqual(health);
    expect(fetchMock).toHaveBeenCalledWith("/api/health", {
      cache: "no-store",
    });
  });

  it("rejects a successful response that does not report healthy", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "degraded" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    await expect(new SecureAPIClient().checkHealth()).rejects.toThrow(
      /invalid health response/i,
    );
  });
});
