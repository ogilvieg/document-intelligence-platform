"""Tests for RAG API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.main import app
from app.models.database import (
    ChunkInDB,
    RetrievedChunk,
    RetrievalMetadata,
    SearchFilters,
    EmbeddingInDB
)
from app.models import AnalysisOutput
from app.models.schemas import Citation

client = TestClient(app)


@pytest.fixture
def sample_document_id():
    """Sample document ID."""
    return uuid4()


@pytest.fixture
def sample_embeddings(sample_document_id):
    """Sample embeddings for testing."""
    return [
        EmbeddingInDB(
            id=uuid4(),
            chunk_id=uuid4(),
            vector=[0.1] * 1536,
            model_name="text-embedding-3-small",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        for _ in range(3)
    ]


@pytest.fixture
def sample_retrieved_chunks():
    """Sample retrieved chunks."""
    doc_id = uuid4()
    chunks = [
        ChunkInDB(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=i,
            text=f"Sample chunk {i} text with relevant information.",
            token_count=10,
            metadata={"page": i + 1},
            created_at=datetime.utcnow()
        )
        for i in range(3)
    ]
    
    return [
        RetrievedChunk(
            chunk=chunk,
            similarity_score=0.9 - (i * 0.1),
            document_title="Test Document",
            document_type="resume"
        )
        for i, chunk in enumerate(chunks)
    ]


@pytest.fixture
def sample_retrieval_metadata(sample_retrieved_chunks):
    """Sample retrieval metadata."""
    return RetrievalMetadata(
        chunks_retrieved=sample_retrieved_chunks,
        query="test query",
        query_embedding_model="text-embedding-3-small",
        retrieval_timestamp=datetime.utcnow(),
        filters_applied=None,
        total_chunks_available=None
    )


@pytest.fixture
def sample_analysis_output():
    """Sample analysis output."""
    return AnalysisOutput(
        overall_fit="Strong candidate with relevant experience",
        strengths=["Technical skills", "Leadership"],
        gaps=["Cloud experience"],
        risk_factors=["Limited team size"],
        confidence=0.85,
        recommended_focus=["Assess cloud skills"]
    )


@pytest.fixture
def sample_citations(sample_retrieved_chunks):
    """Sample citations."""
    return [
        Citation(
            chunk_id=rc.chunk.id,
            document_id=rc.chunk.document_id,
            document_title=rc.document_title,
            chunk_text=rc.chunk.text,
            relevance_score=rc.similarity_score
        )
        for rc in sample_retrieved_chunks
    ]


def test_generate_embeddings_endpoint(sample_document_id, sample_embeddings):
    """Test POST /documents/{id}/generate-embeddings endpoint."""
    with patch('app.api.routes.embedding_service') as mock_embedding_service:
        mock_embedding_service.embed_document_chunks = AsyncMock(return_value=sample_embeddings)
        mock_embedding_service.model_name = "text-embedding-3-small"
        
        response = client.post(f"/api/v1/documents/{sample_document_id}/generate-embeddings")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["document_id"] == str(sample_document_id)
        assert data["total_embeddings"] == 3
        assert data["model"] == "text-embedding-3-small"
        assert data["embedding_dimensions"] == 1536
        assert "timestamp" in data


def test_generate_embeddings_handles_errors(sample_document_id):
    """Test embedding generation handles errors."""
    with patch('app.api.routes.embedding_service') as mock_embedding_service:
        mock_embedding_service.embed_document_chunks = AsyncMock(
            side_effect=Exception("Database connection failed")
        )
        
        response = client.post(f"/api/v1/documents/{sample_document_id}/generate-embeddings")
        
        assert response.status_code == 500
        assert "Failed to generate embeddings" in response.json()["detail"]


def test_search_chunks_endpoint(sample_retrieval_metadata):
    """Test POST /search/chunks endpoint."""
    with patch('app.api.routes.retrieval_service') as mock_retrieval_service:
        mock_retrieval_service.retrieve_chunks = AsyncMock(return_value=sample_retrieval_metadata)
        
        response = client.post(
            "/api/v1/search/chunks",
            params={
                "query": "Python experience",
                "top_k": 5,
                "similarity_threshold": 0.5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["query"] == "test query"
        assert data["chunks_retrieved"] == 3
        assert data["query_embedding_model"] == "text-embedding-3-small"
        assert len(data["chunks"]) == 3
        
        # Verify chunk structure
        chunk = data["chunks"][0]
        assert "chunk_id" in chunk
        assert "document_id" in chunk
        assert "text" in chunk
        assert "similarity_score" in chunk
        assert chunk["similarity_score"] == 0.9


def test_search_chunks_with_filters(sample_retrieval_metadata):
    """Test chunk search with filters."""
    with patch('app.api.routes.retrieval_service') as mock_retrieval_service:
        mock_retrieval_service.retrieve_chunks = AsyncMock(return_value=sample_retrieval_metadata)
        
        filters = {
            "doc_type": "resume",
            "document_ids": [str(uuid4())]
        }
        
        response = client.post(
            "/api/v1/search/chunks",
            params={"query": "skills"},
            json=filters
        )
        
        assert response.status_code == 200


def test_search_chunks_handles_errors():
    """Test chunk search handles errors."""
    with patch('app.api.routes.retrieval_service') as mock_retrieval_service:
        mock_retrieval_service.retrieve_chunks = AsyncMock(
            side_effect=Exception("Vector search failed")
        )
        
        response = client.post(
            "/api/v1/search/chunks",
            params={"query": "test"}
        )
        
        assert response.status_code == 500
        assert "Chunk search failed" in response.json()["detail"]


def test_analyze_rag_endpoint(
    sample_retrieval_metadata,
    sample_analysis_output,
    sample_citations
):
    """Test POST /analyze-rag endpoint (main RAG workflow)."""
    with patch('app.api.routes.retrieval_service') as mock_retrieval_service, \
         patch('app.api.routes.llm_service') as mock_llm_service:
        
        mock_retrieval_service.retrieve_chunks = AsyncMock(return_value=sample_retrieval_metadata)
        
        mock_llm_service.analyze_with_chunks.return_value = (
            sample_analysis_output,
            sample_citations,
            {
                "model": "gpt-4-turbo-preview",
                "latency_ms": 1200,
                "prompt_tokens": 500,
                "completion_tokens": 150,
                "total_tokens": 650
            }
        )
        mock_llm_service.estimate_cost.return_value = 0.0195
        
        response = client.post(
            "/api/v1/analyze-rag",
            json={
                "query": "Evaluate this candidate for senior role",
                "top_k": 5,
                "temperature": 0.7
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "analysis_id" in data
        assert data["query"] == "Evaluate this candidate for senior role"
        
        # Verify analysis output
        assert data["output"]["confidence"] == 0.85
        assert len(data["output"]["strengths"]) == 2
        
        # Verify citations
        assert len(data["citations"]) == 3
        citation = data["citations"][0]
        assert "chunk_id" in citation
        assert "document_id" in citation
        assert "relevance_score" in citation
        
        # Verify retrieval metadata
        assert data["retrieval_metadata"]["chunks_retrieved"] == 3
        assert data["retrieval_metadata"]["query_embedding_model"] == "text-embedding-3-small"
        
        # Verify LLM metadata
        assert data["llm_metadata"]["model"] == "gpt-4-turbo-preview"
        assert data["llm_metadata"]["latency_ms"] == 1200
        assert data["llm_metadata"]["total_tokens"] == 650
        assert data["llm_metadata"]["cost_usd"] == 0.0195


def test_analyze_rag_with_document_filter(
    sample_retrieval_metadata,
    sample_analysis_output,
    sample_citations
):
    """Test RAG analysis with document ID filter."""
    with patch('app.api.routes.retrieval_service') as mock_retrieval_service, \
         patch('app.api.routes.llm_service') as mock_llm_service:
        
        mock_retrieval_service.retrieve_chunks = AsyncMock(return_value=sample_retrieval_metadata)
        mock_llm_service.analyze_with_chunks.return_value = (
            sample_analysis_output,
            sample_citations,
            {"model": "gpt-4", "latency_ms": 1000, "prompt_tokens": 400, "completion_tokens": 100, "total_tokens": 500}
        )
        mock_llm_service.estimate_cost.return_value = 0.015
        
        doc_ids = [str(uuid4()), str(uuid4())]
        
        response = client.post(
            "/api/v1/analyze-rag",
            json={
                "query": "Compare these candidates",
                "document_ids": doc_ids
            }
        )
        
        assert response.status_code == 200
        
        # Verify retrieval was called with filters
        call_args = mock_retrieval_service.retrieve_chunks.call_args
        assert call_args[1]['filters'] is not None


def test_analyze_rag_with_doc_type_filter(
    sample_retrieval_metadata,
    sample_analysis_output,
    sample_citations
):
    """Test RAG analysis with document type filter."""
    with patch('app.api.routes.retrieval_service') as mock_retrieval_service, \
         patch('app.api.routes.llm_service') as mock_llm_service:
        
        mock_retrieval_service.retrieve_chunks = AsyncMock(return_value=sample_retrieval_metadata)
        mock_llm_service.analyze_with_chunks.return_value = (
            sample_analysis_output,
            sample_citations,
            {"model": "gpt-4", "latency_ms": 1000, "prompt_tokens": 400, "completion_tokens": 100, "total_tokens": 500}
        )
        mock_llm_service.estimate_cost.return_value = 0.015
        
        response = client.post(
            "/api/v1/analyze-rag",
            json={
                "query": "Find resume skills",
                "doc_type": "resume"
            }
        )
        
        assert response.status_code == 200


def test_analyze_rag_no_chunks_found():
    """Test RAG analysis when no chunks are retrieved."""
    empty_metadata = RetrievalMetadata(
        chunks_retrieved=[],
        query="obscure query",
        query_embedding_model="text-embedding-3-small",
        retrieval_timestamp=datetime.utcnow(),
        filters_applied=None,
        total_chunks_available=None
    )
    
    with patch('app.api.routes.retrieval_service') as mock_retrieval_service:
        mock_retrieval_service.retrieve_chunks = AsyncMock(return_value=empty_metadata)
        
        response = client.post(
            "/api/v1/analyze-rag",
            json={"query": "obscure query"}
        )
        
        assert response.status_code == 404
        assert "No relevant chunks found" in response.json()["detail"]


def test_analyze_rag_handles_errors():
    """Test RAG analysis handles errors."""
    with patch('app.api.routes.retrieval_service') as mock_retrieval_service:
        mock_retrieval_service.retrieve_chunks = AsyncMock(
            side_effect=Exception("Retrieval service down")
        )
        
        response = client.post(
            "/api/v1/analyze-rag",
            json={"query": "test"}
        )
        
        assert response.status_code == 500
        assert "RAG analysis failed" in response.json()["detail"]


def test_analyze_rag_custom_parameters(
    sample_retrieval_metadata,
    sample_analysis_output,
    sample_citations
):
    """Test RAG analysis with custom parameters."""
    with patch('app.api.routes.retrieval_service') as mock_retrieval_service, \
         patch('app.api.routes.llm_service') as mock_llm_service:
        
        mock_retrieval_service.retrieve_chunks = AsyncMock(return_value=sample_retrieval_metadata)
        mock_llm_service.analyze_with_chunks.return_value = (
            sample_analysis_output,
            sample_citations,
            {"model": "gpt-4", "latency_ms": 1000, "prompt_tokens": 400, "completion_tokens": 100, "total_tokens": 500}
        )
        mock_llm_service.estimate_cost.return_value = 0.015
        
        response = client.post(
            "/api/v1/analyze-rag",
            json={
                "query": "test",
                "top_k": 10,
                "similarity_threshold": 0.8,
                "temperature": 0.3
            }
        )
        
        assert response.status_code == 200
        
        # Verify parameters were passed
        retrieval_call = mock_retrieval_service.retrieve_chunks.call_args
        assert retrieval_call[1]['top_k'] == 10
        assert retrieval_call[1]['similarity_threshold'] == 0.8
        
        llm_call = mock_llm_service.analyze_with_chunks.call_args
        assert llm_call[1]['temperature'] == 0.3


def test_rag_endpoint_traceability(
    sample_retrieval_metadata,
    sample_analysis_output,
    sample_citations
):
    """Test that RAG endpoint provides full traceability."""
    with patch('app.api.routes.retrieval_service') as mock_retrieval_service, \
         patch('app.api.routes.llm_service') as mock_llm_service:
        
        mock_retrieval_service.retrieve_chunks = AsyncMock(return_value=sample_retrieval_metadata)
        mock_llm_service.analyze_with_chunks.return_value = (
            sample_analysis_output,
            sample_citations,
            {"model": "gpt-4", "latency_ms": 1000, "prompt_tokens": 400, "completion_tokens": 100, "total_tokens": 500}
        )
        mock_llm_service.estimate_cost.return_value = 0.015
        
        response = client.post(
            "/api/v1/analyze-rag",
            json={"query": "test query"}
        )
        
        data = response.json()
        
        # Verify all traceability components present
        assert "analysis_id" in data
        assert "query" in data
        assert "output" in data
        assert "citations" in data
        assert "retrieval_metadata" in data
        assert "llm_metadata" in data
        assert "created_at" in data
        
        # Verify we can trace from output -> citations -> chunks
        assert len(data["citations"]) == 3
        assert data["retrieval_metadata"]["chunks_retrieved"] == 3
        
        # Verify cost tracking
        assert "cost_usd" in data["llm_metadata"]
        assert data["llm_metadata"]["cost_usd"] > 0
