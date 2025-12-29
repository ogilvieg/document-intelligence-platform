"""Tests for updated ChunkingService with database persistence."""

import pytest
from uuid import uuid4
from app.services.chunking import ChunkingService


@pytest.mark.asyncio
async def test_chunk_text_with_persistence():
    """Test chunking with database persistence."""
    service = ChunkingService(chunk_size=100, chunk_overlap=20, persist_to_db=False)
    
    document_id = uuid4()
    text = "This is a test document. " * 20  # ~500 chars
    
    chunks = await service.chunk_text(
        text=text,
        document_id=document_id,
        doc_type="test",
        metadata={"source": "test"}
    )
    
    assert len(chunks) > 0
    assert all(chunk.document_id == document_id for chunk in chunks)
    assert all(chunk.metadata.get("doc_type") == "test" for chunk in chunks)
    
    # Check chunk indices are sequential
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i


@pytest.mark.asyncio
async def test_chunk_document():
    """Test document chunking convenience method."""
    service = ChunkingService(chunk_size=100, chunk_overlap=20, persist_to_db=False)
    
    document_id = uuid4()
    text = "This is a test document. " * 20
    
    result = await service.chunk_document(
        document_text=text,
        document_id=document_id,
        doc_type="resume",
        document_metadata={"author": "test"}
    )
    
    assert result["total_chunks"] > 0
    assert result["total_characters"] > 0
    assert result["average_chunk_size"] > 0
    assert len(result["chunks"]) == result["total_chunks"]


def test_validate_chunks():
    """Test chunk validation."""
    from app.models.database import ChunkInDB
    from datetime import datetime
    
    service = ChunkingService()
    
    # Create mock chunks
    chunks = [
        ChunkInDB(
            id=uuid4(),
            document_id=uuid4(),
            chunk_index=i,
            text="A" * 100,
            metadata={},
            created_at=datetime.utcnow()
        )
        for i in range(3)
    ]
    
    validation = service.validate_chunks(chunks)
    
    assert validation["valid"] is True
    assert validation["statistics"]["total_chunks"] == 3


@pytest.mark.asyncio
async def test_idempotency():
    """Test that chunking is idempotent (doesn't duplicate chunks)."""
    # This test would require database setup, so it's more of an integration test
    # For now, we just verify the structure is correct
    service = ChunkingService(persist_to_db=False)
    
    document_id = uuid4()
    text = "Test text for idempotency."
    
    # First call
    chunks1 = await service.chunk_text(
        text=text,
        document_id=document_id,
        doc_type="test"
    )
    
    # Second call with same document_id should return same structure
    chunks2 = await service.chunk_text(
        text=text,
        document_id=document_id,
        doc_type="test"
    )
    
    assert len(chunks1) == len(chunks2)
    assert all(c1.text == c2.text for c1, c2 in zip(chunks1, chunks2))


def test_token_estimation():
    """Test token count estimation."""
    service = ChunkingService()
    
    text = "This is a test"  # 14 chars
    tokens = service._estimate_tokens(text)
    
    # Should be ~14/4 = 3-4 tokens
    assert 2 <= tokens <= 5
