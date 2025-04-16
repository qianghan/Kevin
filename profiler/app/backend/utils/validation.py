"""
WebSocket message validation using Pydantic.

This module provides schemas for validating WebSocket messages
to ensure consistent contracts between frontend and backend.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, validator, AnyUrl

class ProfileStatus(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class ProfileState(BaseModel):
    """Profile state model"""
    userId: str
    status: ProfileStatus
    progress: float = Field(..., ge=0, le=100)
    data: Optional[Dict[str, Any]] = None

class WebSocketMessage(BaseModel):
    """Base WebSocket message model"""
    type: str
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None

class StateUpdateMessage(WebSocketMessage):
    """State update message model"""
    type: str = "state_update"
    data: ProfileState

class ConnectedMessage(WebSocketMessage):
    """Connected message model"""
    type: str = "connected"
    session_id: str
    message: str

class ErrorMessage(WebSocketMessage):
    """Error message model"""
    type: str = "error"
    error: str

class DocumentAnalysisData(BaseModel):
    """Document analysis data model"""
    documentId: str
    content: Optional[str] = None
    url: Optional[AnyUrl] = None

class DocumentAnalysisMessage(WebSocketMessage):
    """Document analysis message model"""
    type: str = "analyze_document"
    data: DocumentAnalysisData

class QuestionData(BaseModel):
    """Question data model"""
    question: str
    context: Optional[str] = None

class QuestionMessage(WebSocketMessage):
    """Question message model"""
    type: str = "ask_question"
    data: QuestionData

class RecommendationData(BaseModel):
    """Recommendation data model"""
    profile_id: Optional[str] = None
    count: Optional[int] = Field(None, gt=0)

class RecommendationMessage(WebSocketMessage):
    """Recommendation message model"""
    type: str = "get_recommendations"
    data: RecommendationData

def validate_websocket_message(message: Dict[str, Any]) -> WebSocketMessage:
    """
    Validate a WebSocket message based on its type.
    
    Args:
        message: Dictionary containing the message
        
    Returns:
        Validated WebSocketMessage instance
        
    Raises:
        ValueError: If the message is invalid
    """
    if not isinstance(message, dict) or 'type' not in message:
        raise ValueError("Invalid message format, missing 'type' field")
    
    message_type = message.get("type")
    
    # Map message types to their corresponding models
    type_to_model = {
        "state_update": StateUpdateMessage,
        "connected": ConnectedMessage,
        "error": ErrorMessage,
        "analyze_document": DocumentAnalysisMessage,
        "ask_question": QuestionMessage,
        "get_recommendations": RecommendationMessage
    }
    
    # Get the appropriate model for validation
    model = type_to_model.get(message_type, WebSocketMessage)
    
    try:
        return model(**message)
    except Exception as e:
        raise ValueError(f"Invalid message format for type '{message_type}': {str(e)}") 