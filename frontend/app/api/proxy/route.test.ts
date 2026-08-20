import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { POST } from "./route";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("POST /api/proxy", () => {
  it("preserves explicit zero values when forwarding JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ analysis_id: "analysis-1" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const request = new NextRequest(
      "http://localhost/api/proxy?endpoint=/analyze-rag",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: "Inspect this document",
          top_k: 0,
          similarity_threshold: 0.0,
          temperature: 0.0,
        }),
      },
    );

    const response = await POST(request);

    expect(response.status).toBe(200);
    const forwarded = JSON.parse(
      String((fetchMock.mock.calls[0][1] as RequestInit).body),
    ) as Record<string, unknown>;
    expect(forwarded.top_k).toBe(0);
    expect(forwarded.similarity_threshold).toBe(0.0);
    expect(forwarded.temperature).toBe(0.0);
  });
});
