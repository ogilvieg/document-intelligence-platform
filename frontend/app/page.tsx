"use client";

import {
  useState,
  useRef,
  useCallback,
  useEffect,
  startTransition,
  memo,
} from "react";
import {
  useBackendHealth,
  useDocumentUpload,
  useRAGAnalysis,
  useSampleAnalysis,
} from "@/lib/hooks";
import {
  formatLatency,
  formatCost,
  RAGAnalysisResponse,
} from "@/lib/api-client";
import { PROJECT_LINKS } from "@/lib/project-links";
import { AnalysisComposer } from "./analysis-composer";

// ─── Inline style tokens ──────────────────────────────────────────────────────
const S = {
  mono: "var(--font-ibm-plex-mono)" as const,
  syne: "var(--font-special-elite)" as const,
  sans: "var(--font-ibm-plex-sans)" as const,
};

type DivStyle = React.CSSProperties;

const rule: DivStyle = {
  flex: 1,
  height: "1px",
  backgroundColor: "var(--border)",
};

function SectionLabel({ n, label }: { n: string; label: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        marginBottom: "20px",
      }}
    >
      <span
        style={{
          fontFamily: S.mono,
          fontSize: "10px",
          color: "var(--amber)",
          letterSpacing: "0.15em",
        }}
      >
        {n}
      </span>
      <span
        style={{
          fontFamily: S.syne,
          fontSize: "12px",
          fontWeight: 700,
          letterSpacing: "0.18em",
          textTransform: "uppercase",
          color: "var(--text-secondary)",
        }}
      >
        {label}
      </span>
      <div style={rule} />
    </div>
  );
}

function DataCell({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: string;
}) {
  return (
    <div>
      <p
        style={{
          fontFamily: S.mono,
          fontSize: "9px",
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.15em",
          marginBottom: "5px",
        }}
      >
        {label}
      </p>
      <p
        style={{
          fontFamily: S.mono,
          fontSize: "18px",
          color: accent ?? "var(--text-primary)",
          fontWeight: 400,
          letterSpacing: "-0.02em",
        }}
      >
        {value}
      </p>
    </div>
  );
}

function SignedList({
  items,
  sigil,
  color,
}: {
  items: string[];
  sigil: string;
  color: string;
}) {
  return (
    <ul style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
      {items.map((item, i) => (
        <li
          key={i}
          style={{
            fontSize: "13px",
            color: "var(--text-secondary)",
            paddingLeft: "18px",
            position: "relative",
            lineHeight: "1.6",
          }}
        >
          <span
            style={{
              position: "absolute",
              left: 0,
              color,
              fontFamily: S.mono,
              fontWeight: 500,
            }}
          >
            {sigil}
          </span>
          {item}
        </li>
      ))}
    </ul>
  );
}

