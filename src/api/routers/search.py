"""
Search router for Kevin API.

This module provides API endpoints for searching documents.
"""

import time
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from src.api.models import ErrorResponse
from src.api.services.search import search_documents, search_web
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/documents", responses={500: {"model": ErrorResponse}})
async def search_docs(
    query: str,
    limit: int = Query(5, ge=1, le=20),
    include_content: bool = Query(True)
):
    """
    Search documents in the vector store.
    
    This endpoint searches for documents relevant to the query in the vector store.
    """
    try:
        # Start timing
        start_time = time.time()
        
        # Perform the search
        documents = search_documents(query, limit)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Prepare results
        results = []
        for doc in documents:
            doc_data = {
                "id": doc.get("id", ""),
                "metadata": doc.get("metadata", {})
            }
            if include_content:
                doc_data["content"] = doc.get("content", "")
            results.append(doc_data)
        
        # Return the response
        return {
            "query": query,
            "documents": results,
            "count": len(results),
            "duration_seconds": duration
        }
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/web", responses={500: {"model": ErrorResponse}})
async def search_web_endpoint(
    query: str,
    limit: int = Query(5, ge=1, le=10)
):
    """
    Search the web for information.
    
    This endpoint searches the web for information relevant to the query.
    """
    try:
        # Start timing
        start_time = time.time()
        
        # Perform the search
        documents = search_web(query, limit)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Return the response
        return {
            "query": query,
            "documents": documents,
            "count": len(documents),
            "duration_seconds": duration
        }
    except Exception as e:
        logger.error(f"Error searching web: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 