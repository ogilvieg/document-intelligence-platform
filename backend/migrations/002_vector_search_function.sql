-- Function for vector similarity search with filters
-- This is called from the application layer via RPC

CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5,
    filter_doc_type text DEFAULT NULL,
    filter_document_ids uuid[] DEFAULT NULL
)
RETURNS TABLE (
    chunk jsonb,
    similarity float,
    document_title text,
    document_type text
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        to_jsonb(c.*) as chunk,
        1 - (e.vector <=> query_embedding) as similarity,
        d.title as document_title,
        d.doc_type as document_type
    FROM embeddings e
    JOIN chunks c ON e.chunk_id = c.id
    JOIN documents d ON c.document_id = d.id
    WHERE 
        1 - (e.vector <=> query_embedding) > match_threshold
        AND (filter_doc_type IS NULL OR d.doc_type = filter_doc_type)
        AND (filter_document_ids IS NULL OR d.id = ANY(filter_document_ids))
    ORDER BY e.vector <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Comment
COMMENT ON FUNCTION match_chunks IS 'Search for similar chunks using cosine similarity with optional filters';
