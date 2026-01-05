"""API routes."""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form, Depends
from typing import List, Optional
from datetime import datetime
from uuid import uuid4, UUID
import structlog

from app.models import (
    DocumentUploadRequest,
    DocumentResponse,
    AnalysisRequest,
    AnalysisResponse,
    Citation,
    DocumentType
)
from app.models.database import (
    SearchFilters,
    RetrievalMetadata,
    RetrievedChunk
)
from app.services import LLMService, DocumentIngestionService, ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.retrieval import RetrievalService
from app.middleware.auth import verify_api_key

logger = structlog.get_logger()
router = APIRouter()

# Initialize services
llm_service = LLMService()
document_ingestion_service = DocumentIngestionService()
chunking_service = ChunkingService()
embedding_service = EmbeddingService()
retrieval_service = RetrievalService(embedding_service=embedding_service)


@router.post("/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(verify_api_key)])
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    source: Optional[str] = Form(None)
):
    """
    Upload a document for processing.
    
    Supports: PDF, Markdown, HTML
    
    The document will be:
    1. Validated for size and type
    2. Parsed to extract text content
    3. Stored with metadata
    
    Args:
        file: The document file to upload
        title: Optional title (defaults to filename)
        source: Optional source information
        
    Returns:
        DocumentResponse with document ID and metadata
    """
    logger.info("document_upload_requested", filename=file.filename, content_type=file.content_type)
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Ingest document
        result = document_ingestion_service.ingest_document(
            file_content=file_content,
            filename=file.filename or "untitled",
            content_type=file.content_type or "application/octet-stream"
        )
        
        # Determine document type from content type
        content_type_map = {
            'application/pdf': DocumentType.PDF,
            'text/markdown': DocumentType.MARKDOWN,
            'text/html': DocumentType.HTML,
            'text/plain': DocumentType.MARKDOWN
        }
        doc_type = content_type_map.get(file.content_type, DocumentType.MARKDOWN)
        
        # Generate document ID
        document_id = uuid4()
        
        # Chunk the document
        chunking_result = await chunking_service.chunk_document(
            document_text=result['text'],
            document_id=document_id,
            doc_type=doc_type.value,  # Convert enum to string
            document_metadata=result.get('metadata', {})
        )
        
        # TODO Week 1: Store document and chunks in Supabase database
        # For now, we're just parsing and chunking, returning metadata
        
        # Prepare response
        response = DocumentResponse(
            id=document_id,
            title=title or file.filename or "untitled",
            type=doc_type,
            source=source,
            version="1.0",
            created_at=datetime.utcnow(),
            metadata={
                'original_filename': file.filename,
                'text_length': len(result['text']),
                'page_count': result.get('page_count'),
                'parser': result['metadata'].get('parser'),
                'content_type': file.content_type,
                'chunks': {
                    'total_chunks': chunking_result['total_chunks'],
                    'average_chunk_size': chunking_result['average_chunk_size'],
                    'chunk_size_config': chunking_result['chunk_size_config'],
                    'chunk_overlap_config': chunking_result['chunk_overlap_config']
                }
            }
        )
        
        logger.info(
            "document_upload_completed",
            document_id=str(document_id),
            filename=file.filename,
            text_length=len(result['text']),
            page_count=result.get('page_count'),
            total_chunks=chunking_result['total_chunks']
        )
        
        return response
        
    except ValueError as e:
        logger.error("document_upload_validation_failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "document_upload_failed",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.post("/analyze", response_model=AnalysisResponse, dependencies=[Depends(verify_api_key)])
async def analyze_documents(request: AnalysisRequest):
    """
    Run analysis on uploaded documents.
    
    Week 1 MVP: Simple LLM analysis without document retrieval.
    Accepts document context directly for testing.
    
    Week 2+: Will integrate document retrieval and chunking.
    """
    logger.info("analysis_requested", document_ids=request.document_ids, options=request.options)
    
    try:
        # Week 1 MVP: Use sample context for testing
        # In production, this would retrieve actual documents by ID
        sample_context = """
        Sample Document Analysis Context:
        
        This is a test document for the Document Intelligence Platform.
        The system is designed to analyze multiple documents, perform 
        retrieval + reasoning, and return structured, traceable outputs 
        with evaluation and operational guardrails.
        
        Key features include:
        - Document ingestion (PDF, Markdown, HTML)
        - Vector embeddings and search
        - Schema-validated outputs
        - Cost and latency tracking
        """
        
        # If options include 'context', use that instead
        if request.options and 'context' in request.options:
            sample_context = request.options['context']
        
        # Call LLM service
        analysis_output, metadata = llm_service.analyze_with_llm(
            context=sample_context,
            options=request.options
        )
        
        # Calculate cost
        cost = llm_service.estimate_cost(
            metadata['prompt_tokens'],
            metadata['completion_tokens']
        )
        
        # Create response with placeholder citations
        # Week 2+: Real citations from retrieved chunks
        citations = [
            Citation(
                chunk_id=uuid4(),
                document_id=request.document_ids[0] if request.document_ids else uuid4(),
                document_title="Sample Document",
                chunk_text=sample_context[:200] + "...",
                relevance_score=0.95
            )
        ]
        
        response = AnalysisResponse(
            id=uuid4(),
            output=analysis_output,
            citations=citations,
            latency_ms=metadata['latency_ms'],
            cost=cost,
            created_at=datetime.utcnow()
        )
        
        logger.info(
            "analysis_completed",
            analysis_id=str(response.id),
            latency_ms=response.latency_ms,
            cost=cost,
            confidence=analysis_output.confidence
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "analysis_failed",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents():
    """List all uploaded documents."""
    logger.info("documents_list_requested")
    
    # TODO: Implement document listing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document listing not yet implemented"
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """Get a specific document by ID."""
    logger.info("document_get_requested", document_id=document_id)
    
    # TODO: Implement document retrieval
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document retrieval not yet implemented"
    )


# ============= Week 2: RAG Endpoints =============

@router.post("/documents/{document_id}/generate-embeddings", dependencies=[Depends(verify_api_key)])
async def generate_embeddings(document_id: UUID):
    """
    Generate embeddings for all chunks of a document.
    
    This endpoint:
    1. Retrieves all chunks for the document
    2. Generates embeddings for each chunk (idempotent)
    3. Stores embeddings in the database
    4. Returns metadata about the embedding process
    
    Args:
        document_id: UUID of the document
        
    Returns:
        Metadata about embedding generation (count, model, etc.)
    """
    logger.info("embedding_generation_requested", document_id=str(document_id))
    
    try:
        # Generate embeddings for all document chunks
        embeddings = await embedding_service.embed_document_chunks(document_id)
        
        # Calculate statistics
        total_embeddings = len(embeddings)
        # All embeddings returned are either new or existing, we can't differentiate easily
        # So we'll just report the total
        newly_generated = 0  # Would need to track this in the service
        
        response = {
            "document_id": str(document_id),
            "total_embeddings": total_embeddings,
            "newly_generated": newly_generated,
            "skipped_existing": total_embeddings - newly_generated,
            "model": embedding_service.model_name,
            "embedding_dimensions": 1536,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "embedding_generation_completed",
            document_id=str(document_id),
            total_embeddings=total_embeddings,
            newly_generated=newly_generated
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "embedding_generation_failed",
            document_id=str(document_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embeddings: {str(e)}"
        )


@router.post("/search/chunks", dependencies=[Depends(verify_api_key)])
async def search_chunks(
    query: str,
    filters: Optional[SearchFilters] = None,
    top_k: int = 5,
    similarity_threshold: float = 0.5
):
    """
    Search for relevant chunks using semantic search.
    
    This endpoint:
    1. Embeds the query
    2. Performs vector similarity search
    3. Returns chunks with similarity scores and metadata
    
    Args:
        query: Search query
        filters: Optional filters (doc_type, document_ids, etc.)
        top_k: Number of chunks to return (default: 5)
        similarity_threshold: Minimum similarity score (default: 0.5)
        
    Returns:
        RetrievalMetadata with retrieved chunks and traceability info
    """
    logger.info(
        "chunk_search_requested",
        query=query,
        top_k=top_k,
        filters=filters.model_dump() if filters else None
    )
    
    try:
        # Perform retrieval
        retrieval_metadata = await retrieval_service.retrieve_chunks(
            query=query,
            filters=filters,
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )
        
        # Convert to dict for JSON response
        response = {
            "query": retrieval_metadata.query,
            "chunks_retrieved": len(retrieval_metadata.chunks_retrieved),
            "retrieval_timestamp": retrieval_metadata.retrieval_timestamp.isoformat(),
            "query_embedding_model": retrieval_metadata.query_embedding_model,
            "filters_applied": retrieval_metadata.filters_applied.model_dump() if retrieval_metadata.filters_applied else None,
            "chunks": [
                {
                    "chunk_id": str(rc.chunk.id),
                    "document_id": str(rc.chunk.document_id),
                    "document_title": rc.document_title,
                    "document_type": rc.document_type,
                    "chunk_index": rc.chunk.chunk_index,
                    "text": rc.chunk.text,
                    "similarity_score": rc.similarity_score,
                    "metadata": rc.chunk.metadata
                }
                for rc in retrieval_metadata.chunks_retrieved
            ]
        }
        
        logger.info(
            "chunk_search_completed",
            query=query,
            chunks_retrieved=len(retrieval_metadata.chunks_retrieved)
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "chunk_search_failed",
            query=query,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chunk search failed: {str(e)}"
        )


from pydantic import BaseModel as PydanticBaseModel, Field as PydanticField

class RAGAnalysisRequest(PydanticBaseModel):
    """Request model for RAG analysis."""
    query: str
    document_ids: Optional[List[UUID]] = None
    doc_type: Optional[str] = None
    top_k: int = 5
    similarity_threshold: float = 0.5
    temperature: float = 0.7


@router.post("/analyze-rag", dependencies=[Depends(verify_api_key)])
async def analyze_with_rag(request: RAGAnalysisRequest):
    """
    Analyze documents using RAG (Retrieval-Augmented Generation).
    
    This is the MAIN RAG endpoint that:
    1. Retrieves relevant chunks using semantic search
    2. Analyzes using LLM with retrieved chunks as context
    3. Returns structured output with citations
    4. Includes full traceability metadata
    
    Args:
        request: RAGAnalysisRequest with query, filters, and parameters
        
    Returns:
        Complete analysis with output, citations, and traceability metadata
    """
    logger.info(
        "rag_analysis_requested",
        query=request.query,
        document_ids=[str(d) for d in request.document_ids] if request.document_ids else None,
        doc_type=request.doc_type,
        top_k=request.top_k
    )
    
    try:
        # Step 1: Build filters
        filters = None
        if request.document_ids or request.doc_type:
            filters = SearchFilters(
                document_ids=request.document_ids,
                doc_type=request.doc_type
            )
        
        # Step 2: Retrieve relevant chunks
        retrieval_metadata = await retrieval_service.retrieve_chunks(
            query=request.query,
            filters=filters,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        if not retrieval_metadata.chunks_retrieved:
            logger.warning("no_chunks_retrieved", query=request.query)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No relevant chunks found. Try lowering similarity_threshold or check if documents are embedded."
            )
        
        # Step 3: Analyze with LLM using retrieved chunks
        analysis_output, citations, llm_metadata = llm_service.analyze_with_chunks(
            query=request.query,
            chunks=retrieval_metadata.chunks_retrieved,
            temperature=request.temperature
        )
        
        # Step 4: Calculate cost
        cost = llm_service.estimate_cost(
            llm_metadata['prompt_tokens'],
            llm_metadata['completion_tokens']
        )
        
        # Step 5: Build comprehensive response
        response = {
            "analysis_id": str(uuid4()),
            "query": request.query,
            "output": {
                "overall_fit": analysis_output.overall_fit,
                "strengths": analysis_output.strengths,
                "gaps": analysis_output.gaps,
                "risk_factors": analysis_output.risk_factors,
                "confidence": analysis_output.confidence,
                "recommended_focus": analysis_output.recommended_focus
            },
            "citations": [
                {
                    "chunk_id": str(c.chunk_id),
                    "document_id": str(c.document_id),
                    "document_title": c.document_title,
                    "chunk_text": c.chunk_text,
                    "relevance_score": c.relevance_score
                }
                for c in citations
            ],
            "retrieved_chunks": [
                {
                    "chunk_id": str(retrieved_chunk.chunk.id),
                    "document_id": str(retrieved_chunk.chunk.document_id),
                    "document_title": retrieved_chunk.document_title or "Unknown",
                    "doc_type": retrieved_chunk.document_type or "unknown",
                    "chunk_index": retrieved_chunk.chunk.chunk_index,
                    "text": retrieved_chunk.chunk.text,
                    "similarity_score": retrieved_chunk.similarity_score,
                    "metadata": retrieved_chunk.chunk.metadata
                }
                for retrieved_chunk in retrieval_metadata.chunks_retrieved
            ],
            "retrieval_metadata": {
                "chunks_retrieved": len(retrieval_metadata.chunks_retrieved),
                "query_embedding_model": retrieval_metadata.query_embedding_model,
                "retrieval_timestamp": retrieval_metadata.retrieval_timestamp.isoformat(),
                "filters_applied": retrieval_metadata.filters_applied.model_dump() if retrieval_metadata.filters_applied else None
            },
            "llm_metadata": {
                "model": llm_metadata['model'],
                "temperature": request.temperature,
                "latency_ms": llm_metadata['latency_ms'],
                "prompt_tokens": llm_metadata['prompt_tokens'],
                "completion_tokens": llm_metadata['completion_tokens'],
                "total_tokens": llm_metadata['total_tokens'],
                "cost_usd": cost
            },
            "cost": cost,
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info(
            "rag_analysis_completed",
            analysis_id=response["analysis_id"],
            chunks_used=len(citations),
            confidence=analysis_output.confidence,
            latency_ms=llm_metadata['latency_ms'],
            cost_usd=cost
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "rag_analysis_failed",
            query=request.query,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG analysis failed: {str(e)}"
        )
