# Understanding Persistent Storage Implementation

This document outlines the persistent storage architecture implemented for the Profiler application.

## Architecture Overview

The persistent storage system is built using PostgreSQL with SQLAlchemy as the ORM layer. The implementation follows 
the repository pattern to separate data access from business logic.

### Key Components

1. **Database Models**
   - Defined using SQLAlchemy ORM
   - Include Profile, Document, User, and related models
   - Implement relationships between entities

2. **Repository Interfaces**
   - Define contracts for data access
   - Allow for swappable implementations
   - Support dependency injection

3. **PostgreSQL Repositories**
   - Implement repository interfaces
   - Handle CRUD operations
   - Manage transactions and error handling

4. **Connection Management**
   - Pooled connections for efficiency
   - Transactional support
   - Error recovery mechanisms

## Database Structure

The PostgreSQL database includes a dedicated schema (`profiler_schema`) with the following tables:

### User Management
- `users`: Core user account information
- `roles`: User role definitions
- `permissions`: Granular permissions
- `user_roles`: Many-to-many mapping between users and roles
- `role_permissions`: Many-to-many mapping between roles and permissions

### Profile Management
- `profiles`: User profile data
- `sections`: Profile section information
- `answers`: User responses to profile questions

### Document Management
- `documents`: Document metadata and storage information
- `document_chunks`: Processed document segments for analysis

### Recommendations
- `recommendations`: AI-generated recommendations for profiles

### Session Management
- `sessions`: User authentication sessions

All tables use UUID primary keys with auto-generation and include appropriate indexes for optimal query performance.

## Testing Infrastructure

The testing infrastructure for persistent storage includes:

1. **BDD Tests**
   - Feature files defining behavior scenarios
   - Step implementations for each scenario
   - Testing of CRUD operations on profiles, authentication, etc.

2. **Test Environment**
   - Docker-based PostgreSQL container for integration tests
   - Separate test database for isolation
   - Automated setup and teardown via `run_bdd_tests.sh`

3. **Documentation Generation**
   - Automated creation of documentation for authentication flows
   - Documentation of persistent storage architecture

## Authentication System

The authentication system implemented includes:

1. **JWT-Based Authentication**
   - Token generation on successful login
   - Token validation on protected requests
   - Token refresh mechanisms

2. **Role-Based Access Control**
   - Users assigned to roles (admin, user, manager)
   - Resources protected by permission checks
   - Granular permission system

3. **Session Management**
   - Session creation and retrieval
   - Session invalidation
   - Security measures to prevent session hijacking

## Repository Pattern Implementation

The repository pattern is implemented with:

1. **Interface Definition**
   - `ProfileRepositoryInterface` defines the contract
   - Methods for CRUD operations on profiles
   - Consistent error handling

2. **Multiple Implementations**
   - `PostgreSQLProfileRepository` for production
   - `JSONFileProfileRepository` for development/testing
   - `MockProfileRepository` for unit tests

3. **Database Connection**
   - Connection pooling for performance
   - Transactional operations
   - Proper resource cleanup

## SOLID Architecture

The implementation adheres to SOLID principles:

1. **Single Responsibility Principle**
   - Each repository handles one entity type
   - Separation of connection management from data access

2. **Open/Closed Principle**
   - Repository interfaces allow for extension without modification
   - New repository types can be added without changing client code

3. **Liskov Substitution Principle**
   - Different repository implementations can be substituted
   - Tests work with mock implementations

4. **Interface Segregation Principle**
   - Specific interfaces for different repository types
   - Client code only depends on methods it needs

5. **Dependency Inversion Principle**
   - Services depend on repository interfaces, not implementations
   - Simplified testing and maintenance

## Backup and Restore

The system includes functionality for:

1. **Database Backups**
   - Scheduled and on-demand backups
   - Consistent backup format

2. **Restore Operations**
   - Restoration from backup files
   - Validation of backup integrity

## Security Considerations

Security measures implemented include:

1. **Data Protection**
   - Parameterized queries to prevent SQL injection
   - Password hashing with salt
   - Secure handling of connection strings

2. **Access Control**
   - Repository-level access control
   - Data ownership enforcement
   - Validation before storage

## Performance Optimization

Performance considerations include:

1. **Connection Pooling**
   - Efficient database connection reuse
   - Connection limits and timeouts

2. **Query Optimization**
   - Appropriate indexes on frequently queried fields
   - Optimized join queries

3. **Data Access Patterns**
   - Batch operations for bulk processing
   - Lazy loading of related entities 