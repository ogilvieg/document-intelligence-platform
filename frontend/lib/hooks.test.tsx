import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  probeBackendHealth,
  useBackendHealth,
  useRAGAnalysis,
  useSampleAnalysis,
} from "./hooks";
import type {
  HealthResponse,
  RAGAnalysisResponse,
  SampleAnalysisResponse,
} from "./api-client";
import { secureApiClient } from "./secure-api-client";

vi.mock("./secure-api-client", () => ({
  secureApiClient: {
    analyzeWithRAG: vi.fn(),
    checkHealth: vi.fn(),
    getSampleAnalysis: vi.fn(),
  },
}));

const analyzeWithRAG = vi.mocked(secureApiClient.analyzeWithRAG);
const checkHealth = vi.mocked(secureApiClient.checkHealth);
const getSampleAnalysis = vi.mocked(secureApiClient.getSampleAnalysis);

afterEach(() => {
  vi.useRealTimers();
});

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

describe("useBackendHealth", () => {
  beforeEach(() => checkHealth.mockReset());

  it("reports online only after the initial health probe succeeds", async () => {
    const pending = deferred<HealthResponse>();
    checkHealth.mockReturnValue(pending.promise);
    const { result } = renderHook(() => useBackendHealth());

    expect(result.current.status).toBe("connecting");
    await act(async () => {
      pending.resolve({ status: "healthy" } as HealthResponse);
      await pending.promise;
    });
    await waitFor(() => expect(result.current.status).toBe("online"));
  });

  it("reports a delayed probe and still accepts its later success", async () => {
    vi.useFakeTimers();
    const pending = deferred<HealthResponse>();
    checkHealth.mockReturnValue(pending.promise);
    const { result } = renderHook(() => useBackendHealth());

    act(() => vi.advanceTimersByTime(5_000));
    expect(result.current.status).toBe("delayed");
    await act(async () => {
      pending.resolve({ status: "healthy" } as HealthResponse);
      await pending.promise;
    });
    expect(result.current.status).toBe("online");
  });

  it("classifies a failed health probe as unavailable", async () => {
    const status = await probeBackendHealth(async () => {
      throw new Error("Backend unavailable");
    });
    expect(status).toBe("unavailable");
  });

  it("retries an unavailable probe through connecting to online", async () => {
    const retryResult = deferred<"online" | "unavailable">();
    const probe = vi
      .fn()
      .mockResolvedValueOnce("unavailable")
      .mockReturnValueOnce(retryResult.promise);
    const { result } = renderHook(() => useBackendHealth(probe));
    await waitFor(() => expect(result.current.status).toBe("unavailable"));

    act(() => void result.current.retry());
    expect(result.current.status).toBe("connecting");
    await act(async () => {
      retryResult.resolve("online");
      await retryResult.promise;
    });
    expect(result.current.status).toBe("online");
  });

  it("ignores a stale probe after a retry succeeds", async () => {
    const stale = deferred<"online" | "unavailable">();
    const current = deferred<"online" | "unavailable">();
    const probe = vi
      .fn()
      .mockReturnValueOnce(stale.promise)
      .mockReturnValueOnce(current.promise);
    const { result } = renderHook(() => useBackendHealth(probe));

    await waitFor(() => expect(probe).toHaveBeenCalledOnce());
    act(() => void result.current.retry());
    await act(async () => {
      current.resolve("online");
      await current.promise;
    });
    await act(async () => {
      stale.resolve("unavailable");
      await stale.promise;
    });

    expect(result.current.status).toBe("online");
  });

  it("aborts an in-flight probe on unmount", async () => {
    const probe = vi.fn((signal: AbortSignal) => {
      void signal;
      return new Promise<never>(() => {});
    });
    const { unmount } = renderHook(() => useBackendHealth(probe));
    await waitFor(() => expect(probe).toHaveBeenCalledOnce());
    const signal = probe.mock.calls[0][0];

    expect(signal).toBeInstanceOf(AbortSignal);
    expect(signal.aborted).toBe(false);
    unmount();
    expect(signal.aborted).toBe(true);
  });
});

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
