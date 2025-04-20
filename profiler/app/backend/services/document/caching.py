"""
Document caching service.

This module provides functionality for caching document content and metadata to improve
retrieval performance.
"""

import os
import time
import asyncio
from typing import Dict, List, Any, Optional, BinaryIO, Tuple, Union, Set
from datetime import datetime, timedelta
import hashlib
import json
import pickle
import base64
import tempfile
from functools import lru_cache

from app.backend.utils.logging import get_logger
from app.backend.utils.errors import StorageError, CacheError
from .models import Document

logger = get_logger(__name__)


class CacheEntry:
    """Represents a cached document item."""
    
    def __init__(self, 
                key: str, 
                value: Any, 
                expires_at: Optional[datetime] = None,
                metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a cache entry.
        
        Args:
            key: Cache key
            value: Cached value
            expires_at: When the entry expires
            metadata: Additional metadata
        """
        self.key = key
        self.value = value
        self.expires_at = expires_at
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.last_accessed_at = self.created_at
        self.access_count = 0
    
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        return self.expires_at is not None and datetime.utcnow() > self.expires_at
    
    def access(self) -> None:
        """Record an access to this cache entry."""
        self.last_accessed_at = datetime.utcnow()
        self.access_count += 1


class InMemoryCache:
    """Simple in-memory cache implementation."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize an in-memory cache.
        
        Args:
            max_size: Maximum number of items in the cache
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        entry = self.cache.get(key)
        if entry is None:
            return None
        
        if entry.is_expired():
            del self.cache[key]
            return None
        
        entry.access()
        return entry.value
    
    async def set(self, 
               key: str, 
               value: Any, 
               ttl_seconds: Optional[int] = None, 
               metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds
            metadata: Additional metadata
        """
        # Check if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_entries()
        
        # Calculate expiration time
        expires_at = None
        if ttl_seconds is not None:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        # Create cache entry
        entry = CacheEntry(key=key, value=value, expires_at=expires_at, metadata=metadata)
        
        # Add to cache
        self.cache[key] = entry
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key was found and deleted, False otherwise
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    async def clear(self) -> None:
        """Clear all entries from the cache."""
        self.cache.clear()
    
    def _evict_entries(self) -> None:
        """Evict entries to make room in the cache."""
        # First, remove expired entries
        now = datetime.utcnow()
        expired_keys = [k for k, v in self.cache.items() if v.expires_at and v.expires_at < now]
        for key in expired_keys:
            del self.cache[key]
        
        # If still too many entries, remove least recently used
        if len(self.cache) >= self.max_size:
            # Sort by last accessed time
            sorted_entries = sorted(
                self.cache.items(),
                key=lambda x: x[1].last_accessed_at
            )
            
            # Remove 10% of entries or at least one
            to_remove = max(1, len(self.cache) // 10)
            for i in range(to_remove):
                if i < len(sorted_entries):
                    del self.cache[sorted_entries[i][0]]


class FileCache:
    """File-based cache implementation for larger documents."""
    
    def __init__(self, cache_dir: Optional[str] = None, max_size_mb: int = 1000):
        """
        Initialize a file-based cache.
        
        Args:
            cache_dir: Directory to store cached files
            max_size_mb: Maximum size of the cache in MB
        """
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "document_cache")
        self.max_size_mb = max_size_mb
        self.metadata_dir = os.path.join(self.cache_dir, "metadata")
        self.data_dir = os.path.join(self.cache_dir, "data")
        
        # Create cache directories
        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _get_path_for_key(self, key: str, is_metadata: bool = False) -> str:
        """Get file path for a cache key."""
        # Use hash of key as filename to avoid invalid characters
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        
        if is_metadata:
            return os.path.join(self.metadata_dir, f"{hashed_key}.json")
        else:
            return os.path.join(self.data_dir, f"{hashed_key}.data")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        metadata_path = self._get_path_for_key(key, is_metadata=True)
        data_path = self._get_path_for_key(key, is_metadata=False)
        
        # Check if files exist
        if not os.path.exists(metadata_path) or not os.path.exists(data_path):
            return None
        
        try:
            # Read metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Check if expired
            if metadata.get('expires_at'):
                expires_at = datetime.fromisoformat(metadata['expires_at'])
                if datetime.utcnow() > expires_at:
                    # Remove expired files
                    os.remove(metadata_path)
                    os.remove(data_path)
                    return None
            
            # Read data
            with open(data_path, 'rb') as f:
                data = pickle.load(f)
            
            # Update access info
            metadata['last_accessed_at'] = datetime.utcnow().isoformat()
            metadata['access_count'] = metadata.get('access_count', 0) + 1
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to read from cache for key {key}: {str(e)}")
            return None
    
    async def set(self, 
               key: str, 
               value: Any, 
               ttl_seconds: Optional[int] = None, 
               metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds
            metadata: Additional metadata
        """
        # Check if cache is full
        await self._check_size()
        
        metadata_path = self._get_path_for_key(key, is_metadata=True)
        data_path = self._get_path_for_key(key, is_metadata=False)
        
        try:
            # Calculate expiration time
            expires_at = None
            if ttl_seconds is not None:
                expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()
            
            # Prepare metadata
            entry_metadata = {
                'key': key,
                'created_at': datetime.utcnow().isoformat(),
                'last_accessed_at': datetime.utcnow().isoformat(),
                'access_count': 0,
                'expires_at': expires_at,
                'custom_metadata': metadata or {}
            }
            
            # Write metadata
            with open(metadata_path, 'w') as f:
                json.dump(entry_metadata, f)
            
            # Write data
            with open(data_path, 'wb') as f:
                pickle.dump(value, f)
                
        except Exception as e:
            logger.error(f"Failed to write to cache for key {key}: {str(e)}")
            # Clean up any partial writes
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            if os.path.exists(data_path):
                os.remove(data_path)
    
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if the key was found and deleted, False otherwise
        """
        metadata_path = self._get_path_for_key(key, is_metadata=True)
        data_path = self._get_path_for_key(key, is_metadata=False)
        
        found = False
        
        # Remove files
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
            found = True
        
        if os.path.exists(data_path):
            os.remove(data_path)
            found = True
        
        return found
    
    async def clear(self) -> None:
        """Clear all entries from the cache."""
        # Remove all files in cache directories
        for filename in os.listdir(self.metadata_dir):
            os.remove(os.path.join(self.metadata_dir, filename))
        
        for filename in os.listdir(self.data_dir):
            os.remove(os.path.join(self.data_dir, filename))
    
    async def _check_size(self) -> None:
        """Check if cache is full and evict entries if needed."""
        # Get total size of data directory
        total_size = 0
        for filename in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, filename)
            total_size += os.path.getsize(file_path)
        
        # Convert to MB
        total_size_mb = total_size / (1024 * 1024)
        
        # If over limit, evict entries
        if total_size_mb > self.max_size_mb:
            await self._evict_entries(target_mb=self.max_size_mb * 0.8)  # Aim for 80%
    
    async def _evict_entries(self, target_mb: float) -> None:
        """
        Evict entries to reduce cache size.
        
        Args:
            target_mb: Target size in MB
        """
        # Collect metadata for all entries
        entries = []
        for filename in os.listdir(self.metadata_dir):
            metadata_path = os.path.join(self.metadata_dir, filename)
            
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Extract key and check if data file exists
                key = metadata.get('key')
                if not key:
                    continue
                
                data_path = self._get_path_for_key(key, is_metadata=False)
                if not os.path.exists(data_path):
                    continue
                
                # Add file size
                metadata['file_size'] = os.path.getsize(data_path)
                entries.append(metadata)
                
            except Exception:
                # Skip problematic entries
                continue
        
        # Sort by last access time, oldest first
        entries.sort(key=lambda x: x.get('last_accessed_at', ''))
        
        # Calculate target size in bytes
        target_bytes = target_mb * 1024 * 1024
        
        # Delete oldest entries until under target
        current_size = sum(entry.get('file_size', 0) for entry in entries)
        deleted_count = 0
        
        for entry in entries:
            if current_size <= target_bytes:
                break
                
            key = entry.get('key')
            if key:
                file_size = entry.get('file_size', 0)
                await self.delete(key)
                current_size -= file_size
                deleted_count += 1
        
        logger.info(f"Evicted {deleted_count} entries from file cache")


class DocumentCachingService:
    """Service for caching document content and metadata."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the document caching service.
        
        Args:
            config: Optional configuration for the service
        """
        self.config = config or {}
        
        # Create in-memory cache for metadata
        metadata_cache_size = self.config.get("metadata_cache_size", 10000)
        self.metadata_cache = InMemoryCache(max_size=metadata_cache_size)
        
        # Create file cache for document content
        cache_dir = self.config.get("cache_dir")
        max_cache_size_mb = self.config.get("max_cache_size_mb", 2000)  # 2GB default
        self.content_cache = FileCache(cache_dir=cache_dir, max_size_mb=max_cache_size_mb)
        
        # TTL settings
        self.metadata_ttl = self.config.get("metadata_ttl", 3600)  # 1 hour default
        self.content_ttl = self.config.get("content_ttl", 86400)  # 24 hours default
    
    async def initialize(self) -> None:
        """Initialize the document caching service."""
        logger.info("Initialized document caching service")
    
    async def shutdown(self) -> None:
        """Shutdown the document caching service."""
        await self.metadata_cache.clear()
        await self.content_cache.clear()
        logger.info("Shutdown document caching service")
    
    async def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached document metadata.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Cached metadata or None if not found
        """
        cache_key = f"metadata:{document_id}"
        return await self.metadata_cache.get(cache_key)
    
    async def cache_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> None:
        """
        Cache document metadata.
        
        Args:
            document_id: ID of the document
            metadata: Document metadata to cache
        """
        cache_key = f"metadata:{document_id}"
        await self.metadata_cache.set(
            key=cache_key,
            value=metadata,
            ttl_seconds=self.metadata_ttl
        )
    
    async def get_document_content(self, document_id: str) -> Optional[BinaryIO]:
        """
        Get cached document content.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Cached document content or None if not found
        """
        cache_key = f"content:{document_id}"
        return await self.content_cache.get(cache_key)
    
    async def cache_document_content(self, 
                                  document_id: str, 
                                  content: BinaryIO, 
                                  metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Cache document content.
        
        Args:
            document_id: ID of the document
            content: Document content to cache
            metadata: Additional metadata
        """
        cache_key = f"content:{document_id}"
        
        # Get current position to restore later
        pos = content.tell()
        
        try:
            # Read all content
            content.seek(0)
            content_bytes = content.read()
            
            # Cache content
            await self.content_cache.set(
                key=cache_key,
                value=content_bytes,
                ttl_seconds=self.content_ttl,
                metadata=metadata
            )
            
        finally:
            # Restore original position
            content.seek(pos)
    
    async def invalidate_document(self, document_id: str) -> None:
        """
        Invalidate cached document metadata and content.
        
        Args:
            document_id: ID of the document
        """
        metadata_key = f"metadata:{document_id}"
        content_key = f"content:{document_id}"
        
        await self.metadata_cache.delete(metadata_key)
        await self.content_cache.delete(content_key)
    
    @staticmethod
    def generate_cache_key(document_id: str, version_id: Optional[str] = None) -> str:
        """
        Generate a cache key for a document.
        
        Args:
            document_id: ID of the document
            version_id: Optional version ID
            
        Returns:
            Cache key
        """
        if version_id:
            return f"{document_id}:{version_id}"
        return document_id 