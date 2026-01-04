"""Tests for LLMService RAG functionality with chunk-based analysis."""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.llm_service import LLMService
from app.models.database import ChunkInDB, RetrievedChunk
from app.models.schemas import Citation
from app.models import AnalysisOutput


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing."""
    doc_id = uuid4()
    return [
        ChunkInDB(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=0,
            text="The candidate has 5 years of Python experience with Django and Flask frameworks.",
            token_count=15,
            metadata={"page": 1},
            created_at=datetime.utcnow()
        ),
        ChunkInDB(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=1,
            text="Led a team of 3 developers on a microservices project using Docker and Kubernetes.",
            token_count=15,
            metadata={"page": 1},
            created_at=datetime.utcnow()
        ),
        ChunkInDB(
            id=uuid4(),
            document_id=doc_id,
            chunk_index=2,
            text="Strong background in machine learning with TensorFlow and PyTorch. Published 2 papers.",
            token_count=15,
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
            document_title="Senior Python Engineer Resume",
            document_type="resume"
        ),
        RetrievedChunk(
            chunk=sample_chunks[1],
            similarity_score=0.88,
            document_title="Senior Python Engineer Resume",
            document_type="resume"
        ),
        RetrievedChunk(
            chunk=sample_chunks[2],
            similarity_score=0.82,
            document_title="Senior Python Engineer Resume",
            document_type="resume"
        ),
    ]


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for chunk-based analysis."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """{
        "overall_fit": "Strong candidate with relevant Python and ML experience",
        "strengths": ["5 years Python experience", "Team leadership", "ML expertise"],
        "gaps": ["No cloud architecture experience mentioned"],
        "risk_factors": ["Limited team size in previous role"],
        "confidence": 0.85,
        "recommended_focus": ["Assess cloud architecture skills", "Validate ML project outcomes"]
    }"""
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 500
    mock_response.usage.completion_tokens = 150
    mock_response.usage.total_tokens = 650
    return mock_response


def test_create_chunk_based_prompt(sample_retrieved_chunks):
    """Test chunk-based prompt creation."""
    llm_service = LLMService()
    
    prompt = llm_service._create_chunk_based_prompt(
        query="Evaluate this candidate for a senior Python role",
        chunks=sample_retrieved_chunks,
        options=None
    )
    
    # Verify prompt includes query
    assert "Evaluate this candidate for a senior Python role" in prompt
    
    # Verify prompt includes all chunks
    assert "[CHUNK 1]" in prompt
    assert "[CHUNK 2]" in prompt
    assert "[CHUNK 3]" in prompt
    
    # Verify chunk content is included
    assert "5 years of Python experience" in prompt
    assert "Led a team of 3 developers" in prompt
    assert "machine learning with TensorFlow" in prompt
    
    # Verify metadata is included
    assert "Senior Python Engineer Resume" in prompt
    assert "resume" in prompt
    assert "0.95" in prompt  # Similarity score
    assert "0.88" in prompt
    assert "0.82" in prompt


def test_create_chunk_based_prompt_with_options(sample_retrieved_chunks):
    """Test chunk-based prompt with custom options."""
    llm_service = LLMService()
    
    options = {"focus_area": "technical_skills"}
    prompt = llm_service._create_chunk_based_prompt(
        query="Evaluate candidate",
        chunks=sample_retrieved_chunks,
        options=options
    )
    
    # Verify options are included
    assert "focus_area" in prompt
    assert "technical_skills" in prompt


def test_analyze_with_chunks_success(sample_retrieved_chunks, mock_openai_response):
    """Test successful chunk-based analysis."""
    llm_service = LLMService()
    
    with patch.object(llm_service.client.chat.completions, 'create', return_value=mock_openai_response):
        output, citations, metadata = llm_service.analyze_with_chunks(
            query="Evaluate this candidate",
            chunks=sample_retrieved_chunks,
            temperature=0.7
        )
        
        # Verify output
        assert isinstance(output, AnalysisOutput)
        assert output.overall_fit == "Strong candidate with relevant Python and ML experience"
        assert len(output.strengths) == 3
        assert output.confidence == 0.85
        
        # Verify citations
        assert len(citations) == 3
        assert all(isinstance(c, Citation) for c in citations)
        assert citations[0].relevance_score == 0.95
        assert citations[1].relevance_score == 0.88
        assert citations[2].relevance_score == 0.82
        
        # Verify metadata
        assert metadata["prompt_tokens"] == 500
        assert metadata["completion_tokens"] == 150
        assert metadata["total_tokens"] == 650
        assert metadata["chunks_used"] == 3
        assert "latency_ms" in metadata


def test_analyze_with_chunks_creates_citations(sample_retrieved_chunks, mock_openai_response):
    """Test that citations are created from chunks."""
    llm_service = LLMService()
    
    with patch.object(llm_service.client.chat.completions, 'create', return_value=mock_openai_response):
        _, citations, _ = llm_service.analyze_with_chunks(
            query="Test query",
            chunks=sample_retrieved_chunks
        )
        
        # Verify each chunk has a citation
        assert len(citations) == len(sample_retrieved_chunks)
        
        # Verify citation details
        for i, citation in enumerate(citations):
            assert citation.chunk_id == sample_retrieved_chunks[i].chunk.id
            assert citation.document_id == sample_retrieved_chunks[i].chunk.document_id
            assert citation.document_title == sample_retrieved_chunks[i].document_title
            assert citation.chunk_text == sample_retrieved_chunks[i].chunk.text
            assert citation.relevance_score == sample_retrieved_chunks[i].similarity_score


def test_create_citations(sample_retrieved_chunks):
    """Test citation creation from chunks."""
    llm_service = LLMService()
    
    citations = llm_service._create_citations(sample_retrieved_chunks)
    
    assert len(citations) == 3
    
    # Verify first citation
    assert citations[0].chunk_id == sample_retrieved_chunks[0].chunk.id
    assert citations[0].document_id == sample_retrieved_chunks[0].chunk.document_id
    assert citations[0].document_title == "Senior Python Engineer Resume"
    assert citations[0].relevance_score == 0.95
    assert "5 years of Python experience" in citations[0].chunk_text


def test_analyze_with_chunks_handles_validation_error(sample_retrieved_chunks):
    """Test handling of validation errors in chunk-based analysis."""
    llm_service = LLMService()
    
    # Mock response with invalid schema (missing required fields)
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """{
        "overall_fit": "Test",
        "confidence": 0.5
    }"""
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50
    mock_response.usage.total_tokens = 150
    
    with patch.object(llm_service.client.chat.completions, 'create', return_value=mock_response):
        # Should raise ValidationError after retries
        with pytest.raises(Exception):  # Will be ValidationError from Pydantic
            llm_service.analyze_with_chunks(
                query="Test",
                chunks=sample_retrieved_chunks
            )


def test_analyze_with_chunks_handles_json_error(sample_retrieved_chunks):
    """Test handling of JSON parsing errors."""
    llm_service = LLMService()
    
    # Mock response with invalid JSON
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Not valid JSON {{"
    
    with patch.object(llm_service.client.chat.completions, 'create', return_value=mock_response):
        # Should raise JSONDecodeError after retries
        with pytest.raises(Exception):
            llm_service.analyze_with_chunks(
                query="Test",
                chunks=sample_retrieved_chunks
            )


def test_analyze_with_chunks_temperature(sample_retrieved_chunks, mock_openai_response):
    """Test that temperature parameter is passed correctly."""
    llm_service = LLMService()
    
    with patch.object(llm_service.client.chat.completions, 'create', return_value=mock_openai_response) as mock_create:
        llm_service.analyze_with_chunks(
            query="Test",
            chunks=sample_retrieved_chunks,
            temperature=0.3
        )
        
        # Verify temperature was passed
        call_args = mock_create.call_args
        assert call_args[1]['temperature'] == 0.3


def test_analyze_with_chunks_with_options(sample_retrieved_chunks, mock_openai_response):
    """Test chunk-based analysis with custom options."""
    llm_service = LLMService()
    
    options = {"focus_area": "leadership"}
    
    with patch.object(llm_service.client.chat.completions, 'create', return_value=mock_openai_response) as mock_create:
        llm_service.analyze_with_chunks(
            query="Evaluate leadership skills",
            chunks=sample_retrieved_chunks,
            options=options
        )
        
        # Verify options were included in prompt
        call_args = mock_create.call_args
        prompt = call_args[1]['messages'][1]['content']
        assert "leadership" in prompt


def test_analyze_with_chunks_logs_chunk_details(sample_retrieved_chunks, mock_openai_response):
    """Test that chunk details are logged for traceability."""
    llm_service = LLMService()
    
    with patch.object(llm_service.client.chat.completions, 'create', return_value=mock_openai_response):
        with patch('app.services.llm_service.logger') as mock_logger:
            llm_service.analyze_with_chunks(
                query="Test",
                chunks=sample_retrieved_chunks
            )
            
            # Verify analysis started was logged
            assert any(
                call[0][0] == "chunk_based_analysis_started" 
                for call in mock_logger.info.call_args_list
            )
            
            # Verify chunk details were logged
            assert any(
                call[0][0] == "chunk_used_in_prompt" 
                for call in mock_logger.debug.call_args_list
            )


def test_analyze_with_empty_chunks(mock_openai_response):
    """Test analysis with no chunks."""
    llm_service = LLMService()
    
    with patch.object(llm_service.client.chat.completions, 'create', return_value=mock_openai_response):
        output, citations, metadata = llm_service.analyze_with_chunks(
            query="Test with no chunks",
            chunks=[]
        )
        
        # Should still work but with no citations
        assert isinstance(output, AnalysisOutput)
        assert len(citations) == 0
        assert metadata["chunks_used"] == 0


def test_backward_compatibility_original_method(mock_openai_response):
    """Test that original analyze_with_llm method still works."""
    llm_service = LLMService()
    
    with patch.object(llm_service.client.chat.completions, 'create', return_value=mock_openai_response):
        # Original method should still work
        output, metadata = llm_service.analyze_with_llm(
            context="Test document content",
            temperature=0.7
        )
        
        assert isinstance(output, AnalysisOutput)
        assert "latency_ms" in metadata
        assert "total_tokens" in metadata


def test_citation_traceability(sample_retrieved_chunks, mock_openai_response):
    """Test full traceability chain from chunks to citations."""
    llm_service = LLMService()
    
    with patch.object(llm_service.client.chat.completions, 'create', return_value=mock_openai_response):
        _, citations, _ = llm_service.analyze_with_chunks(
            query="Evaluate candidate",
            chunks=sample_retrieved_chunks
        )
        
        # Verify we can trace back to original chunks
        for i, citation in enumerate(citations):
            original_chunk = sample_retrieved_chunks[i].chunk
            
            # Verify IDs match
            assert citation.chunk_id == original_chunk.id
            assert citation.document_id == original_chunk.document_id
            
            # Verify text matches
            assert citation.chunk_text == original_chunk.text
            
            # Verify similarity score is preserved
            assert citation.relevance_score == sample_retrieved_chunks[i].similarity_score
