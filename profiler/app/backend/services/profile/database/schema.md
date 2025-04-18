# Database Schema Design for Profiler Application

This document outlines the database schema for the Profiler application, focusing on profiles and documents.

## Schema Overview

The database consists of three primary schemas:
- `profile`: Stores user profile data and sections
- `document`: Stores documents uploaded by users
- `recommendation`: Stores recommendation data based on profiles

## Tables and Relationships

### Profile Schema

#### 1. `profiles` table
| Column Name    | Data Type     | Constraints     | Description                           |
|----------------|---------------|-----------------|---------------------------------------|
| profile_id     | VARCHAR(36)   | PRIMARY KEY     | Unique identifier for the profile     |
| user_id        | VARCHAR(36)   | NOT NULL, INDEX | ID of the user who owns the profile   |
| current_section| VARCHAR(50)   | NOT NULL        | Currently active section              |
| metadata       | TEXT          | NULL            | JSON-serialized profile metadata      |
| config         | TEXT          | NOT NULL        | JSON-serialized profile configuration |
| created_at     | TIMESTAMP     | NOT NULL        | Profile creation timestamp            |
| last_updated   | TIMESTAMP     | NOT NULL        | Last update timestamp                 |
| status         | VARCHAR(20)   | NOT NULL, INDEX | Profile status (active, archived, etc.)|

**Indexes:**
- `idx_profiles_user_id`: For querying profiles by user
- `idx_profiles_status`: For filtering by status

#### 2. `profile_sections` table
| Column Name    | Data Type     | Constraints     | Description                           |
|----------------|---------------|-----------------|---------------------------------------|
| id             | VARCHAR(36)   | PRIMARY KEY     | Unique identifier for the section record |
| profile_id     | VARCHAR(36)   | FOREIGN KEY, INDEX | Reference to profiles.profile_id  |
| section_id     | VARCHAR(50)   | NOT NULL, INDEX | Section identifier (e.g., "personal") |
| title          | VARCHAR(100)  | NOT NULL        | Human-readable section title          |
| data           | TEXT          | NULL            | JSON-serialized section data          |
| metadata       | TEXT          | NULL            | JSON-serialized section metadata      |
| completed      | BOOLEAN       | NOT NULL, INDEX | Whether section is completed          |
| last_updated   | TIMESTAMP     | NOT NULL        | Last update timestamp                 |

**Indexes:**
- `idx_profile_sections_profile_id`: For querying sections by profile
- `idx_profile_sections_section_id`: For querying specific section types
- `idx_profile_sections_completed`: For filtering by completion status

**Foreign Keys:**
- `profile_id` references `profiles(profile_id)` ON DELETE CASCADE

### Document Schema

#### 1. `documents` table
| Column Name     | Data Type     | Constraints     | Description                           |
|-----------------|---------------|-----------------|---------------------------------------|
| document_id     | VARCHAR(36)   | PRIMARY KEY     | Unique identifier for the document    |
| profile_id      | VARCHAR(36)   | FOREIGN KEY, INDEX | Reference to profiles.profile_id   |
| user_id         | VARCHAR(36)   | NOT NULL, INDEX | ID of the user who uploaded the document |
| filename        | VARCHAR(255)  | NOT NULL        | Original filename                     |
| file_path       | VARCHAR(512)  | NOT NULL        | Path to the stored file               |
| file_size       | INTEGER       | NOT NULL        | Size of the file in bytes             |
| mime_type       | VARCHAR(100)  | NOT NULL        | MIME type of the document             |
| metadata        | TEXT          | NULL            | JSON-serialized document metadata     |
| status          | VARCHAR(20)   | NOT NULL, INDEX | Document status (active, processing, etc.) |
| created_at      | TIMESTAMP     | NOT NULL        | Document upload timestamp             |
| last_updated    | TIMESTAMP     | NOT NULL        | Last update timestamp                 |
| section_id      | VARCHAR(50)   | NULL, INDEX     | Associated profile section            |

**Indexes:**
- `idx_documents_profile_id`: For querying documents by profile
- `idx_documents_user_id`: For querying documents by user
- `idx_documents_status`: For filtering by status
- `idx_documents_section_id`: For querying documents by section

**Foreign Keys:**
- `profile_id` references `profiles(profile_id)` ON DELETE CASCADE

