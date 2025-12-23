"""Tests for LLM service."""

import pytest
from app.services.llm_service import LLMService
from app.models import AnalysisOutput
from pydantic import ValidationError


class TestLLMService:
    """Test suite for LLM service."""
    
    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance."""
        return LLMService()
    
    def test_create_analysis_prompt(self, llm_service):
        """Test prompt creation."""
        context = "This is a test document about AI systems."
        prompt = llm_service._create_analysis_prompt(context)
        
        assert "test document" in prompt
        assert "JSON format" in prompt
        assert "overall_fit" in prompt
        
    def test_create_analysis_prompt_with_options(self, llm_service):
        """Test prompt creation with options."""
        context = "Test content"
        options = {"focus_area": "technical accuracy"}
        prompt = llm_service._create_analysis_prompt(context, options)
        
        assert "technical accuracy" in prompt
        
    def test_estimate_cost(self, llm_service):
        """Test cost estimation."""
        cost = llm_service.estimate_cost(
            prompt_tokens=1000,
            completion_tokens=500
        )
        
        assert cost > 0
        assert isinstance(cost, float)
        # GPT-4 Turbo: ~$0.01 per 1K prompt + ~$0.03 per 1K completion
        # 1000 * 0.01/1000 + 500 * 0.03/1000 = 0.01 + 0.015 = 0.025
        assert 0.02 < cost < 0.03
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires OpenAI API key and costs money")
    async def test_analyze_with_llm_integration(self, llm_service):
        """Integration test for LLM analysis (skipped by default)."""
        context = """
        Project: Document Intelligence Platform
        Description: An AI system that ingests documents, performs retrieval,
        and returns structured outputs with traceability.
        """
        
        output, metadata = llm_service.analyze_with_llm(context)
        
        # Verify output structure
        assert isinstance(output, AnalysisOutput)
        assert output.overall_fit
        assert len(output.strengths) > 0
        assert 0.0 <= output.confidence <= 1.0
        
        # Verify metadata
        assert metadata['latency_ms'] > 0
        assert metadata['total_tokens'] > 0
        assert metadata['model'] == llm_service.model
