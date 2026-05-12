"""
Direct PostgreSQL database service using asyncpg (AWS RDS backend).

Drop-in replacement for DatabaseService — exposes identical public methods.
Selected automatically when DATABASE_URL is set in the environment.
"""

from typing import List, Optional
from uuid import UUID
import json
import asyncpg
from pgvector.asyncpg import register_vector

import structlog

from app.config import settings
from app.models.database import (
    DocumentCreate, DocumentInDB,
    ChunkCreate, ChunkInDB,
    EmbeddingCreate, EmbeddingInDB,
    SearchFilters, RetrievedChunk,
)

logger = structlog.get_logger()


class PostgresDatabaseService:
    """
    Database service backed by AWS RDS PostgreSQL via asyncpg.

    All public methods are signature-compatible with DatabaseService so
    callers (routes, other services) require zero changes.
    """

    def __init__(self, database_url: str):
        self._database_url = database_url
        self._pool: Optional[asyncpg.Pool] = None

    # ------------------------------------------------------------------
    # Connection pool lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Create the asyncpg connection pool and register pgvector codec."""
        async def _init_conn(conn: asyncpg.Connection) -> None:
            # Ensure pgvector operators (<=>, <#>, <+>) are resolvable
            await conn.execute("SET search_path = docsage, public")
            await register_vector(conn)

        # asyncpg doesn't honour sslmode= in the URL — strip it out and
        # pass ssl=True explicitly so RDS connections work on Render.
        import ssl as _ssl
        from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

        parsed = urlparse(self._database_url)
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        sslmode = query_params.pop("sslmode", ["disable"])[0]
        clean_url = urlunparse(parsed._replace(query=urlencode(
            {k: v[0] for k, v in query_params.items()}
        )))

        ssl_ctx: _ssl.SSLContext | bool = False
        if sslmode in ("require", "verify-ca", "verify-full"):
            ssl_ctx = _ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = _ssl.CERT_NONE  # RDS CA not in default bundle

        self._pool = await asyncpg.create_pool(
            clean_url,
            min_size=2,
            max_size=10,
            ssl=ssl_ctx or None,
            init=_init_conn,
        )
        logger.info("postgres_pool_created", database_url=self._database_url.split("@")[-1])

    async def disconnect(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            await self._pool.close()
            logger.info("postgres_pool_closed")

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("PostgresDatabaseService not connected yet — pool is still initializing.")
        return self._pool

    async def wait_until_ready(self, timeout: float = 30.0) -> None:
        """Wait until the connection pool is ready (useful after background connect)."""
        import asyncio
        deadline = asyncio.get_event_loop().time() + timeout
        while self._pool is None:
            if asyncio.get_event_loop().time() > deadline:
                raise RuntimeError("Timed out waiting for postgres pool to be ready.")
            await asyncio.sleep(0.1)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_row(row: asyncpg.Record, json_fields: tuple = ("metadata",)) -> dict:
        """Convert an asyncpg Record to a dict, parsing any JSON string fields."""
        d = dict(row)
        for field in json_fields:
            if field in d and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except (ValueError, TypeError):
                    d[field] = {}
        return d

    # ------------------------------------------------------------------
    # Document Operations
    # ------------------------------------------------------------------

    async def create_document(self, document: DocumentCreate) -> DocumentInDB:
        """Insert a new document row and return it."""
        try:
            row = await self.pool.fetchrow(
                """
                INSERT INTO documents (title, doc_type, source, version, content_hash, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
                """,
                document.title,
                document.doc_type,
                document.source,
                document.version,
                document.content_hash,
                json.dumps(document.metadata or {}),
            )
            logger.info("document_created", document_id=str(row["id"]))
            return DocumentInDB(**self._parse_row(row))
        except Exception as e:
            logger.error("document_creation_failed", error=str(e))
            raise

    async def get_document(self, document_id: UUID) -> Optional[DocumentInDB]:
        """Fetch a document by primary key."""
        try:
            row = await self.pool.fetchrow(
                "SELECT * FROM documents WHERE id = $1",
                document_id,
            )
            if row is None:
                return None
            return DocumentInDB(**self._parse_row(row))
        except Exception as e:
            logger.error("document_fetch_failed", document_id=str(document_id), error=str(e))
            return None

    async def list_documents(
        self,
        doc_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[DocumentInDB]:
        """List documents, optionally filtered by doc_type."""
        try:
            if doc_type:
                rows = await self.pool.fetch(
                    "SELECT * FROM documents WHERE doc_type = $1 ORDER BY upload_date DESC LIMIT $2",
                    doc_type,
                    limit,
                )
            else:
                rows = await self.pool.fetch(
                    "SELECT * FROM documents ORDER BY upload_date DESC LIMIT $1",
                    limit,
                )
            return [DocumentInDB(**self._parse_row(r)) for r in rows]
        except Exception as e:
            logger.error("document_list_failed", error=str(e))
            return []

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document (chunks + embeddings cascade via FK)."""
        try:
            await self.pool.execute(
                "DELETE FROM documents WHERE id = $1",
                document_id,
            )
            logger.info("document_deleted", document_id=str(document_id))
            return True
        except Exception as e:
            logger.error("document_deletion_failed", document_id=str(document_id), error=str(e))
            return False

    # ------------------------------------------------------------------
    # Chunk Operations
    # ------------------------------------------------------------------

    async def create_chunks(self, chunks: List[ChunkCreate]) -> List[ChunkInDB]:
        """Bulk-insert chunks, idempotent on (document_id, chunk_index)."""
        try:
            rows = await self.pool.fetch(
                """
                INSERT INTO chunks (document_id, chunk_index, text, token_count, metadata)
                SELECT
                    d.document_id::uuid,
                    d.chunk_index,
                    d.text,
                    d.token_count,
                    d.metadata::jsonb
                FROM jsonb_to_recordset($1::jsonb) AS d(
                    document_id text,
                    chunk_index int,
                    text text,
                    token_count int,
                    metadata text
                )
                ON CONFLICT (document_id, chunk_index) DO NOTHING
                RETURNING *
                """,
                json.dumps([
                    {
                        "document_id": str(c.document_id),
                        "chunk_index": c.chunk_index,
                        "text": c.text,
                        "token_count": c.token_count,
                        "metadata": json.dumps(c.metadata or {}),
                    }
                    for c in chunks
                ]),
            )
            created = [ChunkInDB(**self._parse_row(r)) for r in rows]
            logger.info("chunks_created", count=len(created))
            return created
        except Exception as e:
            logger.error("chunk_creation_failed", error=str(e))
            raise

    async def get_chunks_by_document(self, document_id: UUID) -> List[ChunkInDB]:
        """Fetch all chunks for a document, ordered by chunk_index."""
        try:
            rows = await self.pool.fetch(
                "SELECT * FROM chunks WHERE document_id = $1 ORDER BY chunk_index",
                document_id,
            )
            return [ChunkInDB(**self._parse_row(r)) for r in rows]
        except Exception as e:
            logger.error("chunk_fetch_failed", document_id=str(document_id), error=str(e))
            return []

    async def get_chunk(self, chunk_id: UUID) -> Optional[ChunkInDB]:
        """Fetch a single chunk by primary key."""
        try:
            row = await self.pool.fetchrow(
                "SELECT * FROM chunks WHERE id = $1",
                chunk_id,
            )
            if row is None:
                return None
            return ChunkInDB(**self._parse_row(row))
        except Exception as e:
            logger.error("chunk_fetch_failed", chunk_id=str(chunk_id), error=str(e))
            return None

    # ------------------------------------------------------------------
    # Embedding Operations
    # ------------------------------------------------------------------

    async def create_embedding(self, embedding: EmbeddingCreate) -> EmbeddingInDB:
        """Insert or update an embedding, idempotent on (chunk_id, model)."""
        try:
            from pgvector.asyncpg import Vector  # noqa: PLC0415
            row = await self.pool.fetchrow(
                """
                INSERT INTO embeddings (chunk_id, vector, model_name, created_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (chunk_id, model_name) DO UPDATE
                    SET vector     = EXCLUDED.vector,
                        created_at = NOW()
                RETURNING *
                """,
                embedding.chunk_id,
                embedding.vector,
                embedding.model_name,
            )
            logger.info("embedding_created", chunk_id=str(embedding.chunk_id))
            result = dict(row)
            if hasattr(result.get("vector"), "tolist"):
                result["vector"] = result["vector"].tolist()
            return EmbeddingInDB(**result)
        except Exception as e:
            logger.error("embedding_creation_failed", error=str(e))
            raise

    async def get_embedding(
        self,
        chunk_id: UUID,
        model_name: str = "text-embedding-3-small",
    ) -> Optional[EmbeddingInDB]:
        """Fetch the embedding for a chunk + model combination."""
        try:
            row = await self.pool.fetchrow(
                "SELECT * FROM embeddings WHERE chunk_id = $1 AND model_name = $2",
                chunk_id,
                model_name,
            )
            if row is None:
                return None
            result = dict(row)
            if hasattr(result.get("vector"), "tolist"):
                result["vector"] = result["vector"].tolist()
            return EmbeddingInDB(**result)
        except Exception as e:
            logger.error("embedding_fetch_failed", chunk_id=str(chunk_id), error=str(e))
            return None

    async def has_embedding(
        self,
        chunk_id: UUID,
        model_name: str = "text-embedding-3-small",
    ) -> bool:
        """Return True if this chunk already has an embedding (idempotency check)."""
        return await self.get_embedding(chunk_id, model_name) is not None

    # ------------------------------------------------------------------
    # Vector Search
    # ------------------------------------------------------------------

    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        filters: Optional[SearchFilters] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.5,
    ) -> List[RetrievedChunk]:
        """
        Semantic search via the docsage.match_chunks() stored function.

        Calls the same PostgreSQL function created by docsage_schema.sql so
        the query plan (HNSW index) is identical regardless of which Python
        client is used.
        """
        try:
            doc_ids = None
            doc_type = None
            if filters:
                doc_ids = [str(d) for d in filters.document_ids] if filters.document_ids else None
                doc_type = filters.doc_type

            rows = await self.pool.fetch(
                "SELECT * FROM match_chunks($1::vector, $2, $3, $4, $5)",
                query_embedding,        # list[float] — pgvector codec + explicit cast
                similarity_threshold,
                top_k,
                doc_ids,
                doc_type,
            )

            if not rows:
                logger.info("no_chunks_found", top_k=top_k)
                return []

            retrieved: List[RetrievedChunk] = []
            for r in rows:
                chunk = ChunkInDB(
                    id=r["chunk_id"],
                    document_id=r["document_id"],
                    chunk_index=r["chunk_index"],
                    text=r["text"],
                    token_count=None,
                    metadata={},
                )
                retrieved.append(RetrievedChunk(
                    chunk=chunk,
                    similarity_score=float(r["similarity"]),
                    document_title=r.get("document_title"),
                    document_type=r.get("doc_type"),
                ))

            logger.info("chunks_retrieved", count=len(retrieved), top_k=top_k)
            return retrieved

        except Exception as e:
            logger.error("vector_search_failed", error=str(e))
            return []
