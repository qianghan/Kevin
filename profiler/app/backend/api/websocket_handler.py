from abc import ABC, abstractmethod
from typing import Any, Dict
from fastapi import WebSocket

class WebSocketMessageHandler(ABC):
    """Abstract base class for WebSocket message handlers"""
    
    @abstractmethod
    async def handle_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """Handle incoming WebSocket message"""
        pass

class DocumentAnalysisHandler(WebSocketMessageHandler):
    """Handler for document analysis messages"""
    
    def __init__(self, document_service):
        self.document_service = document_service
    
    async def handle_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        if message["type"] == "analyze_document":
            result = await self.document_service.analyze_document(
                message["data"]["document_id"],
                message["data"]["content"]
            )
            await websocket.send_json({
                "type": "document_analysis",
                "data": result.dict()
            })

class QAHandler(WebSocketMessageHandler):
    """Handler for QA messages"""
    
    def __init__(self, qa_service):
        self.qa_service = qa_service
    
    async def handle_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        if message["type"] == "ask_question":
            answer = await self.qa_service.answer_question(
                message["data"]["question"]
            )
            await websocket.send_json({
                "type": "qa_response",
                "data": {"answer": answer}
            })

class RecommendationHandler(WebSocketMessageHandler):
    """Handler for recommendation messages"""
    
    def __init__(self, recommendation_service):
        self.recommendation_service = recommendation_service
    
    async def handle_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        if message["type"] == "get_recommendations":
            recommendations = await self.recommendation_service.get_recommendations(
                message["data"]["context"]
            )
            await websocket.send_json({
                "type": "recommendations",
                "data": {"suggestions": [r.dict() for r in recommendations]}
            })

class WebSocketMessageRouter:
    """Router for WebSocket messages"""
    
    def __init__(self):
        self.handlers: Dict[str, WebSocketMessageHandler] = {}
    
    def register_handler(self, message_type: str, handler: WebSocketMessageHandler):
        """Register a handler for a specific message type"""
        self.handlers[message_type] = handler
    
    async def route_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Route message to appropriate handler"""
        handler = self.handlers.get(message["type"])
        if handler:
            await handler.handle_message(message, websocket)
        else:
            await websocket.send_json({
                "type": "error",
                "error": f"Unknown message type: {message['type']}"
            }) 