"""Unit tests for chunking service."""

import pytest
from uuid import uuid4
from app.services.chunking import ChunkingService


@pytest.fixture
def chunking_service():
    """Create a chunking service instance with default settings."""
    return ChunkingService(chunk_size=100, chunk_overlap=20)


@pytest.fixture
def small_chunking_service():
    """Create a chunking service with small chunks for testing."""
    return ChunkingService(chunk_size=50, chunk_overlap=10)


def test_initialization(chunking_service):
    """Test chunking service initialization."""
    assert chunking_service.chunk_size == 100
    assert chunking_service.chunk_overlap == 20


def test_initialization_invalid_overlap():
    """Test that overlap >= chunk_size raises error."""
    with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
        ChunkingService(chunk_size=100, chunk_overlap=100)
    
    with pytest.raises(ValueError, match="chunk_overlap must be less than chunk_size"):
        ChunkingService(chunk_size=100, chunk_overlap=150)


def test_chunk_text_simple(chunking_service):
    """Test basic text chunking."""
    text = "This is a simple test. " * 10  # ~240 chars
    document_id = uuid4()
    
    chunks = chunking_service.chunk_text(text, document_id)
    
    assert len(chunks) > 0
    assert all('id' in chunk for chunk in chunks)
    assert all('document_id' in chunk for chunk in chunks)
    assert all('chunk_index' in chunk for chunk in chunks)
    assert all('text' in chunk for chunk in chunks)
    assert all(chunk['document_id'] == document_id for chunk in chunks)
    
    # Check indices are sequential
    for i, chunk in enumerate(chunks):
        assert chunk['chunk_index'] == i


def test_chunk_text_empty(chunking_service):
    """Test chunking with empty text."""
    document_id = uuid4()
    
    # Empty string
    chunks = chunking_service.chunk_text("", document_id)
    assert len(chunks) == 0
    
    # Whitespace only
    chunks = chunking_service.chunk_text("   \n\n  ", document_id)
    assert len(chunks) == 0


def test_chunk_text_short(chunking_service):
    """Test chunking with text shorter than chunk_size."""
    text = "Short text"
    document_id = uuid4()
    
    chunks = chunking_service.chunk_text(text, document_id)
    
    assert len(chunks) == 1
    assert chunks[0]['text'] == text
    assert chunks[0]['chunk_index'] == 0


def test_chunk_text_overlap(small_chunking_service):
    """Test that chunks have proper overlap."""
    # Create text with clear markers
    text = "AAAA BBBB CCCC DDDD EEEE FFFF GGGG HHHH IIII JJJJ KKKK LLLL"
    document_id = uuid4()
    
    chunks = small_chunking_service.chunk_text(text, document_id)
    
    # Should have multiple chunks
    assert len(chunks) > 1
    
    # Check that consecutive chunks have overlapping content
    for i in range(len(chunks) - 1):
        current_text = chunks[i]['text']
        next_text = chunks[i + 1]['text']
        
        # The end of current chunk should appear near start of next chunk
        # (due to overlap)
        current_end = current_text[-15:] if len(current_text) >= 15 else current_text
        # At least some overlap should exist
        assert any(word in next_text for word in current_end.split())


def test_chunk_text_sentence_boundaries(chunking_service):
    """Test that chunking tries to break at sentence boundaries."""
    text = (
        "This is the first sentence. "
        "This is the second sentence. "
        "This is the third sentence. "
        "This is the fourth sentence. "
        "This is the fifth sentence. "
        "This is the sixth sentence."
    )
    document_id = uuid4()
    
    chunks = chunking_service.chunk_text(text, document_id)
    
    # Most chunks should end with sentence punctuation
    chunks_ending_with_sentence = sum(
        1 for chunk in chunks
        if chunk['text'].rstrip().endswith(('.', '!', '?'))
    )
    
    # At least some chunks should respect sentence boundaries
    assert chunks_ending_with_sentence > 0


def test_chunk_text_with_metadata(chunking_service):
    """Test that metadata is attached to chunks."""
    text = "Test text. " * 20
    document_id = uuid4()
    metadata = {'source': 'test', 'type': 'markdown'}
    
    chunks = chunking_service.chunk_text(text, document_id, metadata)
    
    assert all('metadata' in chunk for chunk in chunks)
    assert all(chunk['metadata'] == metadata for chunk in chunks)


def test_chunk_text_start_end_positions(small_chunking_service):
    """Test that start_char and end_char are tracked correctly."""
    text = "0123456789" * 10  # 100 chars
    document_id = uuid4()
    
    chunks = small_chunking_service.chunk_text(text, document_id)
    
    # All chunks should have start and end positions
    assert all('start_char' in chunk for chunk in chunks)
    assert all('end_char' in chunk for chunk in chunks)
    
    # First chunk should start at 0
    assert chunks[0]['start_char'] == 0
    
    # Each chunk's positions should be within text bounds
    for chunk in chunks:
        assert 0 <= chunk['start_char'] < len(text)
        assert 0 < chunk['end_char'] <= len(text)
        assert chunk['start_char'] < chunk['end_char']


