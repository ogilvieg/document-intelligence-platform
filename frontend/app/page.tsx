"use client";

import { useState, useRef, useCallback } from "react";
import { useDocumentUpload, useDocumentAnalysis } from "@/lib/hooks";
import { formatFileSize, formatLatency, formatCost } from "@/lib/api-client";

export default function Home() {
  const { upload, isUploading, uploadError, uploadedDocument, resetUpload } =
    useDocumentUpload();
  const { analyze, isAnalyzing, analysisError, analysisResult, resetAnalysis } =
    useDocumentAnalysis();

  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  // Handle drop
  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      await handleFileUpload(file);
    }
  }, []);

  // Handle file upload
  const handleFileUpload = async (file: File) => {
    resetAnalysis(); // Clear previous analysis when uploading new file
    await upload(file, file.name.replace(/\.[^/.]+$/, ""), "web_upload");
  };

  // Handle file input change
  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      await handleFileUpload(e.target.files[0]);
    }
  };

  // Handle click on upload area
  const handleClick = () => {
    fileInputRef.current?.click();
  };

  // Handle analyze button
  const handleAnalyze = async () => {
    if (!uploadedDocument) return;

    await analyze({
      document_ids: [uploadedDocument.id],
      options: {
        context: `Analyzing document: ${
          uploadedDocument.title
        }. Document type: ${uploadedDocument.type}. Contains ${
          uploadedDocument.metadata.chunks?.total_chunks || 0
        } chunks.`,
      },
    });
  };

  // Handle reset
  const handleReset = () => {
    resetUpload();
    resetAnalysis();
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            Document Intelligence Platform
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            AI-powered document analysis with structured outputs and full
            traceability
          </p>
        </div>

        {/* Main Content Area */}
        <div className="max-w-4xl mx-auto bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8">
          {/* Upload Section */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-4">
              Upload Documents
            </h2>
            <div
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${
                dragActive
                  ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                  : "border-slate-300 dark:border-slate-600 hover:border-blue-500"
              } ${isUploading ? "opacity-50 cursor-wait" : ""}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={handleClick}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".pdf,.md,.html,.txt"
                onChange={handleChange}
                disabled={isUploading}
              />
              <div className="space-y-4">
                {isUploading ? (
                  <>
                    <div className="mx-auto h-12 w-12">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                    </div>
                    <p className="text-lg text-slate-600 dark:text-slate-300">
                      Uploading and processing...
                    </p>
                  </>
                ) : (
                  <>
                    <svg
                      className="mx-auto h-12 w-12 text-slate-400"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                      aria-hidden="true"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <div>
                      <p className="text-lg text-slate-600 dark:text-slate-300">
                        <span className="font-semibold text-blue-600 dark:text-blue-400">
                          Click to upload
                        </span>{" "}
                        or drag and drop
                      </p>
                      <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                        PDF, Markdown, or HTML files (max 10MB)
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Upload Error */}
            {uploadError && (
              <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-red-800 dark:text-red-200 text-sm">
                  <strong>Error:</strong> {uploadError}
                </p>
              </div>
            )}
          </div>

          {/* Uploaded Document Info */}
          {uploadedDocument && (
            <div className="mb-8">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  Uploaded Document
                </h3>
                <button
                  onClick={handleReset}
                  className="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                >
                  Clear & Upload New
                </button>
              </div>
              <div className="bg-slate-50 dark:bg-slate-700 rounded-lg p-4 space-y-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-semibold text-slate-900 dark:text-slate-100">
                      {uploadedDocument.title}
                    </p>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                      {uploadedDocument.metadata.original_filename} •{" "}
                      {uploadedDocument.type.toUpperCase()}
                    </p>
                  </div>
                  <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 text-xs font-medium rounded">
                    ✓ Uploaded
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-200 dark:border-slate-600">
                  <div>
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      Text Length
                    </p>
                    <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                      {uploadedDocument.metadata.text_length.toLocaleString()}{" "}
                      chars
                    </p>
                  </div>
                  {uploadedDocument.metadata.chunks && (
                    <div>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Chunks
                      </p>
                      <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                        {uploadedDocument.metadata.chunks.total_chunks} chunks
                        <span className="text-xs text-slate-500 dark:text-slate-400 ml-1">
                          (avg{" "}
                          {Math.round(
                            uploadedDocument.metadata.chunks.average_chunk_size
                          )}{" "}
                          chars)
                        </span>
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Analyze Button */}
          <div className="flex justify-center">
            <button
              onClick={handleAnalyze}
              disabled={!uploadedDocument || isAnalyzing}
              className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg shadow-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isAnalyzing ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Analyzing...
                </>
              ) : (
                "Run Analysis"
              )}
            </button>
          </div>

          {/* Analysis Error */}
          {analysisError && (
            <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-red-800 dark:text-red-200 text-sm">
                <strong>Error:</strong> {analysisError}
              </p>
            </div>
          )}
        </div>

        {/* Results Section */}
        {analysisResult && (
          <div className="max-w-4xl mx-auto mt-8 bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
                Analysis Results
              </h2>
              <div className="flex gap-4 text-sm">
                <span className="text-slate-600 dark:text-slate-400">
                  ⚡ {formatLatency(analysisResult.latency_ms)}
                </span>
                <span className="text-slate-600 dark:text-slate-400">
                  💰 {formatCost(analysisResult.cost)}
                </span>
              </div>
            </div>

            {/* Overall Assessment */}
            <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2 uppercase tracking-wide">
                Overall Assessment
              </h3>
              <p className="text-slate-800 dark:text-slate-200">
                {analysisResult.output.overall_fit}
              </p>
              <div className="mt-3 flex items-center gap-2">
                <span className="text-xs text-blue-700 dark:text-blue-300 font-medium">
                  Confidence:
                </span>
                <div className="flex-1 bg-blue-200 dark:bg-blue-800 rounded-full h-2 max-w-xs">
                  <div
                    className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full transition-all"
                    style={{
                      width: `${analysisResult.output.confidence * 100}%`,
                    }}
                  ></div>
                </div>
                <span className="text-xs font-semibold text-blue-700 dark:text-blue-300">
                  {(analysisResult.output.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>

            {/* Strengths */}
            {analysisResult.output.strengths.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-green-700 dark:text-green-400 mb-3 flex items-center gap-2">
                  <span className="text-xl">✓</span> Strengths
                </h3>
                <ul className="space-y-2">
                  {analysisResult.output.strengths.map((strength, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg"
                    >
                      <span className="text-green-600 dark:text-green-400 mt-0.5">
                        •
                      </span>
                      <span className="text-slate-800 dark:text-slate-200">
                        {strength}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Gaps */}
            {analysisResult.output.gaps.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-amber-700 dark:text-amber-400 mb-3 flex items-center gap-2">
                  <span className="text-xl">⚠</span> Gaps & Areas for
                  Improvement
                </h3>
                <ul className="space-y-2">
                  {analysisResult.output.gaps.map((gap, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg"
                    >
                      <span className="text-amber-600 dark:text-amber-400 mt-0.5">
                        •
                      </span>
                      <span className="text-slate-800 dark:text-slate-200">
                        {gap}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Risk Factors */}
            {analysisResult.output.risk_factors.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-red-700 dark:text-red-400 mb-3 flex items-center gap-2">
                  <span className="text-xl">⚡</span> Risk Factors
                </h3>
                <ul className="space-y-2">
                  {analysisResult.output.risk_factors.map((risk, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg"
                    >
                      <span className="text-red-600 dark:text-red-400 mt-0.5">
                        •
                      </span>
                      <span className="text-slate-800 dark:text-slate-200">
                        {risk}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommended Focus */}
            {analysisResult.output.recommended_focus.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-purple-700 dark:text-purple-400 mb-3 flex items-center gap-2">
                  <span className="text-xl">→</span> Recommended Focus Areas
                </h3>
                <ul className="space-y-2">
                  {analysisResult.output.recommended_focus.map((focus, idx) => (
                    <li
                      key={idx}
                      className="flex items-start gap-2 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg"
                    >
                      <span className="text-purple-600 dark:text-purple-400 mt-0.5">
                        •
                      </span>
                      <span className="text-slate-800 dark:text-slate-200">
                        {focus}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Citations */}
            {analysisResult.citations.length > 0 && (
              <div className="pt-6 border-t border-slate-200 dark:border-slate-700">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-3">
                  Source Citations ({analysisResult.citations.length})
                </h3>
                <div className="space-y-3">
                  {analysisResult.citations.map((citation, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-50 dark:bg-slate-700 rounded-lg text-sm"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-slate-700 dark:text-slate-300">
                          {citation.document_title}
                        </span>
                        <span className="text-xs text-slate-500 dark:text-slate-400">
                          Relevance:{" "}
                          {(citation.relevance_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-slate-600 dark:text-slate-400 text-xs line-clamp-2">
                        {citation.chunk_text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State for Results */}
        {!analysisResult && (
          <div className="max-w-4xl mx-auto mt-8 bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-4">
              Analysis Results
            </h2>
            <div className="bg-slate-50 dark:bg-slate-700 rounded-lg p-8 text-center text-slate-500 dark:text-slate-400">
              {uploadedDocument
                ? 'Click "Run Analysis" to analyze your document'
                : "Upload a document to get started"}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-12 text-sm text-slate-500 dark:text-slate-400">
          <p>Week 1 MVP - Document Upload & Analysis Interface</p>
        </div>
      </div>
    </main>
  );
}
