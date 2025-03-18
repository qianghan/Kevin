"""
Chat router for Kevin API.

This module provides API endpoints for chat functionality.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import StreamingResponse

# Add a path fix to ensure src is in the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.api.models import ChatRequest, ChatResponse, ErrorResponse
from src.api.services.chat import process_chat, get_conversation_history
from src.api.services.streaming import StreamManager, StreamCallbackHandler, SyncToAsyncAdapter, StreamEvent
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/query", response_model=ChatResponse, responses={500: {"model": ErrorResponse}})
async def chat_query(request: ChatRequest):
    """
    Process a chat query.
    
    This endpoint processes a chat query and returns a response.
    If streaming is requested, it will redirect to the /query/stream endpoint.
    """
    try:
        # If streaming is requested, redirect to streaming endpoint
        if request.stream:
            url = f"/api/chat/query/stream?query={request.query}"
            if request.use_web_search:
                url += "&use_web_search=true"
            if request.conversation_id:
                url += f"&conversation_id={request.conversation_id}"
            
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url=url, status_code=307)
        
        # Process the query
        answer, conversation_id, thinking_steps, documents, duration = process_chat(
            query=request.query,
            use_web_search=request.use_web_search,
            conversation_id=request.conversation_id
        )
        
        # Return the response
        return ChatResponse(
            answer=answer,
            conversation_id=conversation_id,
            thinking_steps=thinking_steps,
            documents=documents,
            duration_seconds=duration
        )
    except Exception as e:
        logger.error(f"Error processing chat query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/stream", responses={500: {"model": ErrorResponse}})
async def chat_query_stream(
    query: str,
    use_web_search: bool = False,
    conversation_id: Optional[str] = None
):
    """
    Process a chat query with streaming response.
    
    This endpoint processes a chat query and returns a streaming response
    using Server-Sent Events (SSE).
    """
    try:
        # Create a stream manager for this request
        stream_manager = StreamManager()
        
        # Create a callback handler for streaming
        callback_handler = StreamCallbackHandler(stream_manager)
        
        # Set up the background task
        adapter = SyncToAsyncAdapter(stream_manager)
        
        # Start processing in the background
        adapter.run_in_background(
            process_chat,
            query,
            use_web_search,
            conversation_id,
            callback_handler
        )
        
        # Return a streaming response
        return StreamingResponse(
            stream_manager.get_stream(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error processing streaming chat query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}", responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def get_conversation(conversation_id: str):
    """
    Get conversation history.
    
    This endpoint returns the conversation history for a specific conversation.
    """
    try:
        # Get the conversation history
        history = get_conversation_history(conversation_id)
        
        # Return 404 if conversation not found
        if not history:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        
        # Return the conversation history
        return {"conversation_id": conversation_id, "messages": history}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 