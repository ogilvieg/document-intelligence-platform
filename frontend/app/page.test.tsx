import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "./page";
import {
  useBackendHealth,
  useDocumentUpload,
  useRAGAnalysis,
  useSampleAnalysis,
} from "@/lib/hooks";
import type { SampleAnalysisResponse } from "@/lib/api-client";

vi.mock("@/lib/hooks", () => ({
  useBackendHealth: vi.fn(),
  useDocumentUpload: vi.fn(),
  useRAGAnalysis: vi.fn(),
  useSampleAnalysis: vi.fn(),
}));

const mockedUseBackendHealth = vi.mocked(useBackendHealth);
const mockedUseDocumentUpload = vi.mocked(useDocumentUpload);
const mockedUseRAGAnalysis = vi.mocked(useRAGAnalysis);
const mockedUseSampleAnalysis = vi.mocked(useSampleAnalysis);

const sampleResponse = {
  sample: {
    synthetic: true,
    fixture_version: "v1",
    title: "Synthetic Agreement",
    description: "Precomputed fictional example.",
    metrics_are_representative: true,
  },
  analysis: {
    analysis_id: "sample-1",
    query: "Review risks",
    output: {
      overall_fit: "Needs revision.", strengths: ["Clear fees"], gaps: ["No cure period"],
      risk_factors: ["Uncapped liability"], confidence: 0.8, recommended_focus: ["Add a cap"],
    },
    citations: [{ chunk_id: "c1", document_id: "sample-doc", document_title: "Synthetic Agreement (Sample)", chunk_text: "Termination text", relevance_score: 0.9 }],
    retrieved_chunks: [{ chunk_id: "c1", document_id: "sample-doc", document_title: "Synthetic Agreement (Sample)", doc_type: "pdf", chunk_index: 1, text: "Termination text", similarity_score: 0.9 }],
    retrieval_metadata: { chunks_retrieved: 1, query_embedding_model: "example-model", retrieval_timestamp: "2026-08-20T00:00:00Z", filters_applied: { document_ids: ["sample-doc"] } },
    llm_metadata: { model: "example-model", temperature: 0, latency_ms: 100, prompt_tokens: 100, completion_tokens: 20, total_tokens: 120, cost_usd: 0.002 },
    cost: 0.002,
    created_at: "2026-08-20T00:00:01Z",
  },
} satisfies SampleAnalysisResponse;

