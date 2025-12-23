"""Pydantic models for request/response validation."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
    OTHER = "other"


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    title: str = Field(..., min_length=1, max_length=255)
    type: DocumentType
    source: Optional[str] = None


class DocumentResponse(BaseModel):
    """Response model for document."""
    id: UUID
    title: str
    type: DocumentType
    source: Optional[str] = None
    version: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    """Request model for analysis run."""
    document_ids: List[UUID] = Field(..., min_items=1)
    options: Optional[Dict[str, Any]] = None


class AnalysisOutput(BaseModel):
    """Structured output model for analysis results."""
    overall_fit: str = Field(..., description="Overall assessment of fit/quality")
    strengths: List[str] = Field(..., description="Key strengths identified")
    gaps: List[str] = Field(..., description="Gaps or areas for improvement")
    risk_factors: List[str] = Field(..., description="Potential risks or concerns")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    recommended_focus: List[str] = Field(..., description="Recommended areas of focus")


class Citation(BaseModel):
    """Citation model linking output to source chunks."""
    chunk_id: UUID
    document_id: UUID
    document_title: str
    chunk_text: str
    relevance_score: float


class AnalysisResponse(BaseModel):
    """Response model for analysis run."""
    id: UUID
    output: AnalysisOutput
    citations: List[Citation]
    latency_ms: int
    cost: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