#### 2. `document_versions` table
| Column Name     | Data Type     | Constraints     | Description                           |
|-----------------|---------------|-----------------|---------------------------------------|
| version_id      | VARCHAR(36)   | PRIMARY KEY     | Unique identifier for the version     |
| document_id     | VARCHAR(36)   | FOREIGN KEY, INDEX | Reference to documents.document_id |
| version_number  | INTEGER       | NOT NULL        | Sequential version number             |
| file_path       | VARCHAR(512)  | NOT NULL        | Path to the versioned file            |
| file_size       | INTEGER       | NOT NULL        | Size of the file in bytes             |
| created_at      | TIMESTAMP     | NOT NULL        | Version creation timestamp            |
| created_by      | VARCHAR(36)   | NOT NULL        | User who created this version         |
| change_summary  | TEXT          | NULL            | Summary of changes in this version    |

**Indexes:**
- `idx_document_versions_document_id`: For querying versions by document

**Foreign Keys:**
- `document_id` references `documents(document_id)` ON DELETE CASCADE

#### 3. `document_analysis` table
| Column Name     | Data Type     | Constraints     | Description                           |
|-----------------|---------------|-----------------|---------------------------------------|
| analysis_id     | VARCHAR(36)   | PRIMARY KEY     | Unique identifier for the analysis    |
| document_id     | VARCHAR(36)   | FOREIGN KEY, INDEX | Reference to documents.document_id |
| content_text    | TEXT          | NULL            | Extracted text content                |
| metadata        | TEXT          | NULL            | JSON-serialized analysis metadata     |
| created_at      | TIMESTAMP     | NOT NULL        | Analysis timestamp                    |
| status          | VARCHAR(20)   | NOT NULL        | Analysis status (complete, error, etc.) |

**Indexes:**
- `idx_document_analysis_document_id`: For querying analysis by document

**Foreign Keys:**
- `document_id` references `documents(document_id)` ON DELETE CASCADE

### Recommendation Schema

#### 1. `recommendations` table
| Column Name         | Data Type     | Constraints     | Description                          |
|---------------------|---------------|-----------------|--------------------------------------|
| recommendation_id   | VARCHAR(36)   | PRIMARY KEY     | Unique identifier for recommendation |
| profile_id          | VARCHAR(36)   | FOREIGN KEY, INDEX | Reference to profiles.profile_id |
| section_id          | VARCHAR(50)   | NULL, INDEX     | Associated profile section           |
| title               | VARCHAR(255)  | NOT NULL        | Recommendation title                 |
| description         | TEXT          | NOT NULL        | Detailed recommendation description  |
| action_steps        | TEXT          | NULL            | JSON-serialized action steps         |
| priority            | SMALLINT      | NOT NULL        | Priority level (1-5)                 |
| metadata            | TEXT          | NULL            | JSON-serialized metadata             |
| created_at          | TIMESTAMP     | NOT NULL        | Creation timestamp                   |
| status              | VARCHAR(20)   | NOT NULL, INDEX | Status (active, completed, etc.)     |

**Indexes:**
- `idx_recommendations_profile_id`: For querying recommendations by profile
- `idx_recommendations_section_id`: For querying recommendations by section
- `idx_recommendations_status`: For filtering by status

**Foreign Keys:**
- `profile_id` references `profiles(profile_id)` ON DELETE CASCADE

## Data Relationships

### One-to-Many Relationships:
- A user can have multiple profiles
- A profile can have multiple sections
- A profile can have multiple documents
- A document can have multiple versions
- A document can have one analysis record
- A profile can have multiple recommendations

### Many-to-Many Relationships:
- Documents can be associated with multiple sections through the section_id field

## Schema Migrations

Database migrations will be handled through SQLAlchemy's Alembic integration, with migration scripts stored in the `migrations` directory. This will allow for:

1. Version-controlled schema changes
2. Automated upgrades and downgrades
3. Data transformations during schema changes
4. Safe multi-environment deployments

## Security Considerations

1. Sensitive data will be stored in encrypted format when applicable
2. User IDs are indexed but not exposed in public-facing queries
3. File paths are stored in the database but access is mediated through the application
4. All schema access is controlled via database roles and permissions

## Performance Considerations

1. Appropriate indexing on frequently queried columns
2. JSON data stored in TEXT fields with indexable extracted columns as needed
3. Connection pooling configured for optimal performance
4. Foreign key constraints with cascade deletes to maintain referential integrity 