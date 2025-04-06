"""
Authentication utilities for the Profiler API.

This module provides middleware and dependency functions for authenticating API requests.
"""

from fastapi import Security, HTTPException, status, Depends, Request
from fastapi.security import APIKeyHeader
from typing import List, Optional

# Define the API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    request: Request,
    api_key_header: Optional[str] = Security(API_KEY_HEADER)
) -> str:
    """
    Validate the API key from the request headers.
    
    Args:
        request: The incoming request
        api_key_header: The API key from the X-API-Key header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: If the API key is missing or invalid
    """
    # Get allowed API keys from app state
    allowed_api_keys: List[str] = getattr(request.app.state, "api_keys", [])
    
    # Check if API key is provided
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Please provide a valid API key in the X-API-Key header."
        )
    
    # Check if API key is valid
    if api_key_header not in allowed_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key. Please provide a valid API key."
        )
    
    return api_key_header 