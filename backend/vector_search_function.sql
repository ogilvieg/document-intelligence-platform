-- Vector Search Function for Document Intelligence Platform
-- Run this in your Supabase SQL Editor

-- Drop the function if it exists
DROP FUNCTION IF EXISTS match_chunks(vector(1536), float, int, text, uuid[]);

-- Create the vector search function
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
        jsonb_build_object(
            'id', c.id,
            'document_id', c.document_id,
            'chunk_index', c.chunk_index,
            'text', c.text,
            'token_count', c.token_count,
            'metadata', c.metadata,
            'created_at', c.created_at
        ) AS chunk,
        (1 - (e.vector <=> query_embedding))::float AS similarity,
        d.title AS document_title,
        d.doc_type AS document_type
    FROM embeddings e
    JOIN chunks c ON e.chunk_id = c.id
    JOIN documents d ON c.document_id = d.id
    WHERE 
        (1 - (e.vector <=> query_embedding)) > match_threshold
        AND (filter_doc_type IS NULL OR d.doc_type = filter_doc_type)
        AND (filter_document_ids IS NULL OR d.id = ANY(filter_document_ids))
    ORDER BY e.vector <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Add a comment explaining the function
COMMENT ON FUNCTION match_chunks IS 'Semantic search function that finds similar chunks using vector cosine similarity';
