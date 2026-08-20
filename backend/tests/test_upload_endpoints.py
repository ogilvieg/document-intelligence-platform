"""Upload readiness contract tests."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.models.database import DocumentInDB


client = TestClient(app)


def _stored_document(document_id):
    return DocumentInDB(
        id=document_id,
        title="resume.pdf",
        doc_type="pdf",
        source="upload",
        version="1.0",
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


def _post_upload(*, total_chunks, embedding_result=None, embedding_error=None):
    document_id = uuid4()
    db = MagicMock()
    db.create_document = AsyncMock(return_value=_stored_document(document_id))
    db.wait_until_ready = AsyncMock()
    db.delete_document = AsyncMock(return_value=True)

    with patch("app.api.routes.get_db_service", return_value=db), \
         patch("app.api.routes.document_ingestion_service") as ingestion, \
         patch("app.api.routes.chunking_service") as chunking, \
         patch("app.api.routes.embedding_service") as embeddings:
        ingestion.ingest_document.return_value = {
            "text": "Experienced engineer",
            "page_count": 1,
            "metadata": {"parser": "test"},
        }
        chunking.chunk_document = AsyncMock(return_value={
            "total_chunks": total_chunks,
            "average_chunk_size": 20,
            "chunk_size_config": 1000,
            "chunk_overlap_config": 200,
        })
        embeddings.embed_document_chunks = AsyncMock(
            return_value=embedding_result,
            side_effect=embedding_error,
        )
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("resume.pdf", b"pdf", "application/pdf")},
        )

    return response, db, document_id


def test_upload_does_not_report_success_when_embeddings_fail():
    response, db, document_id = _post_upload(
        total_chunks=1,
        embedding_error=RuntimeError("embedding provider unavailable"),
    )

    assert response.status_code == 503
    db.delete_document.assert_awaited_once_with(document_id)


def test_upload_does_not_report_success_with_partial_embeddings():
    response, db, document_id = _post_upload(
        total_chunks=2,
        embedding_result=[MagicMock()],
    )

    assert response.status_code == 503
    db.delete_document.assert_awaited_once_with(document_id)


def test_upload_does_not_report_success_without_searchable_chunks():
    response, db, document_id = _post_upload(
        total_chunks=0,
        embedding_result=[],
    )

    assert response.status_code == 422
    db.delete_document.assert_awaited_once_with(document_id)


def test_successful_upload_reports_embedding_readiness():
    response, db, _ = _post_upload(
        total_chunks=2,
        embedding_result=[MagicMock(), MagicMock()],
    )

    assert response.status_code == 201
    assert response.json()["metadata"]["embeddings"] == {
        "status": "ready",
        "total_embeddings": 2,
    }
    db.delete_document.assert_not_awaited()