def test_chunk_document(chunking_service):
    """Test the chunk_document convenience method."""
    text = "This is a test document. " * 20
    document_id = uuid4()
    metadata = {'parser': 'test'}
    
    result = chunking_service.chunk_document(text, document_id, metadata)
    
    # Check structure
    assert 'document_id' in result
    assert 'chunks' in result
    assert 'total_chunks' in result
    assert 'total_characters' in result
    assert 'average_chunk_size' in result
    assert 'chunk_size_config' in result
    assert 'chunk_overlap_config' in result
    
    # Check values
    assert result['document_id'] == document_id
    assert result['total_chunks'] == len(result['chunks'])
    assert result['total_chunks'] > 0
    assert result['average_chunk_size'] > 0
    assert result['chunk_size_config'] == chunking_service.chunk_size
    assert result['chunk_overlap_config'] == chunking_service.chunk_overlap


def test_chunk_document_empty(chunking_service):
    """Test chunk_document with empty text."""
    document_id = uuid4()
    
    result = chunking_service.chunk_document("", document_id)
    
    assert result['total_chunks'] == 0
    assert result['total_characters'] == 0
    assert result['average_chunk_size'] == 0
    assert len(result['chunks']) == 0


def test_validate_chunks(chunking_service):
    """Test chunk validation."""
    text = "Test sentence. " * 20
    document_id = uuid4()
    
    chunks = chunking_service.chunk_text(text, document_id)
    validation = chunking_service.validate_chunks(chunks)
    
    assert 'valid' in validation
    assert 'warnings' in validation
    assert 'statistics' in validation
    assert validation['valid'] is True
    
    # Check statistics
    stats = validation['statistics']
    assert 'total_chunks' in stats
    assert 'min_size' in stats
    assert 'max_size' in stats
    assert 'avg_size' in stats
    assert 'has_overlap' in stats


def test_validate_chunks_empty(chunking_service):
    """Test validation with empty chunks list."""
    validation = chunking_service.validate_chunks([])
    
    assert validation['valid'] is True
    assert len(validation['warnings']) == 0


def test_validate_chunks_warnings(small_chunking_service):
    """Test that validation generates appropriate warnings."""
    # Create chunks with no overlap
    document_id = uuid4()
    chunks_no_overlap = [
        {
            'id': uuid4(),
            'document_id': document_id,
            'chunk_index': 0,
            'text': 'First chunk here.',
            'metadata': {}
        },
        {
            'id': uuid4(),
            'document_id': document_id,
            'chunk_index': 1,
            'text': 'Second chunk different.',
            'metadata': {}
        }
    ]
    
    validation = small_chunking_service.validate_chunks(chunks_no_overlap)
    
    # Should warn about no overlap
    assert any('overlap' in warning.lower() for warning in validation['warnings'])


def test_large_document_chunking():
    """Test chunking a large document."""
    # Create a large document (10KB)
    text = "This is sentence number {}. " * 400
    text = text.format(*range(400))
    
    service = ChunkingService(chunk_size=512, chunk_overlap=50)
    document_id = uuid4()
    
    result = service.chunk_document(text, document_id)
    
    # Should create multiple chunks
    assert result['total_chunks'] > 5
    
    # All chunks should be reasonably sized
    for chunk in result['chunks']:
        assert len(chunk['text']) > 0
        assert len(chunk['text']) <= service.chunk_size * 1.5  # Allow some flexibility


def test_chunk_text_special_characters(chunking_service):
    """Test chunking with special characters and unicode."""
    text = "Hello 世界! " * 20 + "Émoji test 🎉🎊. " * 10
    document_id = uuid4()
    
    chunks = chunking_service.chunk_text(text, document_id)
    
    # Should handle special characters without errors
    assert len(chunks) > 0
    
    # Join all chunks and verify content is preserved
    rejoined = " ".join(chunk['text'] for chunk in chunks)
    assert "世界" in rejoined
    assert "Émoji" in rejoined
    assert "🎉" in rejoined or "🎊" in rejoined  # At least one emoji


def test_chunk_text_multiline(chunking_service):
    """Test chunking with multiline text."""
    text = """Line 1 here.
Line 2 here.
Line 3 here.

Paragraph 2 starts here.
More content in paragraph 2.

Final paragraph."""
    
    document_id = uuid4()
    chunks = chunking_service.chunk_text(text, document_id)
    
    # Should create chunks
    assert len(chunks) > 0
    
    # Verify newlines are preserved
    rejoined = "\n".join(chunk['text'] for chunk in chunks)
    assert "Line 1" in rejoined
    assert "Paragraph 2" in rejoined
