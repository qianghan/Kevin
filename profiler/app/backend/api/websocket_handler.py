"""
WebSocket message handlers for different message types.
"""

from typing import Dict, Any, Optional, Type
import logging
import traceback
import json
from datetime import datetime, timezone

from fastapi import WebSocket
from ..utils.validation import (
    validate_websocket_message,
    WebSocketMessage,
    DocumentAnalysisMessage,
    QuestionMessage,
    RecommendationMessage
)
from ..services.interfaces import (
    IDocumentService,
    IRecommendationService,
    IQAService
)

logger = logging.getLogger(__name__)

class MessageHandler:
    """Base message handler interface"""
    
    async def handle(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a WebSocket message.
        
        Args:
            message: The message to handle
            
        Returns:
            Response message
        """
        raise NotImplementedError("Subclasses must implement handle()")


class DocumentAnalysisHandler(MessageHandler):
    """Handler for document analysis messages"""
    
    def __init__(self, document_service: IDocumentService):
        self.document_service = document_service
    
    async def handle(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle document analysis message.
        
        Args:
            message: Document analysis message
            
        Returns:
            Analysis result message
        """
        try:
            # Validate the message
            validated_message = validate_websocket_message(message)
            
            if not isinstance(validated_message, DocumentAnalysisMessage):
                raise ValueError("Invalid document analysis message format")
            
            document_id = validated_message.data.documentId
            content = validated_message.data.content
            url = validated_message.data.url
            
            if not document_id:
                raise ValueError("Document ID is required")
            
            # Process document
            if content:
                result = await self.document_service.analyze_document_content(document_id, content)
            elif url:
                result = await self.document_service.analyze_document_url(document_id, str(url))
            else:
                raise ValueError("Either content or URL is required")
            
            return {
                "type": "analyze_document_response",
                "data": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error in document analysis: {e}")
            logger.debug(traceback.format_exc())
            return {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


class QAHandler(MessageHandler):
    """Handler for Q&A messages"""
    
    def __init__(self, qa_service: IQAService):
        self.qa_service = qa_service
    
    async def handle(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Q&A message.
        
        Args:
            message: Q&A message
            
        Returns:
            Answer message
        """
        try:
            # Validate the message
            validated_message = validate_websocket_message(message)
            
            if not isinstance(validated_message, QuestionMessage):
                raise ValueError("Invalid question message format")
            
            question = validated_message.data.question
            context = validated_message.data.context
            
            if not question:
                raise ValueError("Question is required")
            
            # Process question
            answer = await self.qa_service.answer_question(question, context)
            
            return {
                "type": "ask_question_response",
                "data": answer,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error in QA: {e}")
            logger.debug(traceback.format_exc())
            return {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


class RecommendationHandler(MessageHandler):
    """Handler for recommendation messages"""
    
    def __init__(self, recommendation_service: IRecommendationService):
        self.recommendation_service = recommendation_service
    
    async def handle(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle recommendation message.
        
        Args:
            message: Recommendation message
            
        Returns:
            Recommendations message
        """
        try:
            # Validate the message
            validated_message = validate_websocket_message(message)
            
            if not isinstance(validated_message, RecommendationMessage):
                raise ValueError("Invalid recommendation message format")
            
            profile_id = validated_message.data.profile_id
            count = validated_message.data.count or 5  # Default to 5 recommendations
            
            # Get recommendations
            recommendations = await self.recommendation_service.get_recommendations(
                profile_id=profile_id,
                count=count
            )
            
            return {
                "type": "get_recommendations_response",
                "data": recommendations,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Error in recommendations: {e}")
            logger.debug(traceback.format_exc())
            return {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


class WebSocketMessageRouter:
    """Router for WebSocket messages"""
    
    def __init__(self):
        """Initialize the router with empty handlers"""
        self.handlers: Dict[str, MessageHandler] = {}
    
    def register_handler(self, message_type: str, handler: MessageHandler) -> None:
        """
        Register a handler for a message type.
        
        Args:
            message_type: The message type to register for
            handler: The handler to use
        """
        self.handlers[message_type] = handler
    
    async def route_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a message to the appropriate handler.
        
        Args:
            message: The message to route
            
        Returns:
            Response message
            
        Raises:
            ValueError: If the message type is not supported
        """
        try:
            # Basic validation
            if not isinstance(message, dict) or 'type' not in message:
                raise ValueError("Invalid message format, missing 'type' field")
            
            message_type = message.get('type')
            handler = self.handlers.get(message_type)
            
            if not handler:
                raise ValueError(f"No handler for message type: {message_type}")
            
            return await handler.handle(message)
        except Exception as e:
            logger.error(f"Error routing message: {e}")
            logger.debug(traceback.format_exc())
            return {
                "type": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            } 