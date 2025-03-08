"""
Admin router for Kevin API.

This module provides API endpoints for administrative tasks.
"""

import time
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.responses import JSONResponse

from src.api.models import AdminAction, AdminRequest, AdminResponse, ErrorResponse
from src.api.services.admin import rebuild_index, clear_caches, get_system_status
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("", response_model=AdminResponse, responses={500: {"model": ErrorResponse}})
async def admin_action(request: AdminRequest = Body(...)):
    """
    Perform an administrative action.
    
    This endpoint allows authorized users to perform administrative actions
    such as rebuilding the index, clearing caches, or getting system status.
    """
    try:
        # Start timing
        start_time = time.time()
        
        # Dispatch the action
        if request.action == AdminAction.REBUILD_INDEX:
            result = rebuild_index()
        elif request.action == AdminAction.CLEAR_CACHES:
            result = clear_caches()
        elif request.action == AdminAction.GET_SYSTEM_STATUS:
            result = get_system_status()
        else:
            raise ValueError(f"Unsupported action: {request.action}")
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Create response
        response = AdminResponse(
            success=True,
            message=result.get("message", "Action completed successfully"),
            details=result.get("details"),
            duration_seconds=duration
        )
        
        return response
    except Exception as e:
        logger.error(f"Error performing admin action: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 