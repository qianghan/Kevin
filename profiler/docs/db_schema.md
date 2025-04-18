# Database Schema Design

This document outlines the PostgreSQL database schema design for the Profiler application, focusing on profiles, documents, and related entities.

## Schema Overview

The database is organized in the `profiler_schema` schema with the following main tables:

1. `users` - User accounts and authentication information
2. `roles` - User roles for authorization
3. `permissions` - Granular permissions for access control
4. `user_roles` - Many-to-many relationship between users and roles
5. `role_permissions` - Many-to-many relationship between roles and permissions
6. `profiles` - User profile data
7. `sections` - Profile sections
8. `answers` - User answers to profile questions
9. `documents` - Uploaded documents
10. `document_chunks` - Document chunks for vector search
11. `recommendations` - System recommendations
12. `sessions` - User sessions

## Table Definitions

### Users Table

```sql
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
```

### Roles Table

```sql
CREATE TABLE profiler_schema.roles (
    role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Permissions Table

```sql
CREATE TABLE profiler_schema.permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    permission_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### User Roles Table

```sql
CREATE TABLE profiler_schema.user_roles (
    user_id UUID REFERENCES profiler_schema.users(user_id) ON DELETE CASCADE,
    role_id UUID REFERENCES profiler_schema.roles(role_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);
```

### Role Permissions Table

```sql
CREATE TABLE profiler_schema.role_permissions (
    role_id UUID REFERENCES profiler_schema.roles(role_id) ON DELETE CASCADE,
    permission_id UUID REFERENCES profiler_schema.permissions(permission_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);
```

### Profiles Table

```sql
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
```

### Sections Table

```sql
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
```

### Answers Table

```sql
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
```

### Documents Table

```sql
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
```

### Document Chunks Table

```sql
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
```

### Recommendations Table

```sql
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
```

### Sessions Table

```sql
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
```

## Indexes

```sql
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
```

## Entity-Relationship Diagram

```
users 1--* user_roles *--1 roles 1--* role_permissions *--1 permissions
users 1--* profiles 1--* sections
profiles 1--* answers
users 1--* documents *--1 profiles 
documents 1--* document_chunks
profiles 1--* recommendations
users 1--* sessions *--? profiles
```

## Initialization Scripts

The database is initialized with the following default data:
1. Default roles: `admin`, `user`, `manager`
2. Default permissions for each role
3. Admin user with all permissions

## Data Ownership and Access Control

- Each profile is associated with a specific user
- Documents are associated with both users and (optionally) profiles
- Access control is implemented through the roles and permissions system
- The `own` scope in permissions limits users to accessing their own resources
- Administrators have access to all resources

## Backup Strategy

The database backup strategy includes:
1. Daily full backups
2. Point-in-time recovery through PostgreSQL WAL archiving
3. Backup verification process
4. Retention policy (30 days for daily backups, 1 year for monthly backups) 