-- Profiler Application Database Schema
-- This script initializes the PostgreSQL database for the Profiler application

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create roles
CREATE ROLE profiler_app WITH LOGIN PASSWORD 'profilerdev';
GRANT ALL PRIVILEGES ON DATABASE profiler TO profiler_app;

-- Create schema
CREATE SCHEMA IF NOT EXISTS profiler_schema;
GRANT ALL PRIVILEGES ON SCHEMA profiler_schema TO profiler_app;

-- Set search path
SET search_path TO profiler_schema, public;
ALTER ROLE profiler_app SET search_path TO profiler_schema, public;

-- Create tables

-- Users Table
CREATE TABLE profiler_schema.users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(512) NOT NULL,
    password_salt VARCHAR(128) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    is_locked BOOLEAN DEFAULT FALSE,
    login_attempts INTEGER DEFAULT 0
);

-- Roles Table
CREATE TABLE profiler_schema.roles (
    role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Permissions Table
CREATE TABLE profiler_schema.permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    permission_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Roles Table
CREATE TABLE profiler_schema.user_roles (
    user_id UUID REFERENCES profiler_schema.users(user_id) ON DELETE CASCADE,
    role_id UUID REFERENCES profiler_schema.roles(role_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- Role Permissions Table
CREATE TABLE profiler_schema.role_permissions (
    role_id UUID REFERENCES profiler_schema.roles(role_id) ON DELETE CASCADE,
    permission_id UUID REFERENCES profiler_schema.permissions(permission_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

-- Profiles Table
CREATE TABLE profiler_schema.profiles (
    profile_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiler_schema.users(user_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    current_section VARCHAR(50),
    status VARCHAR(20) DEFAULT 'in_progress',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

-- Sections Table
CREATE TABLE profiler_schema.sections (
    section_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiler_schema.profiles(profile_id) ON DELETE CASCADE,
    section_key VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'not_started',
    order_index INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    data JSONB,
    UNIQUE (profile_id, section_key)
);

-- Answers Table
CREATE TABLE profiler_schema.answers (
    answer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiler_schema.profiles(profile_id) ON DELETE CASCADE,
    section_key VARCHAR(50) NOT NULL,
    question_key VARCHAR(50) NOT NULL,
    answer_text TEXT,
    answer_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (profile_id, section_key, question_key)
);

-- Documents Table
CREATE TABLE profiler_schema.documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiler_schema.users(user_id) ON DELETE CASCADE,
    profile_id UUID REFERENCES profiler_schema.profiles(profile_id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'processing',
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Document Chunks Table
CREATE TABLE profiler_schema.document_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES profiler_schema.documents(document_id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    UNIQUE (document_id, chunk_index)
);

-- Recommendations Table
CREATE TABLE profiler_schema.recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES profiler_schema.profiles(profile_id) ON DELETE CASCADE,
    section_key VARCHAR(50),
    question_key VARCHAR(50),
    recommendation_text TEXT NOT NULL,
    source_document_id UUID REFERENCES profiler_schema.documents(document_id) ON DELETE SET NULL,
    source_chunk_id UUID REFERENCES profiler_schema.document_chunks(chunk_id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    relevance_score FLOAT,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB
);

-- Sessions Table
CREATE TABLE profiler_schema.sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiler_schema.users(user_id) ON DELETE CASCADE,
    profile_id UUID REFERENCES profiler_schema.profiles(profile_id) ON DELETE SET NULL,
    token VARCHAR(512) UNIQUE,
    refresh_token VARCHAR(512) UNIQUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create indexes

-- Users indexes
CREATE INDEX idx_users_username ON profiler_schema.users (username);
CREATE INDEX idx_users_email ON profiler_schema.users (email);

-- Profiles indexes
CREATE INDEX idx_profiles_user_id ON profiler_schema.profiles (user_id);
CREATE INDEX idx_profiles_status ON profiler_schema.profiles (status);

-- Sections indexes
CREATE INDEX idx_sections_profile_id ON profiler_schema.sections (profile_id);
CREATE INDEX idx_sections_section_key ON profiler_schema.sections (section_key);

-- Answers indexes
CREATE INDEX idx_answers_profile_id ON profiler_schema.answers (profile_id);
CREATE INDEX idx_answers_section_key ON profiler_schema.answers (section_key);
CREATE INDEX idx_answers_question_key ON profiler_schema.answers (question_key);

-- Documents indexes
CREATE INDEX idx_documents_user_id ON profiler_schema.documents (user_id);
CREATE INDEX idx_documents_profile_id ON profiler_schema.documents (profile_id);
CREATE INDEX idx_documents_status ON profiler_schema.documents (status);

-- Document chunks indexes
CREATE INDEX idx_document_chunks_document_id ON profiler_schema.document_chunks (document_id);

-- Recommendations indexes
CREATE INDEX idx_recommendations_profile_id ON profiler_schema.recommendations (profile_id);
CREATE INDEX idx_recommendations_section_key ON profiler_schema.recommendations (section_key);
CREATE INDEX idx_recommendations_question_key ON profiler_schema.recommendations (question_key);
CREATE INDEX idx_recommendations_status ON profiler_schema.recommendations (status);

-- Sessions indexes
CREATE INDEX idx_sessions_user_id ON profiler_schema.sessions (user_id);
CREATE INDEX idx_sessions_token ON profiler_schema.sessions (token);
CREATE INDEX idx_sessions_refresh_token ON profiler_schema.sessions (refresh_token);

-- Insert default roles
INSERT INTO profiler_schema.roles (role_name, description)
VALUES 
    ('admin', 'Administrator with full system access'),
    ('user', 'Standard user with access to own resources'),
    ('manager', 'Manager with access to team resources');

-- Insert default permissions
INSERT INTO profiler_schema.permissions (permission_name, description)
VALUES
    ('profile:create', 'Create profile'),
    ('profile:read:own', 'Read own profiles'),
    ('profile:read:all', 'Read all profiles'),
    ('profile:update:own', 'Update own profiles'),
    ('profile:update:all', 'Update all profiles'),
    ('profile:delete:own', 'Delete own profiles'),
    ('profile:delete:all', 'Delete all profiles'),
    ('document:upload', 'Upload documents'),
    ('document:read:own', 'Read own documents'),
    ('document:read:all', 'Read all documents'),
    ('document:delete:own', 'Delete own documents'),
    ('document:delete:all', 'Delete all documents'),
    ('user:create', 'Create users'),
    ('user:read:own', 'Read own user data'),
    ('user:read:all', 'Read all user data'),
    ('user:update:own', 'Update own user data'),
    ('user:update:all', 'Update all user data'),
    ('user:delete:own', 'Delete own user account'),
    ('user:delete:all', 'Delete any user account');

-- Assign permissions to roles
INSERT INTO profiler_schema.role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM profiler_schema.roles r
CROSS JOIN profiler_schema.permissions p
WHERE r.role_name = 'admin';

INSERT INTO profiler_schema.role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM profiler_schema.roles r
CROSS JOIN profiler_schema.permissions p
WHERE r.role_name = 'user' AND p.permission_name LIKE '%:own' OR p.permission_name IN ('profile:create', 'document:upload');

INSERT INTO profiler_schema.role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM profiler_schema.roles r
CROSS JOIN profiler_schema.permissions p
WHERE r.role_name = 'manager' AND (p.permission_name LIKE '%:own' OR p.permission_name LIKE '%:all') AND p.permission_name NOT LIKE 'user:%:all';

-- Create default admin user (username: admin, password: admin)
INSERT INTO profiler_schema.users (username, email, password_hash, password_salt, first_name, last_name, is_active)
VALUES (
    'admin',
    'admin@example.com',
    -- This is a placeholder. In production, use a proper password hashing mechanism
    '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
    'salt',
    'Admin',
    'User',
    TRUE
);

-- Assign admin role to admin user
INSERT INTO profiler_schema.user_roles (user_id, role_id)
SELECT u.user_id, r.role_id
FROM profiler_schema.users u
CROSS JOIN profiler_schema.roles r
WHERE u.username = 'admin' AND r.role_name = 'admin';

COMMENT ON DATABASE profiler IS 'Database for the Profiler application';
COMMENT ON SCHEMA profiler_schema IS 'Schema containing all Profiler application tables';

-- Grant privileges on all tables to the application role
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA profiler_schema TO profiler_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA profiler_schema TO profiler_app; 