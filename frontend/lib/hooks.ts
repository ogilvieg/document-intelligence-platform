/**
 * React hooks for API operations with loading and error states
 */

import { useState } from "react";
import {
  DocumentUploadResponse,
  AnalysisResponse,
  AnalysisRequest,
  RAGAnalysisResponse,
} from "./api-client";
import { secureApiClient as apiClient } from "./secure-api-client";

export interface UseUploadState {
  upload: (
    file: File,
    title?: string,
    source?: string
  ) => Promise<DocumentUploadResponse | null>;
  isUploading: boolean;
  uploadError: string | null;
  uploadedDocument: DocumentUploadResponse | null;
  resetUpload: () => void;
}

/**
 * Hook for document upload with state management
 */
export function useDocumentUpload(): UseUploadState {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadedDocument, setUploadedDocument] =
    useState<DocumentUploadResponse | null>(null);

  const upload = async (file: File, title?: string, source?: string) => {
    setIsUploading(true);
    setUploadError(null);

    try {
      const result = await apiClient.uploadDocument(file, title, source);
      setUploadedDocument(result);
      return result;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed";
      setUploadError(message);
      return null;
    } finally {
      setIsUploading(false);
    }
  };

  const resetUpload = () => {
    setUploadedDocument(null);
    setUploadError(null);
  };

  return {
    upload,
    isUploading,
    uploadError,
    uploadedDocument,
    resetUpload,
  };
}

export interface UseAnalysisState {
  analyze: (request: AnalysisRequest) => Promise<AnalysisResponse | null>;
  isAnalyzing: boolean;
  analysisError: string | null;
  analysisResult: AnalysisResponse | null;
  resetAnalysis: () => void;
}

/**
 * Hook for document analysis with state management
 */
export function useDocumentAnalysis(): UseAnalysisState {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(
    null
  );

  const analyze = async (request: AnalysisRequest) => {
    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const result = await apiClient.analyzeDocuments(request);
      setAnalysisResult(result);
      return result;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Analysis failed";
      setAnalysisError(message);
      return null;
    } finally {
      setIsAnalyzing(false);
    }
  };

  const resetAnalysis = () => {
    setAnalysisResult(null);
    setAnalysisError(null);
  };

  return {
    analyze,
    isAnalyzing,
    analysisError,
    analysisResult,
    resetAnalysis,
  };
}

export interface UseRAGAnalysisState {
  analyzeWithRAG: (
    query: string,
    options?: {
      document_ids?: string[];
      doc_type?: string;
      top_k?: number;
      similarity_threshold?: number;
      temperature?: number;
    }
  ) => Promise<RAGAnalysisResponse | null>;
  isAnalyzing: boolean;
  analysisError: string | null;
  analysisResult: RAGAnalysisResponse | null;
  resetAnalysis: () => void;
}

/**
 * Hook for RAG-based document analysis with retrieval traceability
 */
export function useRAGAnalysis(): UseRAGAnalysisState {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] =
    useState<RAGAnalysisResponse | null>(null);

  const analyzeWithRAG = async (
    query: string,
    options?: {
      document_ids?: string[];
      doc_type?: string;
      top_k?: number;
      similarity_threshold?: number;
      temperature?: number;
    }
  ) => {
    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const result = await apiClient.analyzeWithRAG(query, options);
      setAnalysisResult(result);
      return result;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "RAG analysis failed";
      setAnalysisError(message);
      return null;
    } finally {
      setIsAnalyzing(false);
    }
  };

  const resetAnalysis = () => {
    setAnalysisResult(null);
    setAnalysisError(null);
  };

  return {
    analyzeWithRAG,
    isAnalyzing,
    analysisError,
    analysisResult,
    resetAnalysis,
  };
}
