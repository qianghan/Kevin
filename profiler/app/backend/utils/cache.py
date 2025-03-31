"""
Caching utilities for the Profiler application.

This module provides caching mechanisms to improve performance
by storing frequently accessed data in memory or external cache stores.
"""

import time
import functools
import asyncio
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, cast
import json
import hashlib

from .logging import get_logger

logger = get_logger(__name__)

# Type variables for generic function types
T = TypeVar('T')
R = TypeVar('R')

class SimpleCache:
    """
    Simple in-memory cache with TTL support.
    
    This cache stores items in memory with an optional time-to-live (TTL)
    after which items are considered expired.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize the cache with a maximum size.
        
        Args:
            max_size: Maximum number of items to store in the cache
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._max_size = max_size
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get an item from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value, or None if not found or expired
        """
        if key not in self._cache:
            return None
        
        value, expiry = self._cache[key]
        
        # Check if expired
        if expiry < time.time() and expiry != 0:
            self._cache.pop(key, None)
            return None
        
        return value
    
    def set(self, key: str, value: Any, ttl: int = 0) -> None:
        """
        Set an item in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds (0 for no expiry)
        """
        # Implement LRU eviction if cache is full
        if len(self._cache) >= self._max_size and key not in self._cache:
            # Remove oldest item
            oldest_key = next(iter(self._cache))
            self._cache.pop(oldest_key, None)
        
        # Calculate expiry time
        expiry = time.time() + ttl if ttl > 0 else 0
        
        # Store in cache
        self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> bool:
        """
        Delete an item from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if the item was deleted, False if not found
        """
        if key in self._cache:
            self._cache.pop(key)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all items from the cache."""
        self._cache.clear()
    
    def cleanup(self) -> int:
        """
        Remove all expired items from the cache.
        
        Returns:
            Number of items removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if expiry < current_time and expiry != 0
        ]
        
        for key in expired_keys:
            self._cache.pop(key, None)
        
        return len(expired_keys)

# Create a global cache instance
_cache = SimpleCache()

def cache(ttl: int = 300):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds (0 for no expiry)
        
    Returns:
        Decorated function with caching
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> R:
            # Generate a cache key from function name and arguments
            key_parts = [func.__module__, func.__name__]
            for arg in args:
                key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            
            key_string = ":".join(key_parts)
            cache_key = hashlib.md5(key_string.encode()).hexdigest()
            
            # Check cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Call function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator

def cache_async(ttl: int = 300):
    """
    Decorator for caching async function results.
    
    Args:
        ttl: Time-to-live in seconds (0 for no expiry)
        
    Returns:
        Decorated async function with caching
    """
    def decorator(func: Callable[..., asyncio.Future]) -> Callable[..., asyncio.Future]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Generate a cache key from function name and arguments
            key_parts = [func.__module__, func.__name__]
            for arg in args:
                key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            
            key_string = ":".join(key_parts)
            cache_key = hashlib.md5(key_string.encode()).hexdigest()
            
            # Check cache
            cached_value = _cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Call function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            _cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    
    return decorator

def invalidate_cache(prefix: str = "") -> int:
    """
    Invalidate cache entries matching a prefix.
    
    Args:
        prefix: The prefix to match against cache keys
        
    Returns:
        Number of items invalidated
    """
    if not prefix:
        count = len(_cache._cache)
        _cache.clear()
        return count
    
    keys_to_delete = [
        key for key in _cache._cache.keys()
        if key.startswith(prefix)
    ]
    
    for key in keys_to_delete:
        _cache.delete(key)
    
    return len(keys_to_delete)

def get_cache() -> SimpleCache:
    """
    Get the global cache instance.
    
    Returns:
        The SimpleCache instance
    """
    return _cache 