// ─── Analysis Panel (memoised — doesn't re-render during upload interactions) ─
export const AnalysisPanel = memo(function AnalysisPanel({
  analysisResult,
}: {
  analysisResult: RAGAnalysisResponse;
}) {
  const [showRetrievalDetails, setShowRetrievalDetails] = useState(false);

  return (
    <div style={{ animation: "fadeInUp 0.4s ease forwards" }}>
      {/* Section header with cost summary */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          marginBottom: "20px",
        }}
      >
        <span
          style={{
            fontFamily: S.mono,
            fontSize: "10px",
            color: "var(--amber)",
            letterSpacing: "0.15em",
          }}
        >
          03
        </span>
        <span
          style={{
            fontFamily: S.syne,
            fontSize: "12px",
            fontWeight: 700,
            letterSpacing: "0.18em",
            textTransform: "uppercase",
            color: "var(--text-secondary)",
          }}
        >
          Analysis
        </span>
        <div style={rule} />
        <span
          style={{
            fontFamily: S.mono,
            fontSize: "10px",
            color: "var(--amber)",
            letterSpacing: "0.1em",
            flexShrink: 0,
          }}
        >
          {analysisResult.llm_metadata.total_tokens.toLocaleString()} tokens ·{" "}
          {formatCost(analysisResult.cost)}
        </span>
      </div>

      <div
        style={{
          marginBottom: "14px",
          borderLeft: "2px solid var(--amber)",
          padding: "12px 16px",
          backgroundColor: "var(--amber-dim)",
        }}
      >
        <p
          style={{
            fontFamily: S.mono,
            fontSize: "9px",
            color: "var(--text-muted)",
            textTransform: "uppercase",
            letterSpacing: "0.15em",
            marginBottom: "5px",
          }}
        >
          Completed goal
        </p>
        <p style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
          {analysisResult.query}
        </p>
      </div>

      {/* Retrieval Pipeline ─── */}
      <div
        style={{
          marginBottom: "14px",
          border: "1px solid var(--border-cyan)",
          backgroundColor: "var(--cyan-dim)",
          padding: "20px 24px",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "18px",
          }}
        >
          <p
            style={{
              fontFamily: S.mono,
              fontSize: "9px",
              color: "var(--cyan)",
              letterSpacing: "0.2em",
              textTransform: "uppercase",
            }}
          >
            Retrieval Pipeline
          </p>
          <button
            type="button"
            className="compact-action retrieval-toggle"
            aria-expanded={showRetrievalDetails}
            aria-controls="retrieval-details"
            aria-label={`${showRetrievalDetails ? "Collapse" : "Expand"} retrieval details`}
            onClick={() =>
              startTransition(() => setShowRetrievalDetails((prev) => !prev))
            }
            style={{
              fontFamily: S.mono,
              fontSize: "9px",
              color: "var(--text-muted)",
              cursor: "pointer",
              background: "none",
              border: "none",
              letterSpacing: "0.12em",
            }}
          >
            [{showRetrievalDetails ? "COLLAPSE" : "EXPAND"}]
          </button>
        </div>

        <div
          className="retrieval-stats"
          style={{
            display: "grid",
            gap: "20px",
          }}
        >
          <DataCell
            label="Chunks retrieved"
            value={String(analysisResult.retrieval_metadata.chunks_retrieved)}
            accent="var(--cyan)"
          />
          <DataCell
            label="Total tokens"
            value={analysisResult.llm_metadata.total_tokens.toLocaleString()}
          />
          <DataCell label="Cost" value={formatCost(analysisResult.cost)} />
        </div>

        {showRetrievalDetails ? (
          <div
            id="retrieval-details"
            style={{
              marginTop: "16px",
              paddingTop: "16px",
              borderTop: "1px solid rgba(43,94,167,0.12)",
            }}
          >
            <div
              className="retrieval-details"
              style={{
                display: "grid",
                gap: "14px",
              }}
            >
              {[
                [
                  "Embedding model",
                  analysisResult.retrieval_metadata.query_embedding_model,
                ],
                ["LLM model", analysisResult.llm_metadata.model],
                [
                  "Temperature",
                  String(analysisResult.llm_metadata.temperature),
                ],
                [
                  "Prompt / Completion",
                  `${analysisResult.llm_metadata.prompt_tokens.toLocaleString()} / ${analysisResult.llm_metadata.completion_tokens.toLocaleString()} tokens`,
                ],
                [
                  "Retrieval timestamp",
                  analysisResult.retrieval_metadata.retrieval_timestamp,
                ],
                [
                  "Filters applied",
                  JSON.stringify(
                    analysisResult.retrieval_metadata.filters_applied,
                  ),
                ],
                ["LLM latency", `${analysisResult.llm_metadata.latency_ms} ms`],
                ["LLM cost", formatCost(analysisResult.llm_metadata.cost_usd)],
                ["Created", analysisResult.created_at],
              ].map(([label, val]) => (
                <div key={label}>
                  <p
                    style={{
                      fontFamily: S.mono,
                      fontSize: "9px",
                      color: "var(--text-muted)",
                      textTransform: "uppercase",
                      letterSpacing: "0.15em",
                      marginBottom: "3px",
                    }}
                  >
                    {label}
                  </p>
                  <p
                    style={{
                      fontFamily: S.mono,
                      fontSize: "11px",
                      color: "var(--text-secondary)",
                    }}
                  >
                    {val}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      {/* Retrieved Chunks ─── */}
      {analysisResult.retrieved_chunks &&
      analysisResult.retrieved_chunks.length > 0 ? (
        <div style={{ marginBottom: "14px" }}>
          <p
            style={{
              fontFamily: S.mono,
              fontSize: "9px",
              color: "var(--text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.2em",
              marginBottom: "10px",
            }}
          >
            Retrieved Chunks ({analysisResult.retrieved_chunks.length})
          </p>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {analysisResult.retrieved_chunks.map((chunk, idx) => (
              <div
                key={chunk.chunk_id}
                style={{
                  border: "1px solid var(--border)",
                  backgroundColor: "var(--bg-surface)",
                  padding: "14px 18px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "flex-start",
                    justifyContent: "space-between",
                    marginBottom: "8px",
                    gap: "16px",
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                      }}
                    >
                      <span
                        style={{
                          fontFamily: S.mono,
                          fontSize: "10px",
                          color: "var(--amber)",
                          flexShrink: 0,
                        }}
                      >
                        #{String(idx + 1).padStart(2, "0")}
                      </span>
                      <span
                        style={{
                          fontFamily: S.syne,
                          fontSize: "13px",
                          fontWeight: 600,
                          color: "var(--text-primary)",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {chunk.document_title}
                      </span>
                      <span
                        style={{
                          fontFamily: S.mono,
                          fontSize: "9px",
                          color: "var(--text-muted)",
                          flexShrink: 0,
                        }}
                      >
                        chunk {chunk.chunk_index}
                      </span>
                    </div>
                  </div>
                  <div style={{ flexShrink: 0, textAlign: "right" }}>
                    <p
                      style={{
                        fontFamily: S.mono,
                        fontSize: "13px",
                        color: "var(--cyan)",
                        fontWeight: 500,
                      }}
                    >
                      {(chunk.similarity_score * 100).toFixed(1)}%
                    </p>
                    <div
                      style={{
                        width: "72px",
                        height: "2px",
                        backgroundColor: "var(--border)",
                        marginTop: "4px",
                        marginLeft: "auto",
                      }}
                    >
                      <div
                        style={{
                          width: `${chunk.similarity_score * 100}%`,
                          height: "100%",
                          backgroundColor: "var(--cyan)",
                        }}
                      />
                    </div>
                  </div>
                </div>
                <p
                  style={{
                    fontFamily: S.mono,
                    fontSize: "11px",
                    color: "var(--text-muted)",
                    lineHeight: "1.7",
                    display: "-webkit-box",
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: "vertical" as const,
                    overflow: "hidden",
                  }}
                >
                  {chunk.text}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Overall Assessment ─── */}
      <div
        style={{
          marginBottom: "14px",
          border: "1px solid var(--border-amber)",
          backgroundColor: "var(--amber-dim)",
          padding: "22px 24px",
        }}
      >
        <p
          style={{
            fontFamily: S.mono,
            fontSize: "9px",
            color: "var(--amber)",
            textTransform: "uppercase",
            letterSpacing: "0.2em",
            marginBottom: "12px",
          }}
        >
          Overall Assessment
        </p>
        <p
          style={{
            fontSize: "14px",
            color: "var(--text-primary)",
            lineHeight: "1.75",
            marginBottom: "18px",
            fontFamily: S.sans,
          }}
        >
          {analysisResult.output.overall_fit}
        </p>
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <span
            style={{
              fontFamily: S.mono,
              fontSize: "9px",
              color: "var(--text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.15em",
              flexShrink: 0,
            }}
          >
            Confidence
          </span>
          <div
            style={{
              flex: 1,
              maxWidth: "220px",
              height: "2px",
              backgroundColor: "var(--border)",
            }}
          >
            <div
              style={{
                width: `${analysisResult.output.confidence * 100}%`,
                height: "100%",
                backgroundColor: "var(--amber)",
                transition: "width 0.8s ease",
              }}
            />
          </div>
          <span
            style={{
              fontFamily: S.mono,
              fontSize: "12px",
              color: "var(--amber)",
              flexShrink: 0,
            }}
          >
            {(analysisResult.output.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* 4-quadrant grid ─── */}
      <div
        className="result-quadrants"
        style={{
          display: "grid",
          gap: "10px",
          marginBottom: "14px",
        }}
      >
        {analysisResult.output.strengths.length > 0 ? (
          <div
            style={{
              border: "1px solid var(--border-green)",
              backgroundColor: "var(--green-dim)",
              padding: "20px",
            }}
          >
            <p
              style={{
                fontFamily: S.mono,
                fontSize: "9px",
                color: "var(--green)",
                textTransform: "uppercase",
                letterSpacing: "0.2em",
                marginBottom: "14px",
              }}
            >
              Strengths
            </p>
            <SignedList
              items={analysisResult.output.strengths}
              sigil="+"
              color="var(--green)"
            />
          </div>
        ) : null}
        {analysisResult.output.gaps.length > 0 ? (
          <div
            style={{
              border: "1px solid var(--border-amber)",
              backgroundColor: "var(--amber-dim)",
              padding: "20px",
            }}
          >
            <p
              style={{
                fontFamily: S.mono,
                fontSize: "9px",
                color: "var(--amber)",
                textTransform: "uppercase",
                letterSpacing: "0.2em",
                marginBottom: "14px",
              }}
            >
              Gaps
            </p>
            <SignedList
              items={analysisResult.output.gaps}
              sigil="~"
              color="var(--amber)"
            />
          </div>
        ) : null}
        {analysisResult.output.risk_factors.length > 0 ? (
          <div
            style={{
              border: "1px solid var(--border-red)",
              backgroundColor: "var(--red-dim)",
              padding: "20px",
            }}
          >
            <p
              style={{
                fontFamily: S.mono,
                fontSize: "9px",
                color: "var(--red)",
                textTransform: "uppercase",
                letterSpacing: "0.2em",
                marginBottom: "14px",
              }}
            >
              Risk Factors
            </p>
            <SignedList
              items={analysisResult.output.risk_factors}
              sigil="!"
              color="var(--red)"
            />
          </div>
        ) : null}
        {analysisResult.output.recommended_focus.length > 0 ? (
          <div
            style={{
              border: "1px solid var(--border-purple)",
              backgroundColor: "var(--purple-dim)",
              padding: "20px",
            }}
          >
            <p
              style={{
                fontFamily: S.mono,
                fontSize: "9px",
                color: "var(--purple)",
                textTransform: "uppercase",
                letterSpacing: "0.2em",
                marginBottom: "14px",
              }}
            >
              Focus Areas
            </p>
            <SignedList
              items={analysisResult.output.recommended_focus}
              sigil="→"
              color="var(--purple)"
            />
          </div>
        ) : null}
      </div>

      {/* Citations ─── */}
      {analysisResult.citations.length > 0 ? (
        <div
          style={{
            border: "1px solid var(--border)",
            backgroundColor: "var(--bg-surface)",
            padding: "20px 24px",
          }}
        >
          <p
            style={{
              fontFamily: S.mono,
              fontSize: "9px",
              color: "var(--text-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.2em",
              marginBottom: "14px",
            }}
          >
            Source Citations ({analysisResult.citations.length})
          </p>
          <div
            className="citation-list"
            style={{ display: "flex", flexDirection: "column", gap: "12px" }}
          >
            {analysisResult.citations.map((c, i) => (
              <div
                key={i}
                style={{
                  borderLeft: "2px solid var(--border)",
                  paddingLeft: "16px",
                }}
              >
                <div
                  className="citation-meta"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    marginBottom: "4px",
                  }}
                >
                  <span
                    style={{
                      fontFamily: S.mono,
                      fontSize: "11px",
                      color: "var(--text-secondary)",
                    }}
                  >
                    {c.document_title}
                  </span>
                  <span
                    style={{
                      fontFamily: S.mono,
                      fontSize: "10px",
                      color: "var(--text-muted)",
                    }}
                  >
                    {(c.relevance_score * 100).toFixed(0)}% relevance
                  </span>
                </div>
                <p
                  style={{
                    fontFamily: S.mono,
                    fontSize: "11px",
                    color: "var(--text-muted)",
                    lineHeight: "1.6",
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical" as const,
                    overflow: "hidden",
                  }}
                >
                  {c.chunk_text}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
});

// ─── Main Component ───────────────────────────────────────────────────────────
export default function Home() {
  const { status: backendHealthStatus, retry: retryBackendHealth } =
    useBackendHealth();
  const { upload, isUploading, uploadError, uploadedDocument, resetUpload } =
    useDocumentUpload();
  const {
    analyzeWithRAG,
    isAnalyzing,
    analysisError,
    analysisResult,
    resetAnalysis,
  } = useRAGAnalysis();
  const {
    loadSample,
    isSampleLoading,
    sampleError,
    sampleResult,
    resetSample,
  } = useSampleAnalysis();

  const [dragActive, setDragActive] = useState(false);
  const [showUploadInfo, setShowUploadInfo] = useState(true);
  const [showIntro, setShowIntro] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (localStorage.getItem("uploadInfoDismissed") === "true")
      setShowUploadInfo(false);
    if (localStorage.getItem("introDismissed") === "true") setShowIntro(false);
  }, []);

  const handleDismissIntro = useCallback(() => {
    startTransition(() => setShowIntro(false));
    localStorage.setItem("introDismissed", "true");
  }, []);

  const handleDismissInfo = useCallback(() => {
    startTransition(() => setShowUploadInfo(false));
    localStorage.setItem("uploadInfoDismissed", "true");
  }, []);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  }, []);

  // Defined before handleDrop so the closure is always fresh
  const handleFileUpload = useCallback(
    async (file: File) => {
      resetSample();
      resetAnalysis();
      await upload(file, file.name.replace(/\.[^/.]+$/, ""), "web_upload");
    },
    [resetAnalysis, resetSample, upload],
  );

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      if (e.dataTransfer.files?.[0])
        await handleFileUpload(e.dataTransfer.files[0]);
    },
    [handleFileUpload],
  );

  const handleChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      e.preventDefault();
      if (e.target.files?.[0]) await handleFileUpload(e.target.files[0]);
    },
    [handleFileUpload],
  );

  const handleReset = () => {
    resetUpload();
    resetAnalysis();
    resetSample();
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // ─── Render ─────────────────────────────────────────────────────────────────
  return (
    <main style={{ minHeight: "100vh", backgroundColor: "var(--bg-base)" }}>
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header
        className="site-header"
        style={{
          borderBottom: "1px solid var(--border)",
          alignItems: "center",
          backgroundColor: "var(--bg-surface)",
        }}
      >
        <div>
          <div
            style={{
              fontFamily: S.syne,
              fontSize: "22px",
              fontWeight: 800,
              letterSpacing: "0.06em",
              color: "var(--text-primary)",
            }}
          >
            DOC<span style={{ color: "var(--amber)" }}>SAGE</span>
          </div>
          <p
            style={{
              fontFamily: S.mono,
              fontSize: "10px",
              color: "var(--text-muted)",
              letterSpacing: "0.18em",
              textTransform: "uppercase",
              marginTop: "2px",
            }}
          >
            Document Intelligence
          </p>
        </div>
        <div
          style={{
            display: "flex",
            gap: "16px",
            alignItems: "center",
            flexWrap: "wrap",
            justifyContent: "flex-end",
          }}
        >
          <span
            role="status"
            aria-live="polite"
            style={{
              fontFamily: S.mono,
              fontSize: "10px",
              color:
                backendHealthStatus === "online"
                  ? "var(--green)"
                  : backendHealthStatus === "unavailable"
                    ? "var(--red)"
                    : "var(--amber)",
              border: `1px solid ${
                backendHealthStatus === "online"
                  ? "var(--border-green)"
                  : backendHealthStatus === "unavailable"
                    ? "var(--border-red)"
                    : "var(--border-amber)"
              }`,
              padding: "3px 10px",
              letterSpacing: "0.12em",
            }}
          >
            ● API {backendHealthStatus}
            {backendHealthStatus === "delayed"
              ? " — Render may be waking up"
              : null}
          </span>
          {backendHealthStatus === "unavailable" ? (
            <button
              type="button"
              className="health-retry"
              onClick={() => void retryBackendHealth()}
              style={{
                fontFamily: S.mono,
                fontSize: "10px",
                color: "var(--red)",
                border: "1px solid var(--border-red)",
                background: "transparent",
                padding: "3px 10px",
                letterSpacing: "0.08em",
                cursor: "pointer",
              }}
            >
              Retry API connection
            </button>
          ) : null}
          <span
            style={{
              fontFamily: S.mono,
              fontSize: "10px",
              color: "var(--text-dim)",
              letterSpacing: "0.12em",
            }}
          >
            RAG · pgvector · gpt-4o
          </span>
        </div>
      </header>

      {/* ── Body ───────────────────────────────────────────────────────────── */}
      <div
        className="page-shell"
        style={{ maxWidth: "860px", margin: "0 auto" }}
      >
        <section
          aria-labelledby="homepage-benefit"
          style={{ marginBottom: "36px", maxWidth: "720px" }}
        >
          <p
            style={{
              fontFamily: S.mono,
              fontSize: "10px",
              color: "var(--amber)",
              letterSpacing: "0.16em",
              textTransform: "uppercase",
              marginBottom: "10px",
            }}
          >
            Evidence-first document intelligence
          </p>
          <h1
            id="homepage-benefit"
            style={{
              fontFamily: S.syne,
              fontSize: "clamp(30px, 6vw, 52px)",
              lineHeight: 1.08,
              color: "var(--text-primary)",
              letterSpacing: "-0.02em",
              marginBottom: "16px",
            }}
          >
            Ask your documents. Verify every answer.
          </h1>
          <p
            style={{
              fontFamily: S.sans,
              fontSize: "16px",
              lineHeight: 1.7,
              color: "var(--text-secondary)",
              maxWidth: "660px",
            }}
          >
            Turn a document into focused answers, then inspect the retrieved
            passages and citations behind each conclusion.
          </p>
        </section>

        {/* ── HOW IT WORKS ───────────────────────────────────────────────── */}
        {showIntro && (
          <div
            style={{
              marginBottom: "44px",
              border: "1px solid var(--border)",
              backgroundColor: "var(--bg-surface)",
              padding: "28px 32px",
              position: "relative",
            }}
          >
            {/* Dismiss */}
            <button
              type="button"
              className="compact-action intro-dismiss"
              onClick={handleDismissIntro}
              aria-label="Dismiss introduction"
              style={{
                position: "absolute",
                top: "14px",
                right: "18px",
                fontFamily: S.mono,
                fontSize: "16px",
                color: "var(--text-dim)",
                cursor: "pointer",
                background: "none",
                border: "none",
                lineHeight: 1,
              }}
            >
              ×
            </button>

            {/* Title */}
            <p
              style={{
                fontFamily: S.syne,
                fontSize: "13px",
                fontWeight: 700,
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                color: "var(--text-primary)",
                marginBottom: "18px",
              }}
            >
              What is DocSage?
            </p>

            {/* One-liner */}
            <p
              style={{
                fontFamily: S.sans,
                fontSize: "14px",
                color: "var(--text-secondary)",
                lineHeight: "1.75",
                marginBottom: "24px",
                maxWidth: "620px",
              }}
            >
              Upload a document — a résumé, report, contract, or research paper
              — and DocSage uses retrieval-augmented generation (RAG) to extract
              a structured assessment: overall fit, strengths, gaps, risk
              factors, and focus areas.
            </p>

            {/* 3-step flow */}
            <div
              className="intro-steps"
              style={{
                display: "grid",
                gap: "16px",
              }}
            >
              {(
                [
                  [
                    "01 — Ingest",
                    "Drop in a PDF, Markdown, HTML, or plain-text file. The document is chunked and embedded into a pgvector index.",
                    "var(--cyan)",
                  ],
                  [
                    "02 — Retrieve",
                    "Your query is embedded and the top-k most semantically similar chunks are retrieved using cosine similarity.",
                    "var(--amber)",
                  ],
                  [
                    "03 — Analyse",
                    "GPT-4o synthesises the retrieved chunks into a structured report. Every claim is grounded in source citations.",
                    "var(--purple)",
                  ],
                ] as [string, string, string][]
              ).map(([heading, body, accent]) => (
                <div
                  key={heading}
                  style={{
                    borderLeft: `2px solid ${accent}`,
                    paddingLeft: "14px",
                  }}
                >
                  <p
                    style={{
                      fontFamily: S.mono,
                      fontSize: "10px",
                      color: accent,
                      letterSpacing: "0.14em",
                      textTransform: "uppercase",
                      marginBottom: "6px",
                    }}
                  >
                    {heading}
                  </p>
                  <p
                    style={{
                      fontFamily: S.sans,
                      fontSize: "12px",
                      color: "var(--text-muted)",
                      lineHeight: "1.65",
                    }}
                  >
                    {body}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── 01 INGEST ──────────────────────────────────────────────────── */}
        <section className="upload-section" style={{ marginBottom: "40px" }}>
          <SectionLabel n="01" label="Ingest" />

          <div className="sample-entry">
            <div>
              <p className="sample-entry-title">Explore before you upload</p>
              <p className="sample-entry-copy">
                Inspect a precomputed analysis of a fictional document. No file,
                database record, embedding, or model call is created.
              </p>
            </div>
            <button
              type="button"
              onClick={() => void loadSample()}
              disabled={isSampleLoading}
            >
              {isSampleLoading ? "Loading sample" : "Try a sample document"}
            </button>
          </div>
          {sampleError ? (
            <div className="sample-error" role="alert">
              <p>{sampleError}</p>
              <p>The backend may be starting or temporarily unavailable.</p>
              <button type="button" onClick={() => void loadSample()}>
                Retry sample
              </button>
            </div>
          ) : null}

          <div className="retention-disclosure">
            <p>
              The original file is processed in memory and is not retained.
            </p>
            <p>Extracted text, chunks, and embeddings are stored for retrieval.</p>
            <p>Do not upload confidential material to this public demo.</p>
          </div>

          {/* Format hint */}
          {showUploadInfo && (
            <div
              style={{
                marginBottom: "14px",
                padding: "12px 16px",
                backgroundColor: "var(--cyan-dim)",
                border: "1px solid rgba(6,182,212,0.18)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <p
                style={{
                  fontFamily: S.mono,
                  fontSize: "11px",
                  color: "var(--text-muted)",
                  letterSpacing: "0.08em",
                }}
              >
                <span style={{ color: "var(--cyan)" }}>ACCEPTS</span>
                {"  "}PDF · MD · HTML · TXT — max 10 MB
              </p>
              <button
                type="button"
                className="compact-action upload-info-dismiss"
                onClick={handleDismissInfo}
                style={{
                  fontFamily: S.mono,
                  fontSize: "16px",
                  color: "var(--text-dim)",
                  cursor: "pointer",
                  background: "none",
                  border: "none",
                  lineHeight: 1,
                }}
                aria-label="Dismiss upload requirements"
              >
                ×
              </button>
            </div>
          )}

          {/* Drop zone */}
          <div
            className="upload-drop-zone"
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            style={{
              position: "relative",
              overflow: "hidden",
              border: `1px solid ${dragActive ? "var(--amber)" : "var(--border)"}`,
              backgroundColor: dragActive
                ? "var(--amber-dim)"
                : "var(--bg-surface)",
              textAlign: "center",
              cursor: isUploading ? "wait" : "default",
              transition: "border-color 0.15s, background-color 0.15s",
              boxShadow: dragActive
                ? "inset 0 0 32px rgba(92,61,30,0.06)"
                : "none",
            }}
          >
            <label className="file-chooser-label" htmlFor="document-upload">
              Choose document
            </label>
            <input
              id="document-upload"
              ref={fileInputRef}
              type="file"
              className="file-chooser"
              accept=".pdf,.md,.html,.txt"
              onChange={handleChange}
              disabled={isUploading}
            />

            {/* Scanning bar during upload */}
            {isUploading && (
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  height: "1px",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: "50%",
                    height: "100%",
                    background:
                      "linear-gradient(90deg, transparent, var(--amber), transparent)",
                    animation: "scanH 1.2s linear infinite",
                  }}
                />
              </div>
            )}

            {isUploading ? (
              <div>
                <p
                  style={{
                    fontFamily: S.mono,
                    fontSize: "12px",
                    color: "var(--amber)",
                    letterSpacing: "0.15em",
                    textTransform: "uppercase",
                  }}
                >
                  PROCESSING
                </p>
                <p
                  style={{
                    fontFamily: S.mono,
                    fontSize: "10px",
                    color: "var(--text-dim)",
                    marginTop: "8px",
                    letterSpacing: "0.08em",
                  }}
                >
                  chunking → embedding → indexing
                  <span style={{ animation: "blink 1s step-end infinite" }}>
                    _
                  </span>
                </p>
              </div>
            ) : (
              <div>
                <p
                  style={{
                    fontFamily: S.mono,
                    fontSize: "13px",
                    color: dragActive ? "var(--amber)" : "var(--text-muted)",
                    letterSpacing: "0.06em",
                  }}
                >
                  {dragActive
                    ? "> release to upload"
                    : "> drop file here or choose a document"}
                  <span
                    style={{
                      animation: "blink 1s step-end infinite",
                      color: "var(--amber)",
                    }}
                  >
                    _
                  </span>
                </p>
              </div>
            )}
          </div>

          {/* Upload error */}
          {uploadError && (
            <div
              style={{
                marginTop: "10px",
                padding: "12px 16px",
                backgroundColor: "var(--red-dim)",
                border: "1px solid rgba(155,34,38,0.28)",
              }}
            >
              <p
                style={{
                  fontFamily: S.mono,
                  fontSize: "11px",
                  color: "var(--red)",
                  letterSpacing: "0.06em",
                }}
              >
                ERR: {uploadError}
              </p>
            </div>
          )}
        </section>

        {/* ── 02 INDEXED ─────────────────────────────────────────────────── */}
        {uploadedDocument && (
          <section
            style={{
              marginBottom: "40px",
              animation: "fadeInUp 0.35s ease forwards",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                marginBottom: "20px",
              }}
            >
              <span
                style={{
                  fontFamily: S.mono,
                  fontSize: "10px",
                  color: "var(--amber)",
                  letterSpacing: "0.15em",
                }}
              >
                02
              </span>
              <span
                style={{
                  fontFamily: S.syne,
                  fontSize: "12px",
                  fontWeight: 700,
                  letterSpacing: "0.18em",
                  textTransform: "uppercase",
                  color: "var(--text-secondary)",
                }}
              >
                Indexed
              </span>
              <div style={rule} />
              <button
                type="button"
                className="compact-action clear-document"
                aria-label="Clear indexed document"
                onClick={handleReset}
                style={{
                  fontFamily: S.mono,
                  fontSize: "10px",
                  color: "var(--text-dim)",
                  cursor: "pointer",
                  background: "none",
                  border: "none",
                  letterSpacing: "0.1em",
                  flexShrink: 0,
                }}
              >
                [CLEAR]
              </button>
            </div>

            <div
              style={{
                border: "1px solid rgba(45,106,79,0.28)",
                backgroundColor: "var(--green-dim)",
                padding: "22px 24px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  justifyContent: "space-between",
                  marginBottom: "18px",
                }}
              >
                <div>
                  <p
                    style={{
                      fontFamily: S.syne,
                      fontSize: "15px",
                      fontWeight: 700,
                      color: "var(--text-primary)",
                      marginBottom: "4px",
                    }}
                  >
                    {uploadedDocument.title}
                  </p>
                  <p
                    style={{
                      fontFamily: S.mono,
                      fontSize: "10px",
                      color: "var(--text-muted)",
                    }}
                  >
                    {uploadedDocument.metadata.original_filename}
                  </p>
                </div>
                <span
                  style={{
                    fontFamily: S.mono,
                    fontSize: "9px",
                    color: "var(--green)",
                    border: "1px solid rgba(45,106,79,0.3)",
                    padding: "3px 10px",
                    letterSpacing: "0.12em",
                    flexShrink: 0,
                  }}
                >
                  ✓ INDEXED
                </span>
              </div>

              <div
                className="indexed-stats"
                style={{
                  display: "grid",
                  gap: "20px",
                  paddingTop: "16px",
                  borderTop: "1px solid rgba(45,106,79,0.12)",
                }}
              >
                <DataCell
                  label="Format"
                  value={uploadedDocument.type.toUpperCase()}
                  accent="var(--cyan)"
                />
                <DataCell
                  label="Characters"
                  value={uploadedDocument.metadata.text_length.toLocaleString()}
                />
                {uploadedDocument.metadata.chunks && (
                  <div>
                    <p
                      style={{
                        fontFamily: S.mono,
                        fontSize: "9px",
                        color: "var(--text-muted)",
                        textTransform: "uppercase",
                        letterSpacing: "0.15em",
                        marginBottom: "5px",
                      }}
                    >
                      Chunks
                    </p>
                    <p
                      style={{
                        fontFamily: S.mono,
                        fontSize: "18px",
                        color: "var(--text-primary)",
                        fontWeight: 400,
                        letterSpacing: "-0.02em",
                      }}
                    >
                      {uploadedDocument.metadata.chunks.total_chunks}
                      <span
                        style={{
                          fontSize: "11px",
                          color: "var(--text-muted)",
                          marginLeft: "6px",
                        }}
                      >
                        ×{" "}
                        {Math.round(
                          uploadedDocument.metadata.chunks.average_chunk_size,
                        )}{" "}
                        avg
                      </span>
                    </p>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        {sampleResult && !uploadedDocument ? (
          <section className="sample-source" aria-label="Synthetic sample source">
            <div>
              <p className="sample-entry-title">Synthetic sample</p>
              <p>{sampleResult.sample.title}</p>
              <p>{sampleResult.sample.description}</p>
            </div>
            <span>PRECOMPUTED · {sampleResult.sample.fixture_version}</span>
          </section>
        ) : null}

        {/* ── RUN ANALYSIS ───────────────────────────────────────────────── */}
        <section style={{ marginBottom: "40px" }}>
          {uploadedDocument ? (
            <AnalysisComposer
              key={uploadedDocument.id}
              documentId={uploadedDocument.id}
              isAnalyzing={isAnalyzing}
              analysisError={analysisError}
              onAnalyze={analyzeWithRAG}
            />
          ) : (
            <button className="analysis-submit" disabled>
              Run analysis
            </button>
          )}
        </section>

        {/* ── 03 ANALYSIS ────────────────────────────────────────────────── */}
        {!analysisResult && !sampleResult ? (
          <section
            style={{
              border: "1px solid var(--border)",
              backgroundColor: "var(--bg-surface)",
              padding: "48px 32px",
            }}
          >
            <SectionLabel n="03" label="Analysis" />
            <p
              style={{
                fontFamily: S.mono,
                fontSize: "11px",
                color: "var(--text-dim)",
                textAlign: "center",
                letterSpacing: "0.12em",
              }}
            >
              {uploadedDocument
                ? "— awaiting analysis run —"
                : "— upload a document to begin —"}
            </p>
          </section>
        ) : analysisResult ? (
          <AnalysisPanel analysisResult={analysisResult} />
        ) : sampleResult ? (
          <section aria-label="Synthetic sample result">
            <div className="sample-result-notice">
              <strong>Synthetic sample</strong>
              <span>
                Precomputed fictional data; metrics are representative, not a live run.
              </span>
            </div>
            <AnalysisPanel analysisResult={sampleResult.analysis} />
          </section>
        ) : null}

        {/* ── Footer ─────────────────────────────────────────────────────── */}
        <footer
          className="site-footer"
          style={{
            marginTop: "72px",
            paddingTop: "24px",
            borderTop: "1px solid var(--border)",
            display: "grid",
            gap: "16px",
          }}
        >
          <nav aria-label="Project resources" className="project-links">
            {PROJECT_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
              >
                {link.label} ↗
              </a>
            ))}
          </nav>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: "16px",
              flexWrap: "wrap",
            }}
          >
          <p
            style={{
              fontFamily: S.mono,
              fontSize: "9px",
              color: "var(--text-dim)",
              letterSpacing: "0.12em",
            }}
          >
            text-embedding-3-small · pgvector · gpt-4o
          </p>
          <p
            style={{
              fontFamily: S.mono,
              fontSize: "9px",
              color: "var(--text-dim)",
              letterSpacing: "0.12em",
            }}
          >
            docsage.phoenix7.dev
          </p>
          </div>
        </footer>
      </div>
    </main>
  );
}
