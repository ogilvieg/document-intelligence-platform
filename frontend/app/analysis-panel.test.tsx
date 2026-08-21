import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { RAGAnalysisResponse } from "@/lib/api-client";
import { AnalysisPanel } from "./page";

const response: RAGAnalysisResponse = {
  analysis_id: "analysis-1",
  query: "Compare the termination risks.",
  output: {
    overall_fit: "Material risks need review.",
    strengths: ["Clear notice period"],
    gaps: ["No cure period"],
    risk_factors: ["Broad indemnity"],
    confidence: 0.84,
    recommended_focus: ["Negotiate liability cap"],
  },
  citations: [
    {
      chunk_id: "chunk-1",
      document_id: "document-1",
      document_title: "Agreement",
      chunk_text: "Either party may terminate...",
      relevance_score: 0.92,
    },
  ],
  retrieved_chunks: [
    {
      chunk_id: "chunk-1",
      document_id: "document-1",
      document_title: "Agreement",
      doc_type: "pdf",
      chunk_index: 2,
      text: "Either party may terminate...",
      similarity_score: 0.92,
      metadata: { page: 4 },
    },
  ],
  retrieval_metadata: {
    chunks_retrieved: 1,
    query_embedding_model: "embedding-model",
    retrieval_timestamp: "2026-08-20T20:00:00Z",
    filters_applied: { document_ids: ["document-1"] },
  },
  llm_metadata: {
    model: "model-name",
    temperature: 0,
    latency_ms: 1234,
    prompt_tokens: 100,
    completion_tokens: 25,
    total_tokens: 125,
    cost_usd: 0.002,
  },
  cost: 0.002,
  created_at: "2026-08-20T20:00:02Z",
};

describe("AnalysisPanel", () => {
  it("exposes the analysis region and its evidence sections as headings", () => {
    render(<AnalysisPanel analysisResult={response} />);

    expect(screen.getByRole("heading", { level: 2, name: /analysis/i })).toBeTruthy();
    for (const name of [
      /retrieval pipeline/i,
      /retrieved chunks/i,
      /overall assessment/i,
      /strengths/i,
      /gaps/i,
      /risk factors/i,
      /focus areas/i,
      /source citations/i,
    ]) {
      expect(screen.getByRole("heading", { level: 3, name })).toBeTruthy();
    }
  });

  it("exposes responsive layout regions for result evidence", () => {
    const { container } = render(<AnalysisPanel analysisResult={response} />);

    for (const selector of [
      ".retrieval-stats",
      ".result-quadrants",
      ".citation-list",
    ]) {
      expect(container.querySelector(selector), selector).not.toBeNull();
    }
  });

  it("labels the completed result with the backend-echoed query", () => {
    render(<AnalysisPanel analysisResult={response} />);

    expect(screen.getByText(response.query)).toBeTruthy();
  });

  it("retains retrieval, generation, cost, and creation evidence", async () => {
    render(<AnalysisPanel analysisResult={response} />);
    const toggle = screen.getByRole("button", {
      name: /expand retrieval details/i,
    });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    expect(toggle.getAttribute("aria-controls")).toBe("retrieval-details");

    toggle.focus();
    await userEvent.keyboard("{Enter}");
    expect(toggle.getAttribute("aria-expanded")).toBe("true");

    for (const value of [
      response.retrieval_metadata.retrieval_timestamp,
      String(response.llm_metadata.latency_ms),
      response.created_at,
    ]) {
      expect(screen.getByText(value, { exact: false })).toBeTruthy();
    }
  });
});
