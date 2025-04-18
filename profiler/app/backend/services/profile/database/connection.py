"""
Database connection manager for PostgreSQL using SQLAlchemy.

This module provides functions to create and manage database connections.
"""

import os
import logging
from typing import Optional, Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session

from app.backend.utils.logging import get_logger
from app.backend.utils.config_manager import ConfigManager
from .models import Base

logger = get_logger(__name__)


class DatabaseManager:
    """Database connection manager for PostgreSQL."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the database manager.
        
        Args:
            config: Optional configuration dictionary. If not provided,
                   configuration will be loaded from the config manager.
        """
        self._config = config or ConfigManager().get_value(["database"], {})
        self._engine: Optional[AsyncEngine] = None
        self._session_factory = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize the database connection.
        
        Raises:
            Exception: If the database connection cannot be established.
        """
        if self._initialized:
            logger.info("Database already initialized, skipping")
            return
            
        try:
            logger.info("Initializing database connection")
            
            # Get configuration - check environment variables first, then config
            db_url = os.environ.get("PROFILER_DATABASE__URL")
            if not db_url:
                db_url = self._config.get("url", "postgresql+asyncpg://postgres:postgres@localhost:5432/profiler")
            
            # Get additional connection parameters
            echo = self._config.get("echo", False)
            pool_size = int(os.environ.get("PROFILER_DATABASE__POOL_SIZE", self._config.get("pool_size", 5)))
            max_overflow = int(os.environ.get("PROFILER_DATABASE__MAX_OVERFLOW", self._config.get("max_overflow", 10)))
            connect_timeout = int(os.environ.get("PROFILER_DATABASE__CONNECT_TIMEOUT", self._config.get("connect_timeout", 10)))
            
            logger.info(f"Connecting to database: {self._sanitize_url(db_url)}")
            
            # Create engine with proper parameters
            self._engine = create_async_engine(
                db_url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,  # Check connection validity before using it
                pool_recycle=3600,  # Recycle connections after 1 hour
                connect_args={"timeout": connect_timeout}
            )
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                class_=AsyncSession
            )
            
            # Create tables
            async with self._engine.begin() as conn:
                # Create all tables that don't exist yet
                await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info("Database connection initialized successfully")
        except Exception as e:
            logger.exception(f"Failed to initialize database: {str(e)}")
            raise
    
    def _sanitize_url(self, url: str) -> str:
        """Sanitize a database URL for logging (remove password)."""
        if '://' not in url:
            return url
        
        try:
            # Split URL into components
            protocol_part, rest = url.split('://', 1)
            
            # Check if auth info is present
            if '@' in rest:
                auth_part, host_part = rest.split('@', 1)
                
                # Replace password with asterisks
                if ':' in auth_part:
                    username, password = auth_part.split(':', 1)
                    auth_part = f"{username}:****"
                
                sanitized = f"{protocol_part}://{auth_part}@{host_part}"
            else:
                sanitized = url
                
            return sanitized
        except Exception:
            # If anything goes wrong, just return a generic description
            return f"{protocol_part}://*****"
    
    async def shutdown(self) -> None:
        """
        Shutdown the database connection and release resources.
        """
        if self._engine:
            logger.info("Shutting down database connection")
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._initialized = False
    
    async def get_session(self) -> AsyncSession:
        """
        Get a database session.
        
        Returns:
            AsyncSession: A new database session.
        
        Raises:
            Exception: If the database is not initialized.
        """
        if not self._initialized:
            await self.initialize()
        
        return self._session_factory()
    
    @property
    def engine(self) -> Optional[AsyncEngine]:
        """Get the database engine."""
        return self._engine
    
    @property
    def is_initialized(self) -> bool:
        """Check if the database is initialized."""
        return self._initialized 