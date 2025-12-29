"""LLM service for OpenAI integration with schema validation."""

import json
import time
from typing import Optional, Dict, Any
import structlog
from openai import OpenAI
from pydantic import ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.config import settings
from app.models import AnalysisOutput

logger = structlog.get_logger()


class LLMService:
    """Service for interacting with OpenAI LLM with schema validation and retry logic."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_retries = 3
        
    def _create_analysis_prompt(self, context: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a structured prompt for document analysis.
        
        Args:
            context: The document text or context to analyze
            options: Optional parameters to customize analysis
            
        Returns:
            Formatted prompt string
        """
        base_prompt = f"""You are an expert document analyst. Analyze the following document content and provide a structured assessment.

Document Content:
{context}

Provide your analysis in the following JSON format:
{{
    "overall_fit": "A concise summary of the overall assessment (2-3 sentences)",
    "strengths": ["List", "of", "key", "strengths", "identified"],
    "gaps": ["List", "of", "gaps", "or", "areas", "for", "improvement"],
    "risk_factors": ["List", "of", "potential", "risks", "or", "concerns"],
    "confidence": 0.85,
    "recommended_focus": ["List", "of", "recommended", "focus", "areas"]
}}

Important:
- confidence must be a number between 0.0 and 1.0
- All lists should contain at least one item
- Be specific and actionable in your recommendations
- Return ONLY valid JSON, no additional text
"""
        
        if options:
            base_prompt += f"\n\nAdditional instructions: {json.dumps(options)}"
            
        return base_prompt
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ValidationError, json.JSONDecodeError)),
        reraise=True
    )
    def analyze_with_llm(
        self,
        context: str,
        options: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7
    ) -> tuple[AnalysisOutput, Dict[str, Any]]:
        """
        Analyze document context using LLM with schema validation and automatic retries.
        
        Args:
            context: Document text or context to analyze
            options: Optional parameters for customization
            temperature: LLM temperature (0.0-1.0)
            
        Returns:
            Tuple of (validated AnalysisOutput, metadata dict with latency and tokens)
            
        Raises:
            ValidationError: If LLM output doesn't match schema after max retries
            Exception: For other OpenAI API errors
        """
        start_time = time.time()
        
        prompt = self._create_analysis_prompt(context, options)
        
        logger.info(
            "llm_analysis_started",
            model=self.model,
            context_length=len(context),
            temperature=temperature
        )
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise document analyst that returns only valid JSON responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                response_format={"type": "json_object"}  # Enforce JSON response
            )
            
            # Extract response
            raw_output = response.choices[0].message.content
            
            # Parse JSON
            try:
                output_dict = json.loads(raw_output)
            except json.JSONDecodeError as e:
                logger.error("llm_json_parse_failed", error=str(e), raw_output=raw_output)
                raise
            
            # Validate against Pydantic schema
            try:
                validated_output = AnalysisOutput(**output_dict)
            except ValidationError as e:
                logger.error("llm_schema_validation_failed", error=str(e), output=output_dict)
                raise
            
            # Calculate metadata
            latency_ms = int((time.time() - start_time) * 1000)
            
            metadata = {
                "latency_ms": latency_ms,
                "model": self.model,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason
            }
            
            logger.info(
                "llm_analysis_completed",
                latency_ms=latency_ms,
                total_tokens=metadata["total_tokens"],
                confidence=validated_output.confidence
            )
            
            return validated_output, metadata
            
        except ValidationError:
            # Let tenacity retry handle this
            raise
        except json.JSONDecodeError:
            # Let tenacity retry handle this
            raise
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.error(
                "llm_analysis_failed",
                error=str(e),
                error_type=type(e).__name__,
                latency_ms=latency_ms
            )
            raise
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate cost of API call based on token usage.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Estimated cost in USD
        """
        # GPT-4 Turbo pricing (as of Dec 2024)
        # Adjust these values based on actual pricing
        prompt_cost_per_1k = 0.01  # $0.01 per 1K prompt tokens
        completion_cost_per_1k = 0.03  # $0.03 per 1K completion tokens
        
        prompt_cost = (prompt_tokens / 1000) * prompt_cost_per_1k
        completion_cost = (completion_tokens / 1000) * completion_cost_per_1k
        
        return prompt_cost + completion_cost
