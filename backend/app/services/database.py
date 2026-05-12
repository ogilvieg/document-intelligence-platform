"""Database service for interacting with Supabase."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import json
import structlog
from supabase import create_client, Client

from app.config import settings
from app.models.database import (
    DocumentCreate, DocumentInDB,
    ChunkCreate, ChunkInDB,
    EmbeddingCreate, EmbeddingInDB,
    SearchFilters, RetrievedChunk
)

logger = structlog.get_logger()


class DatabaseService:
    """Service for database operations using Supabase."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        logger.info("database_service_initialized", url=settings.supabase_url)
    
    # ============= Document Operations =============
    
    async def create_document(self, document: DocumentCreate) -> DocumentInDB:
        """Create a new document."""
        try:
            data = document.model_dump(mode='json')
            response = self.client.table("documents").insert(data).execute()
            
            if not response.data:
                raise ValueError("Failed to create document")
            
            doc_data = response.data[0]
            logger.info("document_created", document_id=doc_data["id"])
            return DocumentInDB(**doc_data)
        
        except Exception as e:
            logger.error("document_creation_failed", error=str(e))
            raise
    
    async def get_document(self, document_id: UUID) -> Optional[DocumentInDB]:
        """Get a document by ID."""
        try:
            response = self.client.table("documents")\
                .select("*")\
                .eq("id", str(document_id))\
                .execute()
            
            if not response.data:
                return None
            
            return DocumentInDB(**response.data[0])
        
        except Exception as e:
            logger.error("document_fetch_failed", document_id=str(document_id), error=str(e))
            return None
    
    async def list_documents(
        self,
        doc_type: Optional[str] = None,
        limit: int = 100
    ) -> List[DocumentInDB]:
        """List documents with optional filtering."""
        try:
            query = self.client.table("documents").select("*")
            
            if doc_type:
                query = query.eq("doc_type", doc_type)
            
            response = query.order("created_at", desc=True).limit(limit).execute()
            
            return [DocumentInDB(**doc) for doc in response.data]
        
        except Exception as e:
            logger.error("document_list_failed", error=str(e))
            return []
    
    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document and its chunks (cascades to embeddings)."""
        try:
            response = self.client.table("documents")\
                .delete()\
                .eq("id", str(document_id))\
                .execute()
            
            logger.info("document_deleted", document_id=str(document_id))
            return True
        
        except Exception as e:
            logger.error("document_deletion_failed", document_id=str(document_id), error=str(e))
            return False
    
    # ============= Chunk Operations =============
    
    async def create_chunks(self, chunks: List[ChunkCreate]) -> List[ChunkInDB]:
        """Create multiple chunks (idempotent - skips existing)."""
        try:
            # Convert to dict for Supabase with UUIDs as strings
            chunks_data = [chunk.model_dump(mode='json') for chunk in chunks]
            
            # Upsert to make it idempotent (on conflict do nothing)
            response = self.client.table("chunks")\
                .upsert(chunks_data, on_conflict="document_id,chunk_index")\
                .execute()
            
            if not response.data:
                raise ValueError("Failed to create chunks")
            
            created_chunks = [ChunkInDB(**chunk) for chunk in response.data]
            logger.info("chunks_created", count=len(created_chunks))
            return created_chunks
        
        except Exception as e:
            logger.error("chunk_creation_failed", error=str(e))
            raise
    
    async def get_chunks_by_document(self, document_id: UUID) -> List[ChunkInDB]:
        """Get all chunks for a document."""
        try:
            response = self.client.table("chunks")\
                .select("*")\
                .eq("document_id", str(document_id))\
                .order("chunk_index")\
                .execute()
            
            return [ChunkInDB(**chunk) for chunk in response.data]
        
        except Exception as e:
            logger.error("chunk_fetch_failed", document_id=str(document_id), error=str(e))
            return []
    
    async def get_chunk(self, chunk_id: UUID) -> Optional[ChunkInDB]:
        """Get a single chunk by ID."""
        try:
            response = self.client.table("chunks")\
                .select("*")\
                .eq("id", str(chunk_id))\
                .execute()
            
            if not response.data:
                return None
            
            return ChunkInDB(**response.data[0])
        
        except Exception as e:
            logger.error("chunk_fetch_failed", chunk_id=str(chunk_id), error=str(e))
            return None
    
    # ============= Embedding Operations =============
    
    async def create_embedding(self, embedding: EmbeddingCreate) -> EmbeddingInDB:
        """Create an embedding (idempotent - updates if exists)."""
        try:
            data = embedding.model_dump(mode='json')
            # Convert vector list to string format for pgvector
            data["vector"] = str(data["vector"])
            
            # Upsert to make it idempotent
            response = self.client.table("embeddings")\
                .upsert(data, on_conflict="chunk_id,model_name")\
                .execute()
            
            if not response.data:
                raise ValueError("Failed to create embedding")
            
            emb_data = response.data[0]
            # Parse vector string back to list
            if isinstance(emb_data.get("vector"), str):
                emb_data["vector"] = json.loads(emb_data["vector"])
            logger.info("embedding_created", chunk_id=emb_data["chunk_id"])
            return EmbeddingInDB(**emb_data)
        
        except Exception as e:
            logger.error("embedding_creation_failed", error=str(e))
            raise
    
    async def get_embedding(
        self,
        chunk_id: UUID,
        model_name: str = "text-embedding-3-small"
    ) -> Optional[EmbeddingInDB]:
        """Get embedding for a chunk."""
        try:
            response = self.client.table("embeddings")\
                .select("*")\
                .eq("chunk_id", str(chunk_id))\
                .eq("model_name", model_name)\
                .execute()
            
            if not response.data:
                return None
            
            emb_data = response.data[0]
            # Parse vector string back to list
            if isinstance(emb_data.get("vector"), str):
                emb_data["vector"] = json.loads(emb_data["vector"])
            return EmbeddingInDB(**emb_data)
        
        except Exception as e:
            logger.error("embedding_fetch_failed", chunk_id=str(chunk_id), error=str(e))
            return None
    
    async def has_embedding(
        self,
        chunk_id: UUID,
        model_name: str = "text-embedding-3-small"
    ) -> bool:
        """Check if a chunk already has an embedding (for idempotency)."""
        embedding = await self.get_embedding(chunk_id, model_name)
        return embedding is not None
    
    # ============= Vector Search Operations =============
    
    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        filters: Optional[SearchFilters] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.5
    ) -> List[RetrievedChunk]:
        """
        Search for similar chunks using vector similarity.
        
        Uses pgvector's cosine similarity (<=> operator).
        Returns chunks with similarity scores and document metadata.
        """
        try:
            # Convert embedding to string format for pgvector
            query_vector_str = str(query_embedding)
            
            # Build RPC call for vector search with filters
            # This requires a PostgreSQL function (we'll create it)
            params = {
                "query_embedding": query_vector_str,
                "match_threshold": similarity_threshold,
                "match_count": top_k
            }
            
            # Add filters
            if filters:
                if filters.doc_type:
                    params["filter_doc_type"] = filters.doc_type
                if filters.document_ids:
                    params["filter_document_ids"] = [str(id) for id in filters.document_ids]
            
            # Call stored function for vector search
            response = self.client.rpc("match_chunks", params).execute()
            
            if not response.data:
                logger.info("no_chunks_found", top_k=top_k)
                return []
            
            # Parse results into RetrievedChunk objects
            retrieved_chunks = []
            for item in response.data:
                chunk = ChunkInDB(**item["chunk"])
                retrieved_chunks.append(RetrievedChunk(
                    chunk=chunk,
                    similarity_score=item["similarity"],
                    document_title=item.get("document_title"),
                    document_type=item.get("document_type")
                ))
            
            logger.info("chunks_retrieved", count=len(retrieved_chunks), top_k=top_k)
            return retrieved_chunks
        
        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            return []


# Global database service instance (lazy initialization)
_db_service = None


def get_db_service():
    """
    Return the appropriate database service based on available config.

    - DATABASE_URL set  →  PostgresDatabaseService (AWS RDS via asyncpg)
    - DATABASE_URL unset →  DatabaseService (Supabase — legacy, backwards-compatible)
    """
    global _db_service
    if _db_service is None:
        if settings.rds_database_url:
            from app.services.postgres_database import PostgresDatabaseService
            _db_service = PostgresDatabaseService(settings.rds_database_url)
            logger.info("db_backend_selected", backend="postgres_rds")
        else:
            _db_service = DatabaseService()
            logger.info("db_backend_selected", backend="supabase")
    return _db_service


# Backwards compatibility alias
db_service = property(lambda self: get_db_service())
