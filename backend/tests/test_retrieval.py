"""Tests for RetrievalService."""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.retrieval import RetrievalService
from app.services.embedding_service import EmbeddingService
from app.models.database import (
    ChunkInDB,
    RetrievedChunk,
    SearchFilters,
    RetrievalMetadata
)


@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    mock = MagicMock(spec=EmbeddingService)
    mock.model_name = "text-embedding-3-small"
    mock.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    return mock


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing."""
    doc_id = uuid4()
    return [
        ChunkInDB(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=0,
            text="Python is a high-level programming language.",
            token_count=10,
            metadata={"page": 1},
            created_at=datetime.utcnow()
        ),
        ChunkInDB(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=1,
            text="FastAPI is a modern web framework for Python.",
            token_count=10,
            metadata={"page": 1},
            created_at=datetime.utcnow()
        ),
        ChunkInDB(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=2,
            text="Vector databases enable semantic search.",
            token_count=8,
            metadata={"page": 2},
            created_at=datetime.utcnow()
        ),
    ]


@pytest.fixture
def sample_retrieved_chunks(sample_chunks):
    """Create sample retrieved chunks with scores."""
    return [
        RetrievedChunk(
            chunk=sample_chunks[0],
            similarity_score=0.95,
            document_title="Python Guide",
            document_type="resume"
        ),
        RetrievedChunk(
            chunk=sample_chunks[1],
            similarity_score=0.88,
            document_title="Python Guide",
            document_type="resume"
        ),
        RetrievedChunk(
            chunk=sample_chunks[2],
            similarity_score=0.75,
            document_title="Python Guide",
            document_type="resume"
        ),
    ]


@pytest.mark.asyncio
async def test_retrieve_chunks_basic(mock_embedding_service, sample_retrieved_chunks):
    """Test basic chunk retrieval."""
    retrieval_service = RetrievalService(
        embedding_service=mock_embedding_service,
        default_top_k=5,
        similarity_threshold=0.5
    )
    
    # Mock database search
    with patch('app.services.retrieval.get_db_service') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.search_similar_chunks.return_value = sample_retrieved_chunks
        mock_get_db.return_value = mock_db
        
        # Perform retrieval
        result = await retrieval_service.retrieve_chunks(
            query="What is Python?",
            top_k=3
        )
        
        # Verify embedding was generated
        mock_embedding_service.generate_embedding.assert_called_once_with("What is Python?")
        
        # Verify search was called
        mock_db.search_similar_chunks.assert_called_once()
        call_args = mock_db.search_similar_chunks.call_args
        assert call_args[1]['top_k'] == 3
        assert call_args[1]['similarity_threshold'] == 0.5
        
        # Verify results
        assert isinstance(result, RetrievalMetadata)
        assert len(result.chunks_retrieved) == 3
        assert result.query == "What is Python?"
        assert result.query_embedding_model == "text-embedding-3-small"


@pytest.mark.asyncio
async def test_retrieve_chunks_with_filters(mock_embedding_service, sample_retrieved_chunks):
    """Test retrieval with filters."""
    retrieval_service = RetrievalService(embedding_service=mock_embedding_service)
    
    filters = SearchFilters(
        doc_type="resume",
        document_ids=[uuid4()]
    )
    
    with patch('app.services.retrieval.get_db_service') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.search_similar_chunks.return_value = sample_retrieved_chunks
        mock_get_db.return_value = mock_db
        
        result = await retrieval_service.retrieve_chunks(
            query="Python skills",
            filters=filters,
            top_k=5
        )
        
        # Verify filters were passed
        call_args = mock_db.search_similar_chunks.call_args
        assert call_args[1]['filters'] == filters
        
        # Verify results
        assert len(result.chunks_retrieved) == 3
        assert result.filters_applied == filters


@pytest.mark.asyncio
async def test_retrieve_for_document(mock_embedding_service, sample_retrieved_chunks):
    """Test retrieval for a specific document."""
    retrieval_service = RetrievalService(embedding_service=mock_embedding_service)
    doc_id = uuid4()
    
    with patch('app.services.retrieval.get_db_service') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.search_similar_chunks.return_value = sample_retrieved_chunks
        mock_get_db.return_value = mock_db
        
        result = await retrieval_service.retrieve_for_document(
            query="Python frameworks",
            document_id=doc_id,
            top_k=3
        )
        
        # Verify filters include document_id
        call_args = mock_db.search_similar_chunks.call_args
        filters = call_args[1]['filters']
        assert doc_id in filters.document_ids


@pytest.mark.asyncio
async def test_retrieve_by_type(mock_embedding_service, sample_retrieved_chunks):
    """Test retrieval filtered by document type."""
    retrieval_service = RetrievalService(embedding_service=mock_embedding_service)
    
    with patch('app.services.retrieval.get_db_service') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.search_similar_chunks.return_value = sample_retrieved_chunks
        mock_get_db.return_value = mock_db
        
        result = await retrieval_service.retrieve_by_type(
            query="technical skills",
            doc_type="resume",
            top_k=10
        )
        
        # Verify doc_type filter
        call_args = mock_db.search_similar_chunks.call_args
        filters = call_args[1]['filters']
        assert filters.doc_type == "resume"


@pytest.mark.asyncio
async def test_retrieve_multi_document(mock_embedding_service, sample_retrieved_chunks):
    """Test retrieval across multiple documents."""
    retrieval_service = RetrievalService(embedding_service=mock_embedding_service)
    doc_ids = [uuid4(), uuid4(), uuid4()]
    
    with patch('app.services.retrieval.get_db_service') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.search_similar_chunks.return_value = sample_retrieved_chunks
        mock_get_db.return_value = mock_db
        
        result = await retrieval_service.retrieve_multi_document(
            query="compare experience",
            document_ids=doc_ids,
            top_k=5
        )
        
        # Verify document_ids filter
        call_args = mock_db.search_similar_chunks.call_args
        filters = call_args[1]['filters']
        assert set(filters.document_ids) == set(doc_ids)


@pytest.mark.asyncio
async def test_get_chunk_context(sample_chunks):
    """Test retrieving surrounding chunks for context."""
    retrieval_service = RetrievalService()
    target_chunk_id = sample_chunks[1].id  # Middle chunk
    
    with patch('app.services.retrieval.get_db_service') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.get_chunk.return_value = sample_chunks[1]
        mock_db.get_chunks_by_document.return_value = sample_chunks
        mock_get_db.return_value = mock_db
        
        context = await retrieval_service.get_chunk_context(
            chunk_id=target_chunk_id,
            context_size=1
        )
        
        # Should get chunk before, target, and chunk after
        assert len(context) == 3
        assert context[0].id == sample_chunks[0].id
        assert context[1].id == sample_chunks[1].id
        assert context[2].id == sample_chunks[2].id


@pytest.mark.asyncio
async def test_get_chunk_context_edge_cases(sample_chunks):
    """Test chunk context at document boundaries."""
    retrieval_service = RetrievalService()
    
    with patch('app.services.retrieval.get_db_service') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.get_chunk.return_value = sample_chunks[0]
        mock_db.get_chunks_by_document.return_value = sample_chunks
        mock_get_db.return_value = mock_db
        
        # Test first chunk (no chunks before)
        context = await retrieval_service.get_chunk_context(
            chunk_id=sample_chunks[0].id,
            context_size=2
        )
        
        # Should start from beginning
        assert len(context) == 3  # First chunk + 2 after
        assert context[0].id == sample_chunks[0].id


@pytest.mark.asyncio
async def test_explain_retrieval_with_results(mock_embedding_service, sample_retrieved_chunks):
    """Test retrieval explanation with results."""
    retrieval_service = RetrievalService(embedding_service=mock_embedding_service)
    
    metadata = RetrievalMetadata(
        chunks_retrieved=sample_retrieved_chunks,
        query="Python programming",
        query_embedding_model="text-embedding-3-small",
        retrieval_timestamp=datetime.utcnow(),
        filters_applied=None,
        total_chunks_available=None
    )
    
    explanation = await retrieval_service.explain_retrieval(
        query="Python programming",
        retrieval_metadata=metadata
    )
    
    # Verify explanation structure
    assert explanation["query"] == "Python programming"
    assert explanation["chunks_retrieved"] == 3
    assert "score_analysis" in explanation
    assert explanation["score_analysis"]["highest"] == 0.95
    assert explanation["score_analysis"]["lowest"] == 0.75
    assert "documents_represented" in explanation
    assert "top_chunks" in explanation
    assert len(explanation["top_chunks"]) == 3


@pytest.mark.asyncio
async def test_explain_retrieval_no_results(mock_embedding_service):
    """Test retrieval explanation when no chunks found."""
    retrieval_service = RetrievalService(embedding_service=mock_embedding_service)
    
    metadata = RetrievalMetadata(
        chunks_retrieved=[],
        query="nonexistent query",
        query_embedding_model="text-embedding-3-small",
        retrieval_timestamp=datetime.utcnow(),
        filters_applied=None,
        total_chunks_available=None
    )
    
    explanation = await retrieval_service.explain_retrieval(
        query="nonexistent query",
        retrieval_metadata=metadata
    )
    
    # Verify explanation for no results
    assert explanation["result"] == "No chunks found"
    assert "reason" in explanation
    assert "suggestion" in explanation


@pytest.mark.asyncio
async def test_similarity_threshold_filtering(mock_embedding_service):
    """Test that similarity threshold filters results."""
    retrieval_service = RetrievalService(
        embedding_service=mock_embedding_service,
        similarity_threshold=0.8
    )
    
    # Create chunks with varying scores
    low_score_chunks = [
        RetrievedChunk(
            chunk=ChunkInDB(
                id=uuid4(),
                document_id=uuid4(),
                chunk_index=0,
                text="Low relevance text",
                token_count=5,
                metadata={},
                created_at=datetime.utcnow()
            ),
            similarity_score=0.6,
            document_title="Test Doc",
            document_type="resume"
        )
    ]
    
    with patch('app.services.retrieval.get_db_service') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.search_similar_chunks.return_value = low_score_chunks
        mock_get_db.return_value = mock_db
        
        result = await retrieval_service.retrieve_chunks(
            query="test query",
            top_k=5
        )
        
        # Verify threshold was passed to database
        call_args = mock_db.search_similar_chunks.call_args
        assert call_args[1]['similarity_threshold'] == 0.8


@pytest.mark.asyncio
async def test_retrieval_determinism(mock_embedding_service, sample_retrieved_chunks):
    """Test that retrieval is deterministic for the same query."""
    retrieval_service = RetrievalService(embedding_service=mock_embedding_service)
    
    with patch('app.services.retrieval.get_db_service') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.search_similar_chunks.return_value = sample_retrieved_chunks
        mock_get_db.return_value = mock_db
        
        # Run same query twice
        result1 = await retrieval_service.retrieve_chunks(
            query="Python",
            top_k=3
        )
        
        result2 = await retrieval_service.retrieve_chunks(
            query="Python",
            top_k=3
        )
        
        # Verify same chunks returned in same order
        assert len(result1.chunks_retrieved) == len(result2.chunks_retrieved)
        for i in range(len(result1.chunks_retrieved)):
            assert result1.chunks_retrieved[i].chunk.id == result2.chunks_retrieved[i].chunk.id
            assert result1.chunks_retrieved[i].similarity_score == result2.chunks_retrieved[i].similarity_score


@pytest.mark.asyncio
async def test_default_parameters(mock_embedding_service, sample_retrieved_chunks):
    """Test that default parameters are used correctly."""
    retrieval_service = RetrievalService(
        embedding_service=mock_embedding_service,
        default_top_k=7,
        similarity_threshold=0.65
    )
    
    with patch('app.services.retrieval.get_db_service') as mock_get_db:
        mock_db = AsyncMock()
        mock_db.search_similar_chunks.return_value = sample_retrieved_chunks
        mock_get_db.return_value = mock_db
        
        # Call without specifying parameters
        result = await retrieval_service.retrieve_chunks(query="test")
        
        # Verify defaults were used
        call_args = mock_db.search_similar_chunks.call_args
        assert call_args[1]['top_k'] == 7
        assert call_args[1]['similarity_threshold'] == 0.65