describe("Home", () => {
  beforeEach(() => {
    mockedUseBackendHealth.mockReturnValue({
      status: "connecting",
      retry: vi.fn(),
    });
    mockedUseDocumentUpload.mockReturnValue({
      upload: vi.fn(),
      isUploading: false,
      uploadError: null,
      uploadedDocument: null,
      resetUpload: vi.fn(),
    });
    mockedUseRAGAnalysis.mockReturnValue({
      analyzeWithRAG: vi.fn(),
      isAnalyzing: false,
      analysisError: null,
      analysisResult: null,
      resetAnalysis: vi.fn(),
    });
    mockedUseSampleAnalysis.mockReturnValue({
      loadSample: vi.fn(),
      isSampleLoading: false,
      sampleError: null,
      sampleResult: null,
      resetSample: vi.fn(),
    });
  });

  it("describes the public AI stack without naming a model version", () => {
    render(<Home />);

    expect(document.body.textContent).not.toMatch(/gpt-?\d/i);
    expect(document.body.textContent).toMatch(/openai/i);
  });

  it("does not report online before a successful health signal", () => {
    render(<Home />);

    const status = screen.getByRole("status");
    expect(status.textContent).toMatch(/connecting/i);
    expect(status.textContent).not.toMatch(/online/i);
  });

  it("explains a delayed health probe as possible Render startup", () => {
    mockedUseBackendHealth.mockReturnValue({
      status: "delayed",
      retry: vi.fn(),
    });

    render(<Home />);

    const status = screen.getByRole("status");
    expect(status.textContent).toMatch(/delayed/i);
    expect(status.textContent).toMatch(/render/i);
  });

  it("lets a visitor retry an unavailable health probe", async () => {
    const retry = vi.fn();
    mockedUseBackendHealth.mockReturnValue({ status: "unavailable", retry });

    render(<Home />);
    await userEvent.click(
      screen.getByRole("button", { name: /retry api connection/i }),
    );

    expect(retry).toHaveBeenCalledOnce();
  });

  it("keeps the ask-and-verify benefit after supporting details are dismissed", async () => {
    render(<Home />);
    const benefit = screen.getByRole("heading", {
      level: 1,
      name: /ask.*verify/i,
    });

    expect(screen.getByText(/01.*ingest/i)).toBeTruthy();
    await userEvent.click(
      screen.getByRole("button", { name: /dismiss introduction/i }),
    );

    expect(benefit.isConnected).toBe(true);
  });

  it("links technical evaluators to the project evidence", () => {
    render(<Home />);

    const expectedLinks = [
      [
        /source code/i,
        "https://github.com/ogilvieg/document-intelligence-platform",
      ],
      [
        /project brief/i,
        "https://github.com/ogilvieg/document-intelligence-platform/blob/main/DEMO.md",
      ],
      [/api documentation/i, "https://docsage-api.phoenix7.dev/docs"],
      [
        /architecture/i,
        "https://github.com/ogilvieg/document-intelligence-platform#architecture-overview",
      ],
    ] as const;

    for (const [name, href] of expectedLinks) {
      expect(screen.getByRole("link", { name }).getAttribute("href")).toBe(
        href,
      );
    }
  });

  it("offers a zero-risk sample and renders it as synthetic representative data", async () => {
    const loadSample = vi.fn().mockResolvedValue(sampleResponse);
    mockedUseSampleAnalysis.mockReturnValue({
      loadSample,
      isSampleLoading: false,
      sampleError: null,
      sampleResult: sampleResponse,
      resetSample: vi.fn(),
    });

    render(<Home />);
    await userEvent.click(screen.getByRole("button", { name: /try a sample document/i }));

    expect(loadSample).toHaveBeenCalledOnce();
    expect(screen.getAllByText(/synthetic sample/i).length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/representative.*not a live run/i)).toBeTruthy();
    expect(screen.getByText(sampleResponse.analysis.query)).toBeTruthy();
    expect(mockedUseDocumentUpload().upload).not.toHaveBeenCalled();
    expect(mockedUseRAGAnalysis().analyzeWithRAG).not.toHaveBeenCalled();
  });

  it("keeps upload available and supports retry when the sample backend is unavailable", async () => {
    const loadSample = vi.fn();
    mockedUseSampleAnalysis.mockReturnValue({
      loadSample,
      isSampleLoading: false,
      sampleError: "Backend is waking up",
      sampleResult: null,
      resetSample: vi.fn(),
    });

    const { container } = render(<Home />);
    expect(screen.getByRole("alert").textContent).toMatch(/backend is waking up/i);
    expect(container.querySelector('input[type="file"]')).not.toBeNull();
    await userEvent.click(screen.getByRole("button", { name: /retry sample/i }));
    expect(loadSample).toHaveBeenCalledOnce();
  });

  it("clears sample state before transitioning to a real upload", async () => {
    const resetSample = vi.fn();
    const upload = vi.fn().mockResolvedValue(null);
    mockedUseSampleAnalysis.mockReturnValue({
      loadSample: vi.fn(), isSampleLoading: false, sampleError: null,
      sampleResult: sampleResponse, resetSample,
    });
    mockedUseDocumentUpload.mockReturnValue({
      upload, isUploading: false, uploadError: null, uploadedDocument: null, resetUpload: vi.fn(),
    });
    const { container } = render(<Home />);

    await userEvent.upload(
      container.querySelector('input[type="file"]') as HTMLInputElement,
      new File(["document"], "mine.txt", { type: "text/plain" }),
    );

    expect(resetSample).toHaveBeenCalledOnce();
    expect(resetSample.mock.invocationCallOrder[0]).toBeLessThan(upload.mock.invocationCallOrder[0]);
  });

  it("clears sample state before a dropped file is uploaded", async () => {
    const resetSample = vi.fn();
    const upload = vi.fn().mockResolvedValue(null);
    mockedUseSampleAnalysis.mockReturnValue({
      loadSample: vi.fn(), isSampleLoading: false, sampleError: null,
      sampleResult: sampleResponse, resetSample,
    });
    mockedUseDocumentUpload.mockReturnValue({
      upload, isUploading: false, uploadError: null, uploadedDocument: null, resetUpload: vi.fn(),
    });
    const { container } = render(<Home />);
    const dropZone = container.querySelector('input[type="file"]')?.parentElement as HTMLElement;

    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [new File(["document"], "dropped.txt", { type: "text/plain" })],
      },
    });

    expect(dropZone).toBeTruthy();
    expect(resetSample.mock.invocationCallOrder[0]).toBeLessThan(upload.mock.invocationCallOrder[0]);
  });

  it("shows the persistence boundary and confidentiality warning before selection", () => {
    render(<Home />);

    expect(screen.getByText(/original file.*processed in memory.*not retained/i)).toBeTruthy();
    expect(screen.getByText(/extracted text.*chunks.*embeddings.*stored/i)).toBeTruthy();
    expect(screen.getByText(/do not upload confidential material/i)).toBeTruthy();
  });

  it("renders the client page with analysis unavailable before upload", () => {
    render(<Home />);

    expect(screen.getByRole("heading", { level: 1 })).toBeTruthy();
    expect(
      screen.getByRole("button", { name: /run analysis/i }).hasAttribute(
        "disabled",
      ),
    ).toBe(true);
  });

  it("scopes the homepage analysis to the active uploaded document", async () => {
    const analyzeWithRAG = vi.fn().mockResolvedValue(null);
    mockedUseDocumentUpload.mockReturnValue({
      upload: vi.fn(),
      isUploading: false,
      uploadError: null,
      uploadedDocument: {
        id: "document-123",
        title: "Example",
        type: "pdf",
        source: null,
        version: "1",
        created_at: "2026-08-20T00:00:00Z",
        metadata: {
          original_filename: "example.pdf",
          text_length: 1200,
          parser: "pdfplumber",
          content_type: "application/pdf",
        },
      },
      resetUpload: vi.fn(),
    });
    mockedUseRAGAnalysis.mockReturnValue({
      analyzeWithRAG,
      isAnalyzing: false,
      analysisError: null,
      analysisResult: null,
      resetAnalysis: vi.fn(),
    });

    render(<Home />);
    await userEvent.click(
      screen.getByRole("button", { name: /run analysis/i }),
    );

    expect(analyzeWithRAG).toHaveBeenCalledWith(expect.any(String), {
      document_ids: ["document-123"],
      similarity_threshold: 0.3,
      temperature: 0.7,
      top_k: 5,
    });
  });

  it("invalidates an active analysis before replacing the document", async () => {
    const resetAnalysis = vi.fn();
    const upload = vi.fn().mockResolvedValue(null);
    mockedUseDocumentUpload.mockReturnValue({
      upload,
      isUploading: false,
      uploadError: null,
      uploadedDocument: null,
      resetUpload: vi.fn(),
    });
    mockedUseRAGAnalysis.mockReturnValue({
      analyzeWithRAG: vi.fn(),
      isAnalyzing: false,
      analysisError: null,
      analysisResult: null,
      resetAnalysis,
    });
    const { container } = render(<Home />);
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;

    await userEvent.upload(
      input,
      new File(["document"], "replacement.txt", { type: "text/plain" }),
    );

    expect(resetAnalysis).toHaveBeenCalledOnce();
    expect(upload).toHaveBeenCalledOnce();
  });
});
