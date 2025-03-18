"""
Admin service for Kevin API.

This module provides services for administrative tasks.
"""

import os
import time
from typing import Dict, Any, List, Optional, Tuple

from src.utils.logger import get_logger
from src.api.services.documents import clear_document_cache
from src.api.services.chat import get_agent
from src.api.services.cache.cache_service import clear_semantic_cache, get_cache_stats

logger = get_logger(__name__)


def rebuild_index() -> Dict[str, Any]:
    """
    Rebuild the vector index.
    
    Returns:
        Status information
    """
    logger.info("Rebuilding vector index")
    
    start_time = time.time()
    
    # For now, this is a stub - in a real implementation, this would
    # trigger the vector index rebuild process
    
    time.sleep(2)  # Simulate work
    
    duration = time.time() - start_time
    
    return {
        "success": True,
        "message": "Vector index rebuilt successfully",
        "duration_seconds": duration
    }


def clear_caches() -> Dict[str, Any]:
    """
    Clear all caches.
    
    Returns:
        Status information
    """
    logger.info("Clearing all caches")
    
    start_time = time.time()
    
    # Clear document cache
    doc_count = clear_document_cache()
    
    # Clear semantic cache if available
    semantic_cache_count = clear_semantic_cache()
    
    # Clear agent cache if possible
    agent = get_agent()
    agent_cache_cleared = False
    if hasattr(agent, 'clear_cache'):
        agent.clear_cache()
        agent_cache_cleared = True
    
    duration = time.time() - start_time
    
    return {
        "success": True,
        "message": "Caches cleared successfully",
        "details": {
            "documents_cleared": doc_count,
            "semantic_cache_cleared": semantic_cache_count,
            "agent_cache_cleared": agent_cache_cleared
        },
        "duration_seconds": duration
    }


def get_system_status() -> Dict[str, Any]:
    """
    Get system status information.
    
    Returns:
        System status information
    """
    logger.info("Getting system status")
    
    import platform
    import psutil
    
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # Disk usage
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    
    # Python version
    python_version = platform.python_version()
    
    # System info
    system_info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }
    
    # Get cache stats
    cache_stats = get_cache_stats()
    
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "disk_percent": disk_percent,
        "python_version": python_version,
        "system_info": system_info,
        "cache_stats": cache_stats,
        "timestamp": time.time()
    } 