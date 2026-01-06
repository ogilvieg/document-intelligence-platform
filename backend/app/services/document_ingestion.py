"""Document ingestion service for parsing PDF, Markdown, and HTML files."""

import io
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import structlog
from PyPDF2 import PdfReader
import pdfplumber
from bs4 import BeautifulSoup
import markdown

from app.config import settings

logger = structlog.get_logger()


class DocumentIngestionService:
    """Service for parsing and normalizing documents from various formats."""
    
    SUPPORTED_TYPES = {
        'application/pdf': 'pdf',
        'text/markdown': 'markdown',
        'text/x-markdown': 'markdown',  # Alternative markdown MIME type
        'text/html': 'html',
        'text/plain': 'text',
        'application/octet-stream': 'auto'  # Generic binary - detect by extension
    }
    
    # File extension to type mapping (for octet-stream fallback)
    EXTENSION_MAP = {
        '.pdf': 'pdf',
        '.md': 'markdown',
        '.markdown': 'markdown',
        '.html': 'html',
        '.htm': 'html',
        '.txt': 'text'
    }
    
    def __init__(self):
        """Initialize document ingestion service."""
        self.max_file_size_bytes = settings.max_file_size_mb * 1024 * 1024
    
    def validate_file(self, file_content: bytes, content_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file size and type.
        
        Args:
            file_content: Raw file bytes
            content_type: MIME type of the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        if len(file_content) > self.max_file_size_bytes:
            return False, f"File size exceeds maximum of {settings.max_file_size_mb}MB"
        
        # Check content type
        if content_type not in self.SUPPORTED_TYPES:
            supported = ', '.join(self.SUPPORTED_TYPES.keys())
            logger.warning("unsupported_content_type", 
                          content_type=content_type,
                          supported_types=list(self.SUPPORTED_TYPES.keys()))
            return False, f"Unsupported file type. Supported types: {supported}"
        
        return True, None
    
    def parse_pdf(self, file_content: bytes) -> Dict[str, Any]:
        """
        Parse PDF file and extract text content.
        
        Uses pdfplumber for better text extraction with layout preservation.
        Falls back to PyPDF2 if pdfplumber fails.
        
        Args:
            file_content: Raw PDF bytes
            
        Returns:
            Dict with 'text', 'metadata', and 'page_count'
        """
        logger.info("pdf_parsing_started", size_bytes=len(file_content))
        
        try:
            # Primary method: pdfplumber (better layout preservation)
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                pages = []
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        pages.append(f"--- Page {page_num} ---\n{text}")
                
                full_text = "\n\n".join(pages)
                
                metadata = {
                    'parser': 'pdfplumber',
                    'page_count': len(pdf.pages)
                }
                
                # Try to extract PDF metadata
                if pdf.metadata:
                    metadata.update({
                        'title': pdf.metadata.get('Title', ''),
                        'author': pdf.metadata.get('Author', ''),
                        'creator': pdf.metadata.get('Creator', '')
                    })
                
                logger.info(
                    "pdf_parsing_completed",
                    page_count=len(pdf.pages),
                    text_length=len(full_text)
                )
                
                return {
                    'text': full_text,
                    'metadata': metadata,
                    'page_count': len(pdf.pages)
                }
                
        except Exception as e:
            logger.warning("pdfplumber_failed_trying_pypdf2", error=str(e))
            
            # Fallback: PyPDF2
            try:
                reader = PdfReader(io.BytesIO(file_content))
                pages = []
                
                for page_num, page in enumerate(reader.pages, 1):
                    text = page.extract_text()
                    if text:
                        pages.append(f"--- Page {page_num} ---\n{text}")
                
                full_text = "\n\n".join(pages)
                
                metadata = {
                    'parser': 'pypdf2',
                    'page_count': len(reader.pages)
                }
                
                # Extract PDF metadata
                if reader.metadata:
                    metadata.update({
                        'title': reader.metadata.get('/Title', ''),
                        'author': reader.metadata.get('/Author', ''),
                        'creator': reader.metadata.get('/Creator', '')
                    })
                
                logger.info(
                    "pdf_parsing_completed",
                    parser="pypdf2_fallback",
                    page_count=len(reader.pages),
                    text_length=len(full_text)
                )
                
                return {
                    'text': full_text,
                    'metadata': metadata,
                    'page_count': len(reader.pages)
                }
                
            except Exception as fallback_error:
                logger.error(
                    "pdf_parsing_failed",
                    error=str(fallback_error),
                    error_type=type(fallback_error).__name__
                )
                raise ValueError(f"Failed to parse PDF: {str(fallback_error)}")
    
    def parse_markdown(self, file_content: bytes) -> Dict[str, Any]:
        """
        Parse Markdown file and extract content.
        
        Preserves markdown syntax for later processing but also
        generates plain text version.
        
        Args:
            file_content: Raw markdown bytes
            
        Returns:
            Dict with 'text', 'html', and 'metadata'
        """
        logger.info("markdown_parsing_started", size_bytes=len(file_content))
        
        try:
            # Decode to text
            text = file_content.decode('utf-8')
            
            # Convert to HTML for reference
            html = markdown.markdown(text, extensions=['extra', 'codehilite'])
            
            # Extract metadata (if present in YAML front matter)
            metadata = {
                'parser': 'markdown',
                'format': 'markdown',
                'has_html': True
            }
            
            logger.info(
                "markdown_parsing_completed",
                text_length=len(text),
                html_length=len(html)
            )
            
            return {
                'text': text,
                'html': html,
                'metadata': metadata
            }
            
        except UnicodeDecodeError as e:
            logger.error("markdown_decode_failed", error=str(e))
            raise ValueError(f"Failed to decode markdown file: {str(e)}")
        except Exception as e:
            logger.error(
                "markdown_parsing_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise ValueError(f"Failed to parse markdown: {str(e)}")
    
    def parse_html(self, file_content: bytes) -> Dict[str, Any]:
        """
        Parse HTML file and extract text content.
        
        Uses BeautifulSoup to clean HTML and extract readable text.
        Preserves some structure (headings, paragraphs).
        
        Args:
            file_content: Raw HTML bytes
            
        Returns:
            Dict with 'text', 'metadata'
        """
        logger.info("html_parsing_started", size_bytes=len(file_content))
        
        try:
            # Parse HTML
            soup = BeautifulSoup(file_content, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract title if present
            title = soup.title.string if soup.title else None
            
            # Extract text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up excessive whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = '\n'.join(lines)
            
            metadata = {
                'parser': 'beautifulsoup',
                'format': 'html',
                'title': title
            }
            
            logger.info(
                "html_parsing_completed",
                text_length=len(text),
                title=title
            )
            
            return {
                'text': text,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(
                "html_parsing_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise ValueError(f"Failed to parse HTML: {str(e)}")
    
    def ingest_document(
        self,
        file_content: bytes,
        filename: str,
        content_type: str
    ) -> Dict[str, Any]:
        """
        Ingest a document and extract its content.
        
        Main entry point that validates, routes to appropriate parser,
        and normalizes output.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            content_type: MIME type
            
        Returns:
            Dict with 'text', 'metadata', 'source'
            
        Raises:
            ValueError: If validation fails or parsing errors occur
        """
        logger.info(
            "document_ingestion_started",
            filename=filename,
            content_type=content_type,
            size_bytes=len(file_content)
        )
        
        # Validate
        is_valid, error_message = self.validate_file(file_content, content_type)
        if not is_valid:
            logger.error("document_validation_failed", error=error_message)
            raise ValueError(error_message)
        
        # Determine document type
        doc_type = self.SUPPORTED_TYPES.get(content_type)
        
        # If content_type is generic octet-stream, detect by file extension
        if doc_type == 'auto':
            ext = Path(filename).suffix.lower()
            doc_type = self.EXTENSION_MAP.get(ext)
            if not doc_type:
                supported_exts = ', '.join(self.EXTENSION_MAP.keys())
                raise ValueError(f"Could not determine file type from extension '{ext}'. Supported extensions: {supported_exts}")
            logger.info("file_type_detected_by_extension", filename=filename, extension=ext, detected_type=doc_type)
        
        # Route to appropriate parser
        try:
            if doc_type == 'pdf':
                result = self.parse_pdf(file_content)
            elif doc_type == 'markdown':
                result = self.parse_markdown(file_content)
            elif doc_type == 'html':
                result = self.parse_html(file_content)
            elif doc_type == 'text':
                # Plain text - just decode
                text = file_content.decode('utf-8')
                result = {
                    'text': text,
                    'metadata': {'parser': 'plain_text', 'format': 'text'}
                }
            else:
                raise ValueError(f"Unsupported document type: {doc_type}")
            
            # Add source information
            result['source'] = filename
            result['content_type'] = content_type
            
            logger.info(
                "document_ingestion_completed",
                filename=filename,
                text_length=len(result.get('text', '')),
                parser=result['metadata'].get('parser')
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "document_ingestion_failed",
                filename=filename,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
