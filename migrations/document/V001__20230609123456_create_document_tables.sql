-- Initial migration for document tables
-- Creates the tables for documents, document_chunks and document_versions

-- Documents Table
CREATE TABLE IF NOT EXISTS profiler_schema.documents (
    document_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    profile_id VARCHAR(36),
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'processing' NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    metadata TEXT
);

-- Document Chunks Table
CREATE TABLE IF NOT EXISTS profiler_schema.document_chunks (
    chunk_id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL REFERENCES profiler_schema.documents(document_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    metadata TEXT
);

-- Document Versions Table
CREATE TABLE IF NOT EXISTS profiler_schema.document_versions (
    version_id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL REFERENCES profiler_schema.documents(document_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    created_by VARCHAR(36),
    comment TEXT,
    metadata TEXT
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON profiler_schema.documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_profile_id ON profiler_schema.documents(profile_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON profiler_schema.documents(status);

CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON profiler_schema.document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_chunk_index ON profiler_schema.document_chunks(chunk_index);

CREATE INDEX IF NOT EXISTS idx_document_versions_document_id ON profiler_schema.document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_document_versions_version_number ON profiler_schema.document_versions(version_number); 