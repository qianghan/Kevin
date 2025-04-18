"""
Transaction management for document operations.

This module provides utilities for managing database transactions for document operations.
"""

import asyncio
import contextlib
from typing import AsyncGenerator, Optional, Callable, TypeVar, Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.backend.utils.logging import get_logger
from app.backend.utils.errors import StorageError, ConcurrencyError
from .database.connection import DatabaseManager

logger = get_logger(__name__)

# Define generic type for function return values
T = TypeVar('T')


class DocumentTransactionManager:
    """Manages database transactions for document operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the transaction manager.
        
        Args:
            db_manager: Database manager for document operations
        """
        self.db_manager = db_manager
        self._locks: Dict[str, asyncio.Lock] = {}
    
    @contextlib.asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Create a transaction context manager.
        
        Yields:
            SQLAlchemy session with transaction
            
        Raises:
            StorageError: If the transaction fails
        """
        session = await self.db_manager.get_session()
        try:
            async with session.begin():
                yield session
        except Exception as e:
            logger.error(f"Transaction failed: {str(e)}")
            raise StorageError(f"Transaction failed: {str(e)}")
        finally:
            await session.close()
    
    async def run_in_transaction(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Run a function within a transaction.
        
        Args:
            func: Function to run
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function
            
        Raises:
            StorageError: If the transaction fails
        """
        async with self.transaction() as session:
            # Add session to kwargs if not provided
            if 'session' not in kwargs:
                kwargs['session'] = session
                
            return await func(*args, **kwargs)
    
    @contextlib.asynccontextmanager
    async def document_lock(self, document_id: str) -> AsyncGenerator[None, None]:
        """
        Create a lock for a document to prevent concurrent modifications.
        
        Args:
            document_id: ID of the document to lock
            
        Yields:
            None
            
        Raises:
            ConcurrencyError: If the lock cannot be acquired
        """
        # Get or create lock for this document
        if document_id not in self._locks:
            self._locks[document_id] = asyncio.Lock()
            
        lock = self._locks[document_id]
        
        # Try to acquire the lock with timeout
        try:
            acquired = await asyncio.wait_for(lock.acquire(), timeout=5.0)
            if not acquired:
                raise ConcurrencyError(f"Failed to acquire lock for document {document_id}")
                
            logger.debug(f"Acquired lock for document {document_id}")
            yield
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout acquiring lock for document {document_id}")
            raise ConcurrencyError(f"Timeout acquiring lock for document {document_id}")
            
        finally:
            if lock.locked():
                lock.release()
                logger.debug(f"Released lock for document {document_id}")
                
            # Clean up if no active locks
            if document_id in self._locks and not self._locks[document_id].locked():
                # Keep the lock object for potential reuse to avoid creating too many objects
                pass
    
    async def run_with_document_lock(self, document_id: str, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Run a function with a document lock to prevent concurrent modifications.
        
        Args:
            document_id: ID of the document to lock
            func: Function to run
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function
            
        Raises:
            ConcurrencyError: If the lock cannot be acquired
            StorageError: If the function fails
        """
        async with self.document_lock(document_id):
            return await func(*args, **kwargs)
    
    @contextlib.asynccontextmanager
    async def locked_transaction(self, document_id: str) -> AsyncGenerator[AsyncSession, None]:
        """
        Create a transaction with a document lock.
        
        Args:
            document_id: ID of the document to lock
            
        Yields:
            SQLAlchemy session with transaction
            
        Raises:
            ConcurrencyError: If the lock cannot be acquired
            StorageError: If the transaction fails
        """
        async with self.document_lock(document_id):
            async with self.transaction() as session:
                yield session
    
    async def run_in_batch(self, 
                         batch_func: Callable[[AsyncSession, List[Any]], T], 
                         items: List[Any], 
                         batch_size: int = 100) -> List[T]:
        """
        Run a function in batches within a transaction.
        
        Args:
            batch_func: Function to run with each batch
            items: List of items to process
            batch_size: Number of items per batch
            
        Returns:
            List of results from each batch
            
        Raises:
            StorageError: If any batch fails
        """
        results = []
        
        # Process items in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            
            try:
                async with self.transaction() as session:
                    result = await batch_func(session, batch)
                    results.append(result)
                    
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(items)-1)//batch_size + 1} with {len(batch)} items")
                
            except Exception as e:
                logger.error(f"Batch processing failed at batch {i//batch_size + 1}: {str(e)}")
                raise StorageError(f"Batch processing failed: {str(e)}")
        
        return results 