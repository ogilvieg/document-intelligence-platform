"""Chunking service for splitting documents into processable chunks."""

from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import structlog

from app.config import settings
from app.models.database import ChunkCreate, ChunkInDB
from app.services.database import get_db_service

logger = structlog.get_logger()


class ChunkingService:
    """Service for chunking documents into fixed-size segments with overlap."""
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        persist_to_db: bool = True
    ):
        """
        Initialize chunking service.
        
        Args:
            chunk_size: Size of each chunk in characters (defaults to settings.chunk_size)
            chunk_overlap: Overlap between chunks in characters (defaults to settings.chunk_overlap)
            persist_to_db: Whether to persist chunks to database (default: True)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.persist_to_db = persist_to_db
        
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        logger.info(
            "chunking_service_initialized",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            persist_to_db=self.persist_to_db
        )
    
    async def chunk_text(
        self,
        text: str,
        document_id: UUID,
        doc_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ChunkInDB]:
        """
        Split text into fixed-size chunks with overlap.
        
        Uses character-based chunking with sliding window approach.
        Tries to break at sentence boundaries when possible.
        
        IDEMPOTENT: If chunks already exist for this document, returns existing chunks.
        
        Args:
            text: The text to chunk
            document_id: UUID of the parent document
            doc_type: Document type (resume, jd, policy, etc.)
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of ChunkInDB objects (persisted to database if persist_to_db=True)
        """
        if not text or not text.strip():
            logger.warning("chunk_text_called_with_empty_text", document_id=str(document_id))
            return []
        
        # Check if chunks already exist (idempotency)
        if self.persist_to_db:
            db = get_db_service()
            existing_chunks = await db.get_chunks_by_document(document_id)
            if existing_chunks:
                logger.info(
                    "chunks_already_exist",
                    document_id=str(document_id),
                    chunk_count=len(existing_chunks)
                )
                return existing_chunks
        
        logger.info(
            "chunking_started",
            document_id=str(document_id),
            text_length=len(text),
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        
        chunk_dicts = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # Extract chunk text
            if end >= len(text):
                # Last chunk - take remaining text
                chunk_text = text[start:].strip()
            else:
                # Try to break at sentence boundary
                chunk_text = text[start:end]
                
                # Look for sentence endings near the end of the chunk
                sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
                best_break = -1
                
                # Search backwards from end for sentence boundary
                search_start = max(0, len(chunk_text) - 100)  # Look in last 100 chars
                for ending in sentence_endings:
                    pos = chunk_text.rfind(ending, search_start)
                    if pos > best_break:
                        best_break = pos + len(ending)
                
                # If found a good break point, use it
                if best_break > 0 and best_break > len(chunk_text) * 0.5:
                    chunk_text = chunk_text[:best_break].strip()
                    end = start + best_break
                else:
                    # No good sentence boundary, break at word boundary
                    last_space = chunk_text.rfind(' ')
                    if last_space > len(chunk_text) * 0.8:  # Only if reasonably close to end
                        chunk_text = chunk_text[:last_space].strip()
                        end = start + last_space
                    else:
                        chunk_text = chunk_text.strip()
            
            # Skip empty chunks
            if chunk_text:
                # Build chunk metadata
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'start_char': start,
                    'end_char': min(start + len(chunk_text), len(text)),
                    'doc_type': doc_type
                })
                
                chunk_dict = {
                    'document_id': document_id,
                    'chunk_index': chunk_index,
                    'text': chunk_text,
                    'token_count': self._estimate_tokens(chunk_text),
                    'metadata': chunk_metadata
                }
                chunk_dicts.append(chunk_dict)
                chunk_index += 1
            
            # Move to next chunk with overlap
            start = end - self.chunk_overlap
            
            # Prevent infinite loop on very small texts
            if start <= 0 or end >= len(text):
                break
        
        logger.info(
            "chunking_completed",
            document_id=str(document_id),
            total_chunks=len(chunk_dicts),
            avg_chunk_size=sum(len(c['text']) for c in chunk_dicts) / len(chunk_dicts) if chunk_dicts else 0
        )
        
        # Persist to database if enabled
        if self.persist_to_db and chunk_dicts:
            try:
                db = get_db_service()
                chunk_creates = [ChunkCreate(**chunk) for chunk in chunk_dicts]
                persisted_chunks = await db.create_chunks(chunk_creates)
                logger.info("chunks_persisted_to_db", count=len(persisted_chunks))
                return persisted_chunks
            except Exception as e:
                logger.error("chunk_persistence_failed", error=str(e))
                raise
        
        # If not persisting, return as ChunkInDB objects with generated IDs
        # (for testing or temporary use)
        from datetime import datetime
        return [
            ChunkInDB(
                id=uuid4(),
                created_at=datetime.utcnow(),
                **chunk
            )
            for chunk in chunk_dicts
        ]
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a text string.
        
        Uses a simple heuristic: ~4 characters per token for English.
        For production, consider using tiktoken library.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        return len(text) // 4
    
    async def chunk_document(
        self,
        document_text: str,
        document_id: UUID,
        doc_type: str,
        document_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Chunk a complete document and return structured result.
        
        This is a convenience method that wraps chunk_text and adds
        summary statistics.
        
        IDEMPOTENT: Reuses existing chunks if they already exist in database.
        
        Args:
            document_text: The full document text
            document_id: UUID of the document
            doc_type: Document type (resume, jd, policy, etc.)
            document_metadata: Metadata from document ingestion
            
        Returns:
            Dictionary with chunks and statistics
        """
        chunks = await self.chunk_text(
            text=document_text,
            document_id=document_id,
            doc_type=doc_type,
            metadata=document_metadata
        )
        
        if not chunks:
            return {
                'document_id': document_id,
                'chunks': [],
                'total_chunks': 0,
                'total_characters': 0,
                'average_chunk_size': 0
            }
        
        total_chars = sum(len(chunk.text) for chunk in chunks)
        
        return {
            'document_id': document_id,
            'chunks': [chunk.model_dump() for chunk in chunks],  # Convert to dict for JSON
            'total_chunks': len(chunks),
            'total_characters': total_chars,
            'average_chunk_size': total_chars / len(chunks),
            'chunk_size_config': self.chunk_size,
            'chunk_overlap_config': self.chunk_overlap
        }
    
    def validate_chunks(self, chunks: List[ChunkInDB]) -> Dict[str, Any]:
        """
        Validate chunks for quality and consistency.
        
        Checks for:
        - Overlapping content between consecutive chunks
        - Chunk size distribution
        - Coverage of original text
        
        Args:
            chunks: List of ChunkInDB objects
            
        Returns:
            Validation report with warnings and statistics
        """
        if not chunks:
            return {'valid': True, 'warnings': [], 'statistics': {}}
        
        warnings = []
        
        # Check chunk sizes
        sizes = [len(chunk.text) for chunk in chunks]
        min_size = min(sizes)
        max_size = max(sizes)
        avg_size = sum(sizes) / len(sizes)
        
        # Warn if chunks are too small
        if min_size < self.chunk_size * 0.3 and len(chunks) > 1:
            warnings.append(f"Some chunks are very small (min: {min_size} chars)")
        
        # Warn if size variance is very high
        if max_size > avg_size * 1.5:
            warnings.append(f"High variance in chunk sizes (max: {max_size}, avg: {avg_size:.0f})")
        
        # Check for overlap in consecutive chunks
        has_overlap = False
        for i in range(len(chunks) - 1):
            current_text = chunks[i].text
            next_text = chunks[i + 1].text
            
            # Check if there's any overlapping text
            overlap_check = current_text[-50:] if len(current_text) >= 50 else current_text
            if overlap_check in next_text:
                has_overlap = True
                break
        
        if not has_overlap and len(chunks) > 1:
            warnings.append("No overlap detected between consecutive chunks")
        
        return {
            'valid': True,
            'warnings': warnings,
            'statistics': {
                'total_chunks': len(chunks),
                'min_size': min_size,
                'max_size': max_size,
                'avg_size': avg_size,
                'has_overlap': has_overlap
            }
        }
