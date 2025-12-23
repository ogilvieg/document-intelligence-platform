"""Database models for PostgreSQL."""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4


class Document:
    """Document model."""
    def __init__(
        self,
        id: Optional[UUID] = None,
        title: str = "",
        type: str = "",
        source: Optional[str] = None,
        version: str = "1.0",
        created_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = id or uuid4()
        self.title = title
        self.type = type
        self.source = source
        self.version = version
        self.created_at = created_at or datetime.utcnow()
        self.metadata = metadata or {}


class Chunk:
    """Document chunk model."""
    def __init__(
        self,
        id: Optional[UUID] = None,
        document_id: Optional[UUID] = None,
        chunk_index: int = 0,
        text: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[list] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id or uuid4()
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.text = text
        self.metadata = metadata or {}
        self.embedding = embedding
        self.created_at = created_at or datetime.utcnow()


class AnalysisRun:
    """Analysis run model."""
    def __init__(
        self,
        id: Optional[UUID] = None,
        inputs: Optional[Dict[str, Any]] = None,
        output_json: Optional[Dict[str, Any]] = None,
        citations: Optional[list] = None,
        latency_ms: int = 0,
        cost: Optional[float] = None,
        created_at: Optional[datetime] = None,
        status: str = "pending"
    ):
        self.id = id or uuid4()
        self.inputs = inputs or {}
        self.output_json = output_json or {}
        self.citations = citations or []
        self.latency_ms = latency_ms
        self.cost = cost
        self.created_at = created_at or datetime.utcnow()
        self.status = status
