"""Models package initialization."""

from .schemas import (
    DocumentType,
    DocumentUploadRequest,
    DocumentResponse,
    AnalysisRequest,
    AnalysisOutput,
    Citation,
    AnalysisResponse,
    HealthResponse
)
from .database import (
    DocumentCreate,
    DocumentInDB,
    DocumentWithChunks,
    ChunkCreate,
    ChunkInDB,
    ChunkWithEmbedding,
    EmbeddingCreate,
    EmbeddingInDB,
    SearchFilters,
    RetrievedChunk,
    RetrievalMetadata,
    AnalysisRequest as DBAnalysisRequest,
    AnalysisResponse as DBAnalysisResponse
)

__all__ = [
    "DocumentType",
    "DocumentUploadRequest",
    "DocumentResponse",
    "AnalysisRequest",
    "AnalysisOutput",
    "Citation",
    "AnalysisResponse",
    "HealthResponse",
    # Database models
    "DocumentCreate",
    "DocumentInDB",
    "DocumentWithChunks",
    "ChunkCreate",
    "ChunkInDB",
    "ChunkWithEmbedding",
    "EmbeddingCreate",
    "EmbeddingInDB",
    "SearchFilters",
    "RetrievedChunk",
    "RetrievalMetadata",
    "DBAnalysisRequest",
    "DBAnalysisResponse"
]
