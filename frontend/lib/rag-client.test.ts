import { afterEach, describe, expect, it, vi } from "vitest";

import { APIClient } from "./api-client";
import { SecureAPIClient } from "./secure-api-client";

function successfulResponse(body: unknown = {}): Response {
  return {
    ok: true,
    json: vi.fn().mockResolvedValue(body),
  } as unknown as Response;
}

function requestBody(fetchMock: ReturnType<typeof vi.fn>) {
  const init = fetchMock.mock.calls[0][1] as RequestInit;
  return JSON.parse(String(init.body)) as Record<string, unknown>;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe.each([
  ["direct client", () => new APIClient("https://api.example.test/api/v1")],
  ["secure proxy client", () => new SecureAPIClient()],
])("%s RAG contract", (_name, createClient) => {
  it("forwards an arbitrary query without requiring optional filters", async () => {
    const fetchMock = vi.fn().mockResolvedValue(successfulResponse());
    vi.stubGlobal("fetch", fetchMock);

    await createClient().analyzeWithRAG("Compare the termination clauses");

    const body = requestBody(fetchMock);
    expect(body.query).toBe("Compare the termination clauses");
    expect("document_ids" in body).toBe(false);
    expect("doc_type" in body).toBe(false);
  });

  it("preserves explicit zero-valued retrieval and generation options", async () => {
    const fetchMock = vi.fn().mockResolvedValue(successfulResponse());
    vi.stubGlobal("fetch", fetchMock);

    await createClient().analyzeWithRAG("Inspect this document", {
      top_k: 0,
      similarity_threshold: 0.0,
      temperature: 0.0,
    });

    const body = requestBody(fetchMock);
    expect(body.top_k).toBe(0);
    expect(body.similarity_threshold).toBe(0.0);
    expect(body.temperature).toBe(0.0);
  });

  it("returns every field in the backend RAG response contract", async () => {
    const backendResponse = {
      analysis_id: "analysis-1",
      query: "Inspect this document",
      output: {
        overall_fit: "Fit",
        strengths: ["Strength"],
        gaps: ["Gap"],
        risk_factors: ["Risk"],
        confidence: 0.8,
        recommended_focus: ["Focus"],
      },
      citations: [{ chunk_id: "chunk-1" }],
      retrieved_chunks: [{ chunk_id: "chunk-1", metadata: { page: 1 } }],
      retrieval_metadata: {
        chunks_retrieved: 1,
        query_embedding_model: "embedding-model",
        retrieval_timestamp: "2026-08-20T20:00:00Z",
        filters_applied: { document_ids: ["document-1"] },
      },
      llm_metadata: {
        model: "model-name",
        temperature: 0,
        latency_ms: 1000,
        prompt_tokens: 100,
        completion_tokens: 20,
        total_tokens: 120,
        cost_usd: 0.002,
      },
      cost: 0.002,
      created_at: "2026-08-20T20:00:02Z",
    };
    const fetchMock = vi.fn().mockResolvedValue(successfulResponse(backendResponse));
    vi.stubGlobal("fetch", fetchMock);

    const result = await createClient().analyzeWithRAG(backendResponse.query);

    expect(result.query).toBe(backendResponse.query);
    expect(result.output.strengths[0]).toBe("Strength");
    expect(result.citations[0].chunk_id).toBe("chunk-1");
    expect(result.retrieved_chunks?.[0].metadata?.page).toBe(1);
    expect(result.retrieval_metadata.retrieval_timestamp).toBe(
      backendResponse.retrieval_metadata.retrieval_timestamp,
    );
    expect(result.retrieval_metadata.filters_applied?.document_ids).toEqual([
      "document-1",
    ]);
    expect(result.llm_metadata.latency_ms).toBe(1000);
    expect(result.llm_metadata.cost_usd).toBe(0.002);
    expect(result.cost).toBe(0.002);
    expect(result.created_at).toBe(backendResponse.created_at);
  });
});

describe("sample analysis contract", () => {
  it("fetches the precomputed sample through the secure GET proxy", async () => {
    const payload = { sample: { synthetic: true }, analysis: { query: "Risk review" } };
    const fetchMock = vi.fn().mockResolvedValue(successfulResponse(payload));
    vi.stubGlobal("fetch", fetchMock);

    const result = await new SecureAPIClient().getSampleAnalysis();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/proxy?endpoint=/sample-analysis",
    );
    expect(result).toEqual(payload);
  });
});
