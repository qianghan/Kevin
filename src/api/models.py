"""
Data models for Kevin API.

This module defines the Pydantic models used for request and response validation.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ThinkingStep(BaseModel):
    """Model for a thinking step in the agent's reasoning process."""
    
    description: str = Field(description="Description of the thinking step")
    duration: Optional[float] = Field(None, description="Duration of the step in seconds")
    result: Optional[Any] = Field(None, description="Result of the thinking step")
    error: Optional[str] = Field(None, description="Error message if the step failed")


class Document(BaseModel):
    """Model for a document retrieved during the query processing."""
    
    content: str = Field(description="The content of the document")
    metadata: Dict[str, Any] = Field(description="Metadata about the document")


class ChatRequest(BaseModel):
    """Model for a chat query request."""
    
    query: str = Field(description="The query to process")
    use_web_search: bool = Field(False, description="Whether to use web search")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for continuing a conversation")
    stream: bool = Field(False, description="Whether to stream the response")


class ChatResponse(BaseModel):
    """Model for a chat query response."""
    
    answer: str = Field(description="The answer to the query")
    conversation_id: str = Field(description="The conversation ID")
    thinking_steps: List[Dict[str, Any]] = Field([], description="The thinking steps used to generate the answer")
    documents: List[Dict[str, Any]] = Field([], description="The documents retrieved during processing")
    duration_seconds: float = Field(description="Time taken to process the query")


class ErrorResponse(BaseModel):
    """Model for an error response."""
    
    detail: str = Field(description="Error message")


class AdminAction(str, Enum):
    """Enum for admin actions."""
    
    REBUILD_INDEX = "rebuild_index"
    CLEAR_CACHES = "clear_caches"
    GET_SYSTEM_STATUS = "get_system_status"


class AdminRequest(BaseModel):
    """Model for an admin request."""
    
    action: AdminAction = Field(description="The admin action to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters for the action")


class AdminResponse(BaseModel):
    """Model for an admin response."""
    
    success: bool = Field(description="Whether the action was successful")
    message: str = Field(description="A message describing the result")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details about the result")
    duration_seconds: float = Field(description="Time taken to perform the action") 