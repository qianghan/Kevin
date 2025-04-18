-- Migration to create optimized indexes for document queries and search
-- This creates advanced indexes for improved query performance

-- Create GIN index for text search on document content
CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_text_gin ON profiler_schema.document_chunks
USING gin(to_tsvector('english', chunk_text));

-- Create index on document status and created_at for filtering by status with date range
CREATE INDEX IF NOT EXISTS idx_documents_status_created_at ON profiler_schema.documents(status, created_at);

-- Create index on document mime_type for filtering by file type
CREATE INDEX IF NOT EXISTS idx_documents_mime_type ON profiler_schema.documents(mime_type);

-- Create index on combined user_id and created_at for efficient user timeline queries
CREATE INDEX IF NOT EXISTS idx_documents_user_id_created_at ON profiler_schema.documents(user_id, created_at);

-- Create index on combined profile_id and created_at for efficient profile timeline queries
CREATE INDEX IF NOT EXISTS idx_documents_profile_id_created_at ON profiler_schema.documents(profile_id, created_at);

-- Create index for partial filtering by processed documents
CREATE INDEX IF NOT EXISTS idx_documents_processed_partial ON profiler_schema.documents(user_id, processed_at) 
WHERE status = 'ready';

-- Create indexes for document versions
CREATE INDEX IF NOT EXISTS idx_document_versions_created_at ON profiler_schema.document_versions(created_at);
CREATE INDEX IF NOT EXISTS idx_document_versions_created_by ON profiler_schema.document_versions(created_by);

-- Add btree index on document chunks for sorting by chunk_index
CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_index_btree ON profiler_schema.document_chunks(document_id, chunk_index);

-- Add index on filename for document search by filename
CREATE INDEX IF NOT EXISTS idx_documents_filename ON profiler_schema.documents(filename);

-- Create index for partial JSON metadata fields
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON profiler_schema.documents
USING gin((metadata::jsonb));

-- Add this comment so that migration tools know this migration was successful
COMMENT ON TABLE profiler_schema.documents IS 'Document storage with optimized indexes for search and filtering'; 