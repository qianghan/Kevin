"""
Health check endpoints for the Profiler API.

This module provides endpoints for checking the health and status of the API.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request

from app.backend.api.auth import get_api_key

# Create a router for health check endpoints
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check(request: Request, api_key: str = Depends(get_api_key)):
    """
    Health check endpoint for the API.
    
    Returns information about the API status, version, and environment.
    """
    # Get API version from state or use default
    version = getattr(request.app.state, "version", "1.0.0")
    environment = getattr(request.app.state, "environment", "development")
    
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": version,
        "environment": environment,
        "api": {
            "name": "Profiler API",
            "status": "operational"
        }
    } 