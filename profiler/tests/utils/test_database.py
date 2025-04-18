import asyncio
import asyncpg
import os
import pytest
from typing import Dict, Any, List

async def setup_test_database(config: Dict[str, Any]) -> None:
    """
    Set up the test database with a clean state.
    
    This function:
    1. Connects to PostgreSQL using the provided config
    2. Creates tables needed for tests
    3. Sets up any required initial data
    
    Args:
        config: Database configuration dictionary
    """
    # Create a connection
    conn = await asyncpg.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )
    
    try:
        # Make sure we're starting with a clean state
        await conn.execute('BEGIN')
        
        # Create schema if it doesn't exist
        await conn.execute('CREATE SCHEMA IF NOT EXISTS profiler_schema')
        
        # Create tables for testing
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS profiler_schema.users (
            user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS profiler_schema.sessions (
            session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES profiler_schema.users(user_id) ON DELETE CASCADE,
            token VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            session_data JSONB,
            CONSTRAINT fk_user
                FOREIGN KEY(user_id)
                REFERENCES profiler_schema.users(user_id)
                ON DELETE CASCADE
        )
        ''')
        
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS profiler_schema.profiles (
            profile_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            current_section VARCHAR(50),
            status VARCHAR(20) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB,
            CONSTRAINT fk_user
                FOREIGN KEY(user_id)
                REFERENCES profiler_schema.users(user_id)
                ON DELETE CASCADE
        )
        ''')
        
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS profiler_schema.answers (
            answer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            profile_id UUID NOT NULL,
            section_key VARCHAR(50) NOT NULL,
            question_key VARCHAR(50) NOT NULL,
            answer_text TEXT,
            answer_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_profile
                FOREIGN KEY(profile_id)
                REFERENCES profiler_schema.profiles(profile_id)
                ON DELETE CASCADE,
            CONSTRAINT unique_answer
                UNIQUE(profile_id, section_key, question_key)
        )
        ''')
        
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS profiler_schema.documents (
            document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            profile_id UUID NOT NULL,
            filename VARCHAR(255) NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            file_size INTEGER NOT NULL,
            status VARCHAR(20) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB,
            file_content BYTEA NOT NULL,
            CONSTRAINT fk_user
                FOREIGN KEY(user_id)
                REFERENCES profiler_schema.users(user_id)
                ON DELETE CASCADE,
            CONSTRAINT fk_profile
                FOREIGN KEY(profile_id)
                REFERENCES profiler_schema.profiles(profile_id)
                ON DELETE CASCADE
        )
        ''')
        
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS profiler_schema.document_chunks (
            chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL,
            chunk_index INTEGER NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding FLOAT4[] NULL,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_document
                FOREIGN KEY(document_id)
                REFERENCES profiler_schema.documents(document_id)
                ON DELETE CASCADE,
            CONSTRAINT unique_chunk
                UNIQUE(document_id, chunk_index)
        )
        ''')
        
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS profiler_schema.migrations (
            id SERIAL PRIMARY KEY,
            version VARCHAR(50) NOT NULL,
            description TEXT,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        await conn.execute('COMMIT')
    except Exception as e:
        await conn.execute('ROLLBACK')
        raise e
    finally:
        await conn.close()


async def teardown_test_database(config: Dict[str, Any]) -> None:
    """
    Tear down the test database, removing all test data.
    
    Args:
        config: Database configuration dictionary
    """
    # Create a connection
    conn = await asyncpg.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )
    
    try:
        # Clean up all test data
        await conn.execute('BEGIN')
        
        # Drop tables in correct order to respect foreign key constraints
        await conn.execute('DROP TABLE IF EXISTS profiler_schema.document_chunks')
        await conn.execute('DROP TABLE IF EXISTS profiler_schema.documents')
        await conn.execute('DROP TABLE IF EXISTS profiler_schema.answers')
        await conn.execute('DROP TABLE IF EXISTS profiler_schema.profiles')
        await conn.execute('DROP TABLE IF EXISTS profiler_schema.sessions')
        await conn.execute('DROP TABLE IF EXISTS profiler_schema.users')
        await conn.execute('DROP TABLE IF EXISTS profiler_schema.migrations')
        
        await conn.execute('COMMIT')
    except Exception as e:
        await conn.execute('ROLLBACK')
        raise e
    finally:
        await conn.close()


async def reset_test_tables(config: Dict[str, Any]) -> None:
    """
    Reset all tables in the test database, keeping the schema.
    Useful for running multiple tests without dropping the tables.
    
    Args:
        config: Database configuration dictionary
    """
    # Create a connection
    conn = await asyncpg.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )
    
    try:
        # Clear all test data but keep the tables
        await conn.execute('BEGIN')
        
        # Truncate tables in correct order to respect foreign key constraints
        await conn.execute('TRUNCATE TABLE profiler_schema.document_chunks CASCADE')
        await conn.execute('TRUNCATE TABLE profiler_schema.documents CASCADE')
        await conn.execute('TRUNCATE TABLE profiler_schema.answers CASCADE')
        await conn.execute('TRUNCATE TABLE profiler_schema.profiles CASCADE')
        await conn.execute('TRUNCATE TABLE profiler_schema.sessions CASCADE')
        await conn.execute('TRUNCATE TABLE profiler_schema.users CASCADE')
        await conn.execute('TRUNCATE TABLE profiler_schema.migrations CASCADE')
        
        await conn.execute('COMMIT')
    except Exception as e:
        await conn.execute('ROLLBACK')
        raise e
    finally:
        await conn.close()


async def execute_test_query(config: Dict[str, Any], query: str, *args) -> List[Dict[str, Any]]:
    """
    Execute a query on the test database and return results.
    
    Args:
        config: Database configuration dictionary
        query: SQL query to execute
        args: Query parameters
        
    Returns:
        List of records as dictionaries
    """
    # Create a connection
    conn = await asyncpg.connect(
        host=config['host'],
        port=config['port'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )
    
    try:
        # Execute query and return results
        records = await conn.fetch(query, *args)
        return [dict(r) for r in records]
    finally:
        await conn.close() 