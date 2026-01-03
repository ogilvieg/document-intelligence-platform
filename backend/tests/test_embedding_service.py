"""Tests for EmbeddingService."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.embedding_service import EmbeddingService
from app.models.database import ChunkInDB, EmbeddingInDB
from datetime import datetime


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response."""
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(embedding=[0.1] * 1536)  # Mock 1536-dimensional embedding
    ]
    mock_response.usage = MagicMock(total_tokens=50)
    return mock_response


@pytest.fixture
def mock_batch_openai_response():
    """Mock OpenAI batch API response."""
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(embedding=[0.1] * 1536),
        MagicMock(embedding=[0.2] * 1536),
        MagicMock(embedding=[0.3] * 1536)
    ]
    mock_response.usage = MagicMock(total_tokens=150)
    return mock_response


@pytest.fixture
def sample_chunk():
    """Create a sample chunk for testing."""
    return ChunkInDB(
        id=uuid4(),
        document_id=uuid4(),
        chunk_index=0,
        text="This is a test chunk for embedding.",
        token_count=10,
        metadata={"doc_type": "test"},
        created_at=datetime.utcnow()
    )


@pytest.mark.asyncio
async def test_generate_embedding(mock_openai_response):
    """Test single embedding generation."""
    with patch('app.services.embedding_service.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_openai_response)
        mock_client_class.return_value = mock_client
        
        service = EmbeddingService()
        embedding = await service.generate_embedding("test text")
        
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        mock_client.embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_batch(mock_batch_openai_response):
    """Test batch embedding generation."""
    with patch('app.services.embedding_service.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_batch_openai_response)
        mock_client_class.return_value = mock_client
        
        service = EmbeddingService()
        texts = ["text 1", "text 2", "text 3"]
        embeddings = await service.generate_embeddings_batch(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)
        mock_client.embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_batch_empty():
    """Test batch embedding with empty list."""
    service = EmbeddingService()
    embeddings = await service.generate_embeddings_batch([])
    
    assert embeddings == []


@pytest.mark.asyncio
async def test_embed_chunk_new(sample_chunk, mock_openai_response):
    """Test embedding a chunk that doesn't have an embedding yet."""
    with patch('app.services.embedding_service.AsyncOpenAI') as mock_client_class, \
         patch('app.services.embedding_service.get_db_service') as mock_db:
        
        # Mock OpenAI client
        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_openai_response)
        mock_client_class.return_value = mock_client
        
        # Mock database service
        mock_db_instance = AsyncMock()
        mock_db_instance.get_embedding = AsyncMock(return_value=None)  # No existing embedding
        
        created_embedding = EmbeddingInDB(
            id=uuid4(),
            chunk_id=sample_chunk.id,
            vector=[0.1] * 1536,
            model_name="text-embedding-3-small",
            created_at=datetime.utcnow()
        )
        mock_db_instance.create_embedding = AsyncMock(return_value=created_embedding)
        mock_db.return_value = mock_db_instance
        
        service = EmbeddingService()
        result = await service.embed_chunk(sample_chunk)
        
        assert result.chunk_id == sample_chunk.id
        assert len(result.vector) == 1536
        mock_db_instance.create_embedding.assert_called_once()


@pytest.mark.asyncio
async def test_embed_chunk_existing(sample_chunk):
    """Test embedding a chunk that already has an embedding (idempotency)."""
    with patch('app.services.embedding_service.AsyncOpenAI') as mock_client_class, \
         patch('app.services.embedding_service.get_db_service') as mock_db:
        
        # Mock OpenAI client (should NOT be called)
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock database service
        existing_embedding = EmbeddingInDB(
            id=uuid4(),
            chunk_id=sample_chunk.id,
            vector=[0.1] * 1536,
            model_name="text-embedding-3-small",
            created_at=datetime.utcnow()
        )
        
        mock_db_instance = AsyncMock()
        mock_db_instance.get_embedding = AsyncMock(return_value=existing_embedding)
        mock_db.return_value = mock_db_instance
        
        service = EmbeddingService()
        result = await service.embed_chunk(sample_chunk)
        
        assert result == existing_embedding
        # OpenAI API should NOT have been called
        mock_client.embeddings.create.assert_not_called()


@pytest.mark.asyncio
async def test_embed_chunk_force_regenerate(sample_chunk, mock_openai_response):
    """Test force regenerating an embedding."""
    with patch('app.services.embedding_service.AsyncOpenAI') as mock_client_class, \
         patch('app.services.embedding_service.get_db_service') as mock_db:
        
        # Mock OpenAI client
        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_openai_response)
        mock_client_class.return_value = mock_client
        
        # Mock database service
        existing_embedding = EmbeddingInDB(
            id=uuid4(),
            chunk_id=sample_chunk.id,
            vector=[0.1] * 1536,
            model_name="text-embedding-3-small",
            created_at=datetime.utcnow()
        )
        
        new_embedding = EmbeddingInDB(
            id=uuid4(),
            chunk_id=sample_chunk.id,
            vector=[0.2] * 1536,
            model_name="text-embedding-3-small",
            created_at=datetime.utcnow()
        )
        
        mock_db_instance = AsyncMock()
        mock_db_instance.get_embedding = AsyncMock(return_value=existing_embedding)
        mock_db_instance.create_embedding = AsyncMock(return_value=new_embedding)
        mock_db.return_value = mock_db_instance
        
        service = EmbeddingService()
        result = await service.embed_chunk(sample_chunk, force_regenerate=True)
        
        # Should have called OpenAI even though embedding exists
        mock_client.embeddings.create.assert_called_once()
        mock_db_instance.create_embedding.assert_called_once()


