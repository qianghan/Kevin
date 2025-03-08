"""
Documents router for Kevin API.

This module provides API endpoints for document retrieval.
"""

from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from src.api.models import ErrorResponse
from src.api.services.documents import get_document, get_document_by_url
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/get/{document_id}", responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_document_by_id(
    document_id: str,
    include_content: bool = Query(True)
):
    """
    Get a document by its ID.
    
    This endpoint retrieves a document by its ID.
    """
    try:
        # Get the document
        document = get_document(document_id)
        
        # Prepare the response
        response = {
            "id": document_id,
            "metadata": document.get("metadata", {})
        }
        
        # Include content if requested
        if include_content:
            response["content"] = document.get("content", "")
        
        # Return the document
        return response
    except ValueError as e:
        # Document not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Other errors
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/url", responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_document_by_url_endpoint(
    url: str,
    include_content: bool = Query(True)
):
    """
    Get a document by its URL.
    
    This endpoint retrieves a document by its URL.
    """
    try:
        # Get the document
        document = get_document_by_url(url)
        
        # Prepare the response
        response = {
            "url": url,
            "id": document.get("id", ""),
            "metadata": document.get("metadata", {})
        }
        
        # Include content if requested
        if include_content:
            response["content"] = document.get("content", "")
        
        # Return the document
        return response
    except ValueError as e:
        # Document not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Other errors
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 