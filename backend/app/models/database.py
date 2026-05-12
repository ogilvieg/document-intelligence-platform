"""Database models and schemas for documents, chunks, and embeddings."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field


# ============= Document Models =============

class DocumentBase(BaseModel):
    """Base document model."""
    title: str
    doc_type: str = Field(..., description="Document type: resume, jd, policy, etc.")
    source: Optional[str] = None
    version: str = "1.0"
    content_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    filename: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None


class DocumentInDB(DocumentBase):
    """Document as stored in database."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentWithChunks(DocumentInDB):
    """Document with its chunks included."""
    chunks: List["ChunkInDB"] = []


# ============= Chunk Models =============

class ChunkBase(BaseModel):
    """Base chunk model."""
    document_id: UUID
    chunk_index: int
    text: str
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChunkCreate(ChunkBase):
    """Schema for creating a new chunk."""
    pass


class ChunkInDB(ChunkBase):
    """Chunk as stored in database."""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChunkWithEmbedding(ChunkInDB):
    """Chunk with its embedding included."""
    embedding: Optional["EmbeddingInDB"] = None


# ============= Embedding Models =============

class EmbeddingBase(BaseModel):
    """Base embedding model."""
    chunk_id: UUID
    vector: List[float] = Field(..., description="Vector embedding (1536 dimensions)")
    model_name: str = "text-embedding-3-small"


class EmbeddingCreate(EmbeddingBase):
    """Schema for creating a new embedding."""
    pass


class EmbeddingInDB(EmbeddingBase):
    """Embedding as stored in database."""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Retrieval Models =============

class SearchFilters(BaseModel):
    """Filters for vector search."""
    doc_type: Optional[str] = None
    document_ids: Optional[List[UUID]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    metadata_filters: Optional[Dict[str, Any]] = None


class RetrievedChunk(BaseModel):
    """Chunk retrieved from vector search with similarity score."""
    chunk: ChunkInDB
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    document_title: Optional[str] = None
    document_type: Optional[str] = None


class RetrievalMetadata(BaseModel):
    """Metadata about the retrieval process for traceability."""
    chunks_retrieved: List[RetrievedChunk]
    query: str
    query_embedding_model: str
    retrieval_timestamp: datetime
    filters_applied: Optional[SearchFilters] = None
    total_chunks_available: Optional[int] = None


# ============= Analysis Models =============

class AnalysisRequest(BaseModel):
    """Request for document analysis."""
    document_ids: List[UUID]
    query: str
    filters: Optional[SearchFilters] = None
    top_k: int = Field(default=5, ge=1, le=20)


class AnalysisResponse(BaseModel):
    """Response from document analysis with traceability."""
    result: Dict[str, Any] = Field(..., description="Structured analysis output")
    retrieval_metadata: RetrievalMetadata
    processing_time_ms: float
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None


# Update forward references
DocumentWithChunks.model_rebuild()
ChunkWithEmbedding.model_rebuild()
