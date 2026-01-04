/**
 * API Client for Document Intelligence Platform Backend
 *
 * Provides typed methods for interacting with the FastAPI backend.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface DocumentUploadResponse {
  id: string;
  title: string;
  type: "pdf" | "markdown" | "html" | "text" | "other";
  source: string | null;
  version: string;
  created_at: string;
  metadata: {
    original_filename: string;
    text_length: number;
    page_count?: number;
    parser: string;
    content_type: string;
    chunks?: {
      total_chunks: number;
      average_chunk_size: number;
      chunk_size_config: number;
      chunk_overlap_config: number;
    };
  };
}

export interface AnalysisOutput {
  overall_fit: string;
  strengths: string[];
  gaps: string[];
  risk_factors: string[];
  confidence: number;
  recommended_focus: string[];
}

export interface Citation {
  chunk_id: string;
  document_id: string;
  document_title: string;
  chunk_text: string;
  relevance_score: number;
}

export interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  document_title: string;
  doc_type: string;
  chunk_index: number;
  text: string;
  similarity_score: number;
  metadata?: Record<string, any>;
}

export interface RetrievalMetadata {
  chunks_retrieved: number;
  query_embedding_model: string;
  timestamp: string;
  filters: {
    doc_type?: string | null;
    document_ids?: string[] | null;
    metadata_filters?: Record<string, any> | null;
  };
}

export interface LLMMetadata {
  model: string;
  temperature: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface AnalysisResponse {
  id: string;
  output: AnalysisOutput;
  citations: Citation[];
  latency_ms: number;
  cost: number | null;
  created_at: string;
}

export interface RAGAnalysisResponse {
  analysis_id: string;
  query: string;
  output: AnalysisOutput;
  citations: Citation[];
  retrieval_metadata: RetrievalMetadata;
  llm_metadata: LLMMetadata;
  cost: number;
  retrieved_chunks?: RetrievedChunk[];
}

export interface AnalysisRequest {
  document_ids: string[];
  options?: Record<string, any>;
}

export interface HealthResponse {
  status: string;
  timestamp?: string;
}

/**
 * API Client class with methods for all backend endpoints
 */
export class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Upload a document for processing
   */
  async uploadDocument(
    file: File,
    title?: string,
    source?: string
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append("file", file);
    if (title) formData.append("title", title);
    if (source) formData.append("source", source);

    const response = await fetch(`${this.baseURL}/documents/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Upload failed" }));
      throw new Error(error.detail || `Upload failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Run analysis on uploaded documents
   */
  async analyzeDocuments(request: AnalysisRequest): Promise<AnalysisResponse> {
    const response = await fetch(`${this.baseURL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Analysis failed" }));
      throw new Error(
        error.detail || `Analysis failed: ${response.statusText}`
      );
    }

    return response.json();
  }

  /**
   * Run RAG-based analysis with retrieval traceability
   */
  async analyzeWithRAG(
    query: string,
    options?: {
      document_ids?: string[];
      doc_type?: string;
      top_k?: number;
      similarity_threshold?: number;
      temperature?: number;
    }
  ): Promise<RAGAnalysisResponse> {
    const response = await fetch(`${this.baseURL}/analyze-rag`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        document_ids: options?.document_ids,
        doc_type: options?.doc_type,
        top_k: options?.top_k || 5,
        similarity_threshold: options?.similarity_threshold || 0.5,
        temperature: options?.temperature || 0.7,
      }),
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "RAG analysis failed" }));
      throw new Error(
        error.detail || `RAG analysis failed: ${response.statusText}`
      );
    }

    return response.json();
  }

  /**
   * Check backend health
   */
  async checkHealth(): Promise<HealthResponse> {
    const response = await fetch(
      `${this.baseURL.replace("/api/v1", "")}/health`
    );

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * List all uploaded documents (not yet implemented in backend)
   */
  async listDocuments(): Promise<any[]> {
    const response = await fetch(`${this.baseURL}/documents`);

    if (!response.ok) {
      throw new Error(`Failed to list documents: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get a specific document by ID (not yet implemented in backend)
   */
  async getDocument(documentId: string): Promise<any> {
    const response = await fetch(`${this.baseURL}/documents/${documentId}`);

    if (!response.ok) {
      throw new Error(`Failed to get document: ${response.statusText}`);
    }

    return response.json();
  }
}

/**
 * Default API client instance
 */
export const apiClient = new APIClient();

/**
 * Utility function to format file size
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}

/**
 * Utility function to format latency
 */
export function formatLatency(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

/**
 * Utility function to format cost
 */
export function formatCost(cost: number | null): string {
  if (cost === null || cost === undefined) return "N/A";
  return `$${cost.toFixed(4)}`;
}
