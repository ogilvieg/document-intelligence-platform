import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useRAGAnalysis, useSampleAnalysis } from "./hooks";
import type { RAGAnalysisResponse, SampleAnalysisResponse } from "./api-client";
import { secureApiClient } from "./secure-api-client";

vi.mock("./secure-api-client", () => ({
  secureApiClient: {
    analyzeWithRAG: vi.fn(),
    getSampleAnalysis: vi.fn(),
  },
}));

const analyzeWithRAG = vi.mocked(secureApiClient.analyzeWithRAG);
const getSampleAnalysis = vi.mocked(secureApiClient.getSampleAnalysis);

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

describe("useRAGAnalysis", () => {
  beforeEach(() => analyzeWithRAG.mockReset());

  it("prevents a duplicate submission while analysis is pending", async () => {
    const pending = deferred<RAGAnalysisResponse>();
    analyzeWithRAG.mockReturnValue(pending.promise);
    const { result } = renderHook(() => useRAGAnalysis());
    let first!: Promise<unknown>;
    let duplicate!: Promise<unknown>;

    act(() => {
      first = result.current.analyzeWithRAG("First query");
      duplicate = result.current.analyzeWithRAG("Duplicate query");
    });

    const callCount = analyzeWithRAG.mock.calls.length;
    await act(async () => {
      pending.resolve({} as RAGAnalysisResponse);
      await Promise.all([first, duplicate]);
    });
    expect(callCount).toBe(1);
  });

  it("ignores an invalidated response after reset and a newer request", async () => {
    const stale = deferred<RAGAnalysisResponse>();
    const current = deferred<RAGAnalysisResponse>();
    analyzeWithRAG
      .mockReturnValueOnce(stale.promise)
      .mockReturnValueOnce(current.promise);
    const { result } = renderHook(() => useRAGAnalysis());

    act(() => void result.current.analyzeWithRAG("Stale query"));
    act(() => result.current.resetAnalysis());
    act(() => void result.current.analyzeWithRAG("Current query"));

    await act(async () => {
      current.resolve({ query: "Current query" } as RAGAnalysisResponse);
      await current.promise;
    });
    await act(async () => {
      stale.resolve({ query: "Stale query" } as RAGAnalysisResponse);
      await stale.promise;
    });

    expect(result.current.analysisResult?.query).toBe("Current query");
  });

  it("preserves a prior success when a repeat analysis fails", async () => {
    analyzeWithRAG
      .mockResolvedValueOnce({ query: "Successful query" } as RAGAnalysisResponse)
      .mockRejectedValueOnce(new Error("Repeat failed"));
    const { result } = renderHook(() => useRAGAnalysis());

    await act(async () => {
      await result.current.analyzeWithRAG("Successful query");
    });
    await act(async () => {
      await result.current.analyzeWithRAG("Repeat query");
    });

    expect(result.current.analysisResult?.query).toBe("Successful query");
    expect(result.current.analysisError).toBe("Repeat failed");
  });
});

describe("useSampleAnalysis", () => {
  beforeEach(() => getSampleAnalysis.mockReset());

  it("reports a failed load and succeeds when retried", async () => {
    const sample = { analysis: { query: "Sample query" } } as SampleAnalysisResponse;
    getSampleAnalysis
      .mockRejectedValueOnce(new Error("Backend is waking up"))
      .mockResolvedValueOnce(sample);
    const { result } = renderHook(() => useSampleAnalysis());

    await act(async () => void (await result.current.loadSample()));
    expect(result.current.sampleError).toBe("Backend is waking up");

    await act(async () => void (await result.current.loadSample()));
    expect(result.current.sampleResult).toBe(sample);
    expect(result.current.sampleError).toBeNull();
  });

  it("ignores a late response after reset", async () => {
    const pending = deferred<SampleAnalysisResponse>();
    getSampleAnalysis.mockReturnValue(pending.promise);
    const { result } = renderHook(() => useSampleAnalysis());

    act(() => void result.current.loadSample());
    act(() => result.current.resetSample());
    await act(async () => {
      pending.resolve({ analysis: { query: "Late" } } as SampleAnalysisResponse);
      await pending.promise;
    });

    expect(result.current.sampleResult).toBeNull();
    expect(result.current.isSampleLoading).toBe(false);
  });
});
