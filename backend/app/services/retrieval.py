"""Retrieval service for semantic search with full traceability."""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import structlog

from app.config import settings
from app.models.database import (
    SearchFilters,
    RetrievedChunk,
    RetrievalMetadata,
    ChunkInDB
)
from app.services.embedding_service import EmbeddingService
from app.services.database import get_db_service

logger = structlog.get_logger()


class RetrievalService:
    """
    Service for retrieving relevant chunks using semantic search.
    
    Key principle: Retrieval should be deterministic even if generation isn't.
    All retrieval operations are logged for full traceability.
    """
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        default_top_k: int = 5,
        similarity_threshold: float = 0.3  # Lowered from 0.5 for better recall
    ):
        """
        Initialize retrieval service.
        
        Args:
            embedding_service: Service for generating embeddings (creates new if None)
            default_top_k: Default number of chunks to retrieve
            similarity_threshold: Minimum similarity score (0-1) for results
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.default_top_k = default_top_k
        self.similarity_threshold = similarity_threshold
        
        logger.info(
            "retrieval_service_initialized",
            default_top_k=default_top_k,
            similarity_threshold=similarity_threshold,
            embedding_model=self.embedding_service.model_name
        )
    
    async def retrieve_chunks(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> RetrievalMetadata:
        """
        Retrieve relevant chunks for a query with full traceability.
        
        This is the main retrieval method - it:
        1. Embeds the query
        2. Searches for similar chunks
        3. Logs all retrieval details
        4. Returns chunks with metadata
        
        Args:
            query: Search query
            filters: Optional filters (doc_type, document_ids, etc.)
            top_k: Number of chunks to retrieve (defaults to default_top_k)
            similarity_threshold: Minimum similarity (defaults to instance threshold)
            
        Returns:
            RetrievalMetadata with chunks and full traceability info
        """
        top_k = top_k or self.default_top_k
        similarity_threshold = similarity_threshold or self.similarity_threshold
        retrieval_start = datetime.utcnow()
        
        logger.info(
            "retrieval_started",
            query=query,
            top_k=top_k,
            filters=filters.model_dump() if filters else None,
            similarity_threshold=similarity_threshold
        )
        
        # Step 1: Generate query embedding
        logger.debug("embedding_query", query_length=len(query))
        query_embedding = await self.embedding_service.generate_embedding(query)
        logger.debug("query_embedded", embedding_dimensions=len(query_embedding))
        
        # Step 2: Search for similar chunks
        db = get_db_service()
        retrieved_chunks = await db.search_similar_chunks(
            query_embedding=query_embedding,
            filters=filters,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        # Step 3: Log retrieval results
        chunk_ids = [str(rc.chunk.id) for rc in retrieved_chunks]
        scores = [rc.similarity_score for rc in retrieved_chunks]
        
        logger.info(
            "retrieval_completed",
            query=query,
            chunks_retrieved=len(retrieved_chunks),
            chunk_ids=chunk_ids,
            similarity_scores=scores,
            top_score=max(scores) if scores else 0,
            avg_score=sum(scores) / len(scores) if scores else 0
        )
        
        # Step 4: Build traceability metadata
        retrieval_metadata = RetrievalMetadata(
            chunks_retrieved=retrieved_chunks,
            query=query,
            query_embedding_model=self.embedding_service.model_name,
            retrieval_timestamp=retrieval_start,
            filters_applied=filters,
            total_chunks_available=None  # Could be added with a count query
        )
        
        # Log detailed traceability info
        for i, rc in enumerate(retrieved_chunks):
            logger.debug(
                "retrieved_chunk_detail",
                rank=i + 1,
                chunk_id=str(rc.chunk.id),
                document_id=str(rc.chunk.document_id),
                document_title=rc.document_title,
                document_type=rc.document_type,
                chunk_index=rc.chunk.chunk_index,
                similarity_score=rc.similarity_score,
                text_preview=rc.chunk.text[:100] + "..." if len(rc.chunk.text) > 100 else rc.chunk.text
            )
        
        return retrieval_metadata
    
    async def retrieve_for_document(
        self,
        query: str,
        document_id: UUID,
        top_k: Optional[int] = None
    ) -> RetrievalMetadata:
        """
        Retrieve relevant chunks from a specific document only.
        
        Convenience method that filters by document_id.
        
        Args:
            query: Search query
            document_id: Document to search within
            top_k: Number of chunks to retrieve
            
        Returns:
            RetrievalMetadata with chunks from specified document
        """
        filters = SearchFilters(document_ids=[document_id])
        
        logger.info(
            "retrieving_for_document",
            query=query,
            document_id=str(document_id),
            top_k=top_k
        )
        
        return await self.retrieve_chunks(
            query=query,
            filters=filters,
            top_k=top_k
        )
    
    async def retrieve_by_type(
        self,
        query: str,
        doc_type: str,
        top_k: Optional[int] = None
    ) -> RetrievalMetadata:
        """
        Retrieve relevant chunks from documents of a specific type.
        
        Useful for searching only in resumes, job descriptions, etc.
        
        Args:
            query: Search query
            doc_type: Document type to filter by (resume, jd, policy, etc.)
            top_k: Number of chunks to retrieve
            
        Returns:
            RetrievalMetadata with chunks from specified document type
        """
        filters = SearchFilters(doc_type=doc_type)
        
        logger.info(
            "retrieving_by_type",
            query=query,
            doc_type=doc_type,
            top_k=top_k
        )
        
        return await self.retrieve_chunks(
            query=query,
            filters=filters,
            top_k=top_k
        )
    
    async def retrieve_multi_document(
        self,
        query: str,
        document_ids: List[UUID],
        top_k: Optional[int] = None
    ) -> RetrievalMetadata:
        """
        Retrieve relevant chunks from multiple specific documents.
        
        Useful for comparing content across specific documents.
        
        Args:
            query: Search query
            document_ids: List of document IDs to search within
            top_k: Number of chunks to retrieve
            
        Returns:
            RetrievalMetadata with chunks from specified documents
        """
        filters = SearchFilters(document_ids=document_ids)
        
        logger.info(
            "retrieving_multi_document",
            query=query,
            document_count=len(document_ids),
            document_ids=[str(d) for d in document_ids],
            top_k=top_k
        )
        
        return await self.retrieve_chunks(
            query=query,
            filters=filters,
            top_k=top_k
        )
    
    async def get_chunk_context(
        self,
        chunk_id: UUID,
        context_size: int = 2
    ) -> List[ChunkInDB]:
        """
        Get surrounding chunks for context.
        
        Retrieves N chunks before and after the specified chunk
        to provide additional context.
        
        Args:
            chunk_id: ID of the chunk to get context for
            context_size: Number of chunks before/after to retrieve
            
        Returns:
            List of chunks including the target and surrounding chunks
        """
        db = get_db_service()
        
        # Get the target chunk
        target_chunk = await db.get_chunk(chunk_id)
        if not target_chunk:
            logger.warning("chunk_not_found", chunk_id=str(chunk_id))
            return []
        
        # Get all chunks from the same document
        all_chunks = await db.get_chunks_by_document(target_chunk.document_id)
        
        # Find the target chunk's position
        target_index = next(
            (i for i, c in enumerate(all_chunks) if c.id == chunk_id),
            None
        )
        
        if target_index is None:
            return [target_chunk]
        
        # Get surrounding chunks
        start_index = max(0, target_index - context_size)
        end_index = min(len(all_chunks), target_index + context_size + 1)
        
        context_chunks = all_chunks[start_index:end_index]
        
        logger.info(
            "chunk_context_retrieved",
            chunk_id=str(chunk_id),
            target_index=target_index,
            context_chunks=len(context_chunks),
            range=f"{start_index}-{end_index}"
        )
        
        return context_chunks
    
    async def explain_retrieval(
        self,
        query: str,
        retrieval_metadata: RetrievalMetadata
    ) -> Dict[str, Any]:
        """
        Generate an explanation of why chunks were retrieved.
        
        Provides insights into the retrieval process for debugging
        and transparency.
        
        Args:
            query: The original query
            retrieval_metadata: Results from retrieve_chunks()
            
        Returns:
            Dictionary with retrieval explanation
        """
        chunks = retrieval_metadata.chunks_retrieved
        
        if not chunks:
            return {
                "query": query,
                "result": "No chunks found",
                "reason": "No chunks met the similarity threshold",
                "suggestion": "Try lowering the similarity threshold or checking if documents are embedded"
            }
        
        # Analyze score distribution
        scores = [c.similarity_score for c in chunks]
        score_analysis = {
            "highest": max(scores),
            "lowest": min(scores),
            "average": sum(scores) / len(scores),
            "range": max(scores) - min(scores)
        }
        
        # Group by document
        docs_represented = {}
        for chunk in chunks:
            doc_type = chunk.document_type or "unknown"
            if doc_type not in docs_represented:
                docs_represented[doc_type] = 0
            docs_represented[doc_type] += 1
        
        explanation = {
            "query": query,
            "chunks_retrieved": len(chunks),
            "score_analysis": score_analysis,
            "documents_represented": docs_represented,
            "embedding_model": retrieval_metadata.query_embedding_model,
            "filters_applied": retrieval_metadata.filters_applied.model_dump() if retrieval_metadata.filters_applied else None,
            "top_chunks": [
                {
                    "rank": i + 1,
                    "score": c.similarity_score,
                    "document_type": c.document_type,
                    "chunk_index": c.chunk.chunk_index,
                    "text_preview": c.chunk.text[:150] + "..."
                }
                for i, c in enumerate(chunks[:3])  # Top 3
            ]
        }
        
        logger.info("retrieval_explained", **explanation)
        
        return explanation
