import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Home from "./page";
import { useDocumentUpload, useRAGAnalysis } from "@/lib/hooks";

vi.mock("@/lib/hooks", () => ({
  useDocumentUpload: vi.fn(),
  useRAGAnalysis: vi.fn(),
}));

const mockedUseDocumentUpload = vi.mocked(useDocumentUpload);
const mockedUseRAGAnalysis = vi.mocked(useRAGAnalysis);

describe("Home", () => {
  beforeEach(() => {
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
