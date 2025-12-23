"""API routes."""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form
from typing import List, Optional
from datetime import datetime
from uuid import uuid4
import structlog

from app.models import (
    DocumentUploadRequest,
    DocumentResponse,
    AnalysisRequest,
    AnalysisResponse,
    Citation,
    DocumentType
)
from app.services import LLMService, DocumentIngestionService, ChunkingService

logger = structlog.get_logger()
router = APIRouter()

# Initialize services
llm_service = LLMService()
document_ingestion_service = DocumentIngestionService()
chunking_service = ChunkingService()


@router.post("/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
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
        chunking_result = chunking_service.chunk_document(
            document_text=result['text'],
            document_id=document_id,
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


@router.post("/analyze", response_model=AnalysisResponse)
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
