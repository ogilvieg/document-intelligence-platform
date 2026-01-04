"""Embedding service for generating and managing vector embeddings."""

from typing import List, Optional, Dict, Any
from uuid import UUID
import structlog
from openai import AsyncOpenAI

from app.config import settings
from app.models.database import ChunkInDB, EmbeddingCreate, EmbeddingInDB
from app.services.database import get_db_service

logger = structlog.get_logger()


class EmbeddingService:
    """Service for generating and storing vector embeddings using OpenAI."""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        batch_size: int = 100
    ):
        """
        Initialize embedding service.
        
        Args:
            model_name: OpenAI embedding model (defaults to settings.openai_embedding_model)
            batch_size: Number of texts to embed in one API call
        """
        self.model_name = model_name or settings.openai_embedding_model
        self.batch_size = batch_size
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        # Model dimensions (for validation)
        self.model_dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        
        self.expected_dimensions = self.model_dimensions.get(self.model_name, 1536)
        
        logger.info(
            "embedding_service_initialized",
            model=self.model_name,
            dimensions=self.expected_dimensions,
            batch_size=self.batch_size
        )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            Exception: If OpenAI API call fails
        """
        try:
            logger.debug("generating_embedding", text_length=len(text))
            
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # Validate dimensions
            if len(embedding) != self.expected_dimensions:
                logger.warning(
                    "unexpected_embedding_dimensions",
                    expected=self.expected_dimensions,
                    actual=len(embedding)
                )
            
            logger.debug(
                "embedding_generated",
                dimensions=len(embedding),
                tokens_used=response.usage.total_tokens
            )
            
            return embedding
        
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e), text_length=len(text))
            raise
    
    async def generate_embeddings_batch(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in one API call.
        
        More efficient than calling generate_embedding multiple times.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (same order as input texts)
            
        Raises:
            Exception: If OpenAI API call fails
        """
        if not texts:
            return []
        
        try:
            logger.info("generating_embeddings_batch", count=len(texts))
            
            response = await self.client.embeddings.create(
                model=self.model_name,
                input=texts
            )
            
            # Extract embeddings in order
            embeddings = [item.embedding for item in response.data]
            
            logger.info(
                "embeddings_batch_generated",
                count=len(embeddings),
                tokens_used=response.usage.total_tokens,
                avg_tokens_per_text=response.usage.total_tokens / len(texts)
            )
            
            return embeddings
        
        except Exception as e:
            logger.error("batch_embedding_failed", error=str(e), texts_count=len(texts))
            raise
    
    async def embed_chunk(
        self,
        chunk: ChunkInDB,
        force_regenerate: bool = False
    ) -> EmbeddingInDB:
        """
        Generate and store embedding for a single chunk.
        
        IDEMPOTENT: Checks if embedding exists before generating.
        
        Args:
            chunk: Chunk to embed
            force_regenerate: If True, regenerate even if embedding exists
            
        Returns:
            EmbeddingInDB object (existing or newly created)
        """
        db = get_db_service()
        
        # Check if embedding already exists (idempotency)
        if not force_regenerate:
            existing = await db.get_embedding(chunk.id, self.model_name)
            if existing:
                logger.info(
                    "embedding_already_exists",
                    chunk_id=str(chunk.id),
                    model=self.model_name
                )
                return existing
        
        # Generate new embedding
        logger.info("embedding_chunk", chunk_id=str(chunk.id))
        
        vector = await self.generate_embedding(chunk.text)
        
        # Store in database
        embedding_create = EmbeddingCreate(
            chunk_id=chunk.id,
            vector=vector,
            model_name=self.model_name
        )
        
        embedding = await db.create_embedding(embedding_create)
        
        logger.info(
            "chunk_embedded",
            chunk_id=str(chunk.id),
            embedding_id=str(embedding.id),
            vector_dimensions=len(vector)
        )
        
        return embedding
    
    async def embed_chunks(
        self,
        chunks: List[ChunkInDB],
        force_regenerate: bool = False,
        skip_existing: bool = True
    ) -> List[EmbeddingInDB]:
        """
        Generate and store embeddings for multiple chunks.
        
        Uses batch API calls for efficiency.
        IDEMPOTENT: By default, skips chunks that already have embeddings.
        
        Args:
            chunks: List of chunks to embed
            force_regenerate: If True, regenerate all embeddings
            skip_existing: If True, skip chunks with existing embeddings
            
        Returns:
            List of EmbeddingInDB objects
        """
        if not chunks:
            return []
        
        db = get_db_service()
        embeddings = []
        chunks_to_embed = []
        
        logger.info("embedding_chunks_batch", total_chunks=len(chunks))
        
        # Filter out chunks that already have embeddings
        if skip_existing and not force_regenerate:
            for chunk in chunks:
                existing = await db.get_embedding(chunk.id, self.model_name)
                if existing:
                    embeddings.append(existing)
                    logger.debug("skipping_existing_embedding", chunk_id=str(chunk.id))
                else:
                    chunks_to_embed.append(chunk)
        else:
            chunks_to_embed = chunks
        
        if not chunks_to_embed:
            logger.info("all_chunks_already_embedded", count=len(chunks))
            return embeddings
        
        logger.info("chunks_to_embed", count=len(chunks_to_embed))
        
        # Process in batches
        for i in range(0, len(chunks_to_embed), self.batch_size):
            batch = chunks_to_embed[i:i + self.batch_size]
            batch_texts = [chunk.text for chunk in batch]
            
            logger.info(
                "processing_batch",
                batch_num=i // self.batch_size + 1,
                batch_size=len(batch)
            )
            
            # Generate embeddings for batch
            vectors = await self.generate_embeddings_batch(batch_texts)
            
            # Store embeddings in database
            for chunk, vector in zip(batch, vectors):
                embedding_create = EmbeddingCreate(
                    chunk_id=chunk.id,
                    vector=vector,
                    model_name=self.model_name
                )
                
                embedding = await db.create_embedding(embedding_create)
                embeddings.append(embedding)
        
        logger.info(
            "chunks_embedded_complete",
            total_embeddings=len(embeddings),
            newly_created=len(chunks_to_embed),
            skipped=len(chunks) - len(chunks_to_embed)
        )
        
        return embeddings
    
    async def embed_document_chunks(
        self,
        document_id: UUID,
        force_regenerate: bool = False
    ) -> List[EmbeddingInDB]:
        """
        Generate embeddings for all chunks of a document.
        
        Convenience method that fetches chunks and embeds them.
        
        Args:
            document_id: ID of document whose chunks to embed
            force_regenerate: If True, regenerate existing embeddings
            
        Returns:
            List of EmbeddingInDB objects
        """
        db = get_db_service()
        
        logger.info("embedding_document_chunks", document_id=str(document_id))
        
        # Fetch all chunks for document
        chunks = await db.get_chunks_by_document(document_id)
        
        if not chunks:
            logger.warning("no_chunks_found_for_document", document_id=str(document_id))
            return []
        
        logger.info("found_chunks_for_document", document_id=str(document_id), count=len(chunks))
        
        # Embed all chunks
        embeddings = await self.embed_chunks(chunks, force_regenerate=force_regenerate)
        
        return embeddings
    
    async def get_embedding_stats(self, document_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get statistics about embeddings.
        
        Args:
            document_id: Optional document ID to filter stats
            
        Returns:
            Dictionary with embedding statistics
        """
        db = get_db_service()
        
        if document_id:
            chunks = await db.get_chunks_by_document(document_id)
            total_chunks = len(chunks)
            
            # Count how many have embeddings
            embedded_count = 0
            for chunk in chunks:
                if await db.has_embedding(chunk.id, self.model_name):
                    embedded_count += 1
            
            return {
                "document_id": str(document_id),
                "total_chunks": total_chunks,
                "embedded_chunks": embedded_count,
                "pending_chunks": total_chunks - embedded_count,
                "completion_rate": embedded_count / total_chunks if total_chunks > 0 else 0,
                "model": self.model_name
            }
        else:
            # Global stats would require more complex queries
            # For now, just return model info
            return {
                "model": self.model_name,
                "dimensions": self.expected_dimensions,
                "batch_size": self.batch_size
            }
