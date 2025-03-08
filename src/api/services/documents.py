"""
Documents service for Kevin API.

This module provides services for retrieving and managing documents.
"""

import os
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Document cache
_document_cache: Dict[str, Dict[str, Any]] = {}


def get_document(document_id: str) -> Dict[str, Any]:
    """
    Get a document by ID.
    
    Args:
        document_id: The document ID
        
    Returns:
        Document object or None if not found
    """
    # Check cache first
    if document_id in _document_cache:
        logger.info(f"Retrieved document from cache: {document_id}")
        return _document_cache[document_id]
    
    # If not in cache, we need to locate it
    # For now, this is a stub - in a real implementation, this would
    # query a database or file system
    
    # Raise exception if not found
    logger.error(f"Document not found: {document_id}")
    raise ValueError(f"Document not found: {document_id}")


def get_document_by_url(url: str) -> Dict[str, Any]:
    """
    Get a document by URL.
    
    Args:
        url: The document URL
        
    Returns:
        Document object or None if not found
    """
    # Generate a document ID from the URL
    document_id = hashlib.md5(url.encode()).hexdigest()
    
    # Check cache first
    if document_id in _document_cache:
        logger.info(f"Retrieved document from cache: {document_id} (URL: {url})")
        return _document_cache[document_id]
    
    # If not in cache, we need to fetch it
    # For now, this is a stub - in a real implementation, this would
    # fetch the document from the URL or a cache
    
    # Raise exception if not found
    logger.error(f"Document not found for URL: {url}")
    raise ValueError(f"Document not found for URL: {url}")


def cache_document(document: Dict[str, Any]) -> str:
    """
    Cache a document for future retrieval.
    
    Args:
        document: The document to cache
        
    Returns:
        Document ID
    """
    # Generate a document ID
    content = document.get("content", "")
    metadata = document.get("metadata", {})
    document_id = hashlib.md5((content + str(metadata)).encode()).hexdigest()
    
    # Store in cache
    _document_cache[document_id] = document
    
    logger.info(f"Cached document: {document_id}")
    
    return document_id


def clear_document_cache() -> int:
    """
    Clear the document cache.
    
    Returns:
        Number of documents cleared
    """
    global _document_cache
    count = len(_document_cache)
    _document_cache = {}
    logger.info(f"Cleared document cache ({count} documents)")
    return count 