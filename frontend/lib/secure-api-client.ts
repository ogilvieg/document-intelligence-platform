/**
 * Secure API Client using Next.js API Route Proxy
 *
 * This client calls Next.js API routes instead of the backend directly,
 * keeping the API key secure on the server side.
 */

import {
  DocumentUploadResponse,
  AnalysisRequest,
  AnalysisResponse,
  RAGAnalysisResponse,
  HealthResponse,
} from "./api-client";

/**
 * API Client class that uses Next.js API routes as a proxy
 */
export class SecureAPIClient {
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

    const response = await fetch(`/api/proxy?endpoint=/documents/upload`, {
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
    const response = await fetch(`/api/proxy?endpoint=/analyze`, {
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
    const response = await fetch(`/api/proxy?endpoint=/analyze-rag`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        document_ids: options?.document_ids,
        doc_type: options?.doc_type,
        top_k: options?.top_k || 5,
        similarity_threshold: options?.similarity_threshold || 0.3, // Lowered from 0.5 for better recall
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
   * Check backend health (no auth required)
   */
  async checkHealth(): Promise<HealthResponse> {
    const response = await fetch(`/api/proxy?endpoint=/health`);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * List all uploaded documents
   */
  async listDocuments(): Promise<any[]> {
    const response = await fetch(`/api/proxy?endpoint=/documents`);

    if (!response.ok) {
      throw new Error(`Failed to list documents: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get a specific document by ID
   */
  async getDocument(documentId: string): Promise<any> {
    const response = await fetch(
      `/api/proxy?endpoint=/documents/${documentId}`
    );

    if (!response.ok) {
      throw new Error(`Failed to get document: ${response.statusText}`);
    }

    return response.json();
  }
}

// Export a singleton instance
export const secureApiClient = new SecureAPIClient();
