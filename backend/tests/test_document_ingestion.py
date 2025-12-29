"""Unit tests for document ingestion service."""

import pytest
from app.services.document_ingestion import DocumentIngestionService


@pytest.fixture
def ingestion_service():
    """Create a document ingestion service instance."""
    return DocumentIngestionService()


def test_validate_file_size(ingestion_service):
    """Test file size validation."""
    # Valid file size
    small_content = b"Hello World"
    is_valid, error = ingestion_service.validate_file(small_content, "text/markdown")
    assert is_valid is True
    assert error is None
    
    # File too large
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB (exceeds 10MB limit)
    is_valid, error = ingestion_service.validate_file(large_content, "text/markdown")
    assert is_valid is False
    assert "exceeds maximum" in error


def test_validate_file_type(ingestion_service):
    """Test file type validation."""
    content = b"test content"
    
    # Valid types
    for content_type in ["application/pdf", "text/markdown", "text/html", "text/plain"]:
        is_valid, error = ingestion_service.validate_file(content, content_type)
        assert is_valid is True
        assert error is None
    
    # Invalid type
    is_valid, error = ingestion_service.validate_file(content, "application/zip")
    assert is_valid is False
    assert "Unsupported file type" in error


def test_parse_markdown(ingestion_service):
    """Test markdown parsing."""
    markdown_content = b"""# Test Document

This is a **test** document.

## Section 1

- Item 1
- Item 2

```python
print("Hello")
```
"""
    
    result = ingestion_service.parse_markdown(markdown_content)
    
    assert 'text' in result
    assert 'html' in result
    assert 'metadata' in result
    assert result['metadata']['parser'] == 'markdown'
    assert '# Test Document' in result['text']
    assert 'This is a **test** document' in result['text']
    assert len(result['html']) > 0


def test_parse_html(ingestion_service):
    """Test HTML parsing."""
    html_content = b"""<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <script>console.log("remove me");</script>
    <style>body { color: red; }</style>
</head>
<body>
    <h1>Main Title</h1>
    <p>This is a paragraph.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
</body>
</html>
"""
    
    result = ingestion_service.parse_html(html_content)
    
    assert 'text' in result
    assert 'metadata' in result
    assert result['metadata']['parser'] == 'beautifulsoup'
    assert result['metadata']['title'] == 'Test Page'
    
    # Check that content is extracted
    assert 'Main Title' in result['text']
    assert 'This is a paragraph' in result['text']
    assert 'Item 1' in result['text']
    
    # Check that script and style are removed
    assert 'console.log' not in result['text']
    assert 'color: red' not in result['text']


def test_ingest_document_markdown(ingestion_service):
    """Test complete document ingestion for markdown."""
    markdown_content = b"# Test\n\nContent here"
    
    result = ingestion_service.ingest_document(
        file_content=markdown_content,
        filename="test.md",
        content_type="text/markdown"
    )
    
    assert result['source'] == 'test.md'
    assert result['content_type'] == 'text/markdown'
    assert '# Test' in result['text']
    assert result['metadata']['parser'] == 'markdown'


def test_ingest_document_html(ingestion_service):
    """Test complete document ingestion for HTML."""
    html_content = b"<html><body><h1>Test</h1><p>Content</p></body></html>"
    
    result = ingestion_service.ingest_document(
        file_content=html_content,
        filename="test.html",
        content_type="text/html"
    )
    
    assert result['source'] == 'test.html'
    assert result['content_type'] == 'text/html'
    assert 'Test' in result['text']
    assert 'Content' in result['text']
    assert result['metadata']['parser'] == 'beautifulsoup'


def test_ingest_document_plain_text(ingestion_service):
    """Test complete document ingestion for plain text."""
    text_content = b"Plain text content\nLine 2\nLine 3"
    
    result = ingestion_service.ingest_document(
        file_content=text_content,
        filename="test.txt",
        content_type="text/plain"
    )
    
    assert result['source'] == 'test.txt'
    assert result['content_type'] == 'text/plain'
    assert 'Plain text content' in result['text']
    assert result['metadata']['parser'] == 'plain_text'


def test_ingest_document_invalid_type(ingestion_service):
    """Test document ingestion with invalid file type."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        ingestion_service.ingest_document(
            file_content=b"content",
            filename="test.zip",
            content_type="application/zip"
        )


def test_ingest_document_too_large(ingestion_service):
    """Test document ingestion with file too large."""
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    
    with pytest.raises(ValueError, match="exceeds maximum"):
        ingestion_service.ingest_document(
            file_content=large_content,
            filename="large.md",
            content_type="text/markdown"
        )