@pytest.mark.asyncio
async def test_embed_chunks_batch(mock_batch_openai_response):
    """Test embedding multiple chunks in batch."""
    chunks = [
        ChunkInDB(
            id=uuid4(),
            document_id=uuid4(),
            chunk_index=i,
            text=f"Chunk {i}",
            metadata={},
            created_at=datetime.utcnow()
        )
        for i in range(3)
    ]
    
    with patch('app.services.embedding_service.AsyncOpenAI') as mock_client_class, \
         patch('app.services.embedding_service.get_db_service') as mock_db:
        
        # Mock OpenAI client
        mock_client = AsyncMock()
        mock_client.embeddings.create = AsyncMock(return_value=mock_batch_openai_response)
        mock_client_class.return_value = mock_client
        
        # Mock database service
        mock_db_instance = AsyncMock()
        mock_db_instance.get_embedding = AsyncMock(return_value=None)  # No existing embeddings
        
        created_embeddings = [
            EmbeddingInDB(
                id=uuid4(),
                chunk_id=chunk.id,
                vector=[0.1 * (i+1)] * 1536,
                model_name="text-embedding-3-small",
                created_at=datetime.utcnow()
            )
            for i, chunk in enumerate(chunks)
        ]
        
        mock_db_instance.create_embedding = AsyncMock(side_effect=created_embeddings)
        mock_db.return_value = mock_db_instance
        
        service = EmbeddingService()
        results = await service.embed_chunks(chunks)
        
        assert len(results) == 3
        assert all(isinstance(r, EmbeddingInDB) for r in results)
        # Should use batch API
        mock_client.embeddings.create.assert_called_once()


@pytest.mark.asyncio
async def test_embed_chunks_skip_existing():
    """Test that embed_chunks skips chunks with existing embeddings."""
    chunks = [
        ChunkInDB(
            id=uuid4(),
            document_id=uuid4(),
            chunk_index=i,
            text=f"Chunk {i}",
            metadata={},
            created_at=datetime.utcnow()
        )
        for i in range(3)
    ]
    
    with patch('app.services.embedding_service.AsyncOpenAI') as mock_client_class, \
         patch('app.services.embedding_service.get_db_service') as mock_db:
        
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # First chunk has existing embedding, others don't
        existing_embedding = EmbeddingInDB(
            id=uuid4(),
            chunk_id=chunks[0].id,
            vector=[0.1] * 1536,
            model_name="text-embedding-3-small",
            created_at=datetime.utcnow()
        )
        
        mock_db_instance = AsyncMock()
        
        async def mock_get_embedding(chunk_id, model_name):
            if chunk_id == chunks[0].id:
                return existing_embedding
            return None
        
        mock_db_instance.get_embedding = AsyncMock(side_effect=mock_get_embedding)
        mock_db.return_value = mock_db_instance
        
        service = EmbeddingService()
        results = await service.embed_chunks(chunks, skip_existing=True)
        
        # Should have called get_embedding for all chunks
        assert mock_db_instance.get_embedding.call_count == 3


def test_embedding_service_initialization():
    """Test service initialization with default and custom parameters."""
    # Default initialization
    service1 = EmbeddingService()
    assert service1.model_name == "text-embedding-3-small"
    assert service1.expected_dimensions == 1536
    assert service1.batch_size == 100
    
    # Custom initialization
    service2 = EmbeddingService(model_name="text-embedding-ada-002", batch_size=50)
    assert service2.model_name == "text-embedding-ada-002"
    assert service2.batch_size == 50
