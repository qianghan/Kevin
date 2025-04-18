"""
WebSocket handler for real-time profile building.

This module provides functionality for WebSocket connections,
enabling real-time interaction during the profile building process.
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends, status, APIRouter
from typing import Dict, Any, List, Optional, Callable
import json
import asyncio
import uuid
from datetime import datetime, timezone
import logging

from ..utils.logging import get_logger
from ..utils.errors import ValidationError, ServiceError
from ..utils.config_manager import ConfigManager
from ..core.workflows.profile_workflow import (
    create_workflow_executor,
    WorkflowConfig,
    create_profile_workflow
)
from ..core.models.state import create_initial_state, ProfileState
from .dependencies import ServiceFactory
from app.backend.api.websocket_handler import (
    WebSocketMessageRouter,
    DocumentAnalysisHandler,
    QAHandler,
    RecommendationHandler,
    HelloHandler,
    SwitchSectionHandler
)
from app.backend.services.interfaces import (
    IDocumentService,
    IRecommendationService,
    IQAService
)

logger = logging.getLogger(__name__)
config = ConfigManager().get_all()

# Create router with auth
router = APIRouter()

class ConnectionManager:
    """
    Manager for WebSocket connections.
    
    This class handles WebSocket connections, message broadcasting,
    and maintains the workflow executors for each user session.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.workflow_executors: Dict[str, Any] = {}
        self.session_metadata: Dict[str, Dict[str, Any]] = {}
        self.user_states: Dict[str, ProfileState] = {}
        self.message_router = WebSocketMessageRouter()
    
    def initialize_handlers(
        self,
        document_service: IDocumentService,
        recommendation_service: IRecommendationService,
        qa_service: IQAService
    ):
        """Initialize message handlers with service dependencies"""
        self.message_router.register_handler(
            "analyze_document",
            DocumentAnalysisHandler(document_service)
        )
        self.message_router.register_handler(
            "ask_question",
            QAHandler(qa_service)
        )
        self.message_router.register_handler(
            "get_recommendations",
            RecommendationHandler(recommendation_service)
        )
        self.message_router.register_handler(
            "hello",
            HelloHandler()
        )
        # Also register the connection_init handler
        self.message_router.register_handler(
            "connection_init",
            HelloHandler()  # Reuse the HelloHandler for connection_init
        )
        # Fallback for ping messages
        self.message_router.register_handler(
            "ping",
            HelloHandler()  # Reuse the HelloHandler for ping
        )
        # Handler for switch_section messages
        self.message_router.register_handler(
            "switch_section",
            SwitchSectionHandler()
        )
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """
        Connect a new WebSocket client.
        
        Args:
            websocket: The WebSocket connection
            user_id: The user's ID
            
        Returns:
            Session ID for the connection
        """
        try:
            # Generate a unique session ID
            session_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
            
            # Store connection
            self.active_connections[session_id] = websocket
            
            # Record session metadata
            self.session_metadata[session_id] = {
                "user_id": user_id,
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "client_info": {
                    "ip": websocket.client.host if websocket.client else "unknown"
                }
            }
            
            logger.info(f"WebSocket connected: user_id={user_id}, session_id={session_id}")
            
            try:
                # Initialize workflow executor
                workflow_config = WorkflowConfig(
                    session_timeout_minutes=config.get("websocket", {}).get("session_timeout_minutes", 30),
                    max_interactions=config.get("websocket", {}).get("max_interactions", 100),
                    confidence_threshold=config.get("websocket", {}).get("confidence_threshold", 0.8),
                    human_review_threshold=config.get("websocket", {}).get("human_review_threshold", 0.7)
                )
                
                # Get service instances and ensure they're initialized
                qa_service = await ServiceFactory.get_qa_service()
                
                document_service = ServiceFactory.get_document_service()
                await document_service.initialize()
                
                recommendation_service = ServiceFactory.get_recommendation_service()
                await recommendation_service.initialize()
                
                # Create workflow executor
                self.workflow_executors[session_id] = create_workflow_executor(
                    config=workflow_config,
                    qa_service=qa_service,
                    document_service=document_service,
                    recommender_service=recommendation_service
                )
                
                # Create initial state
                initial_state = create_initial_state(user_id)
                self.user_states[session_id] = initial_state
                
                # Send initial messages
                await self.send_message(session_id, {
                    "type": "connected",
                    "session_id": session_id,
                    "message": "Connected to profile builder",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Send initial state
                await self.send_message(session_id, {
                    "type": "state_update",
                    "data": initial_state,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                logger.info(f"Initial state sent for session {session_id}")
                
                return session_id
                
            except Exception as e:
                logger.error(f"Error initializing workflow for session {session_id}: {str(e)}")
                await self.send_message(session_id, {
                    "type": "error",
                    "error": "Failed to initialize profile builder",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                raise
                
        except Exception as e:
            logger.error(f"Error in WebSocket connection: {str(e)}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            raise
    
    def validate_session(self, session_id: str) -> bool:
        """
        Validate a session ID.
        
        Args:
            session_id: The session ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not session_id or not isinstance(session_id, str):
            return False
            
        # Check if session exists
        if session_id not in self.active_connections:
            return False
            
        # Check if session is still active
        if session_id not in self.workflow_executors:
            return False
            
        return True
    
    async def receive_message(self, message: str, websocket: WebSocket) -> None:
        """
        Handle incoming WebSocket messages.
        
        Args:
            message: The received message
            websocket: The WebSocket connection
        """
        session_id = None
        try:
            # Parse message
            data = json.loads(message)
            logger.debug(f"Received message: {data}")
            
            # Get session ID from active connections
            for sid, ws in self.active_connections.items():
                if ws == websocket:
                    session_id = sid
                    break
            
            if not session_id or not self.validate_session(session_id):
                await self.send_message(session_id, {
                    "type": "error",
                    "error": "Invalid session ID",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                return
            
            # Process the message
            response = await self.message_router.route_message(data)
            
            # Send the response back to the client
            if response:
                await self.send_message(session_id, response)
            
            # Update last activity timestamp
            if session_id:
                self.session_metadata[session_id]["last_activity"] = datetime.now(timezone.utc).isoformat()
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in message: {message}")
            # Cannot send an error response without a session ID
            if session_id:
                await self.send_message(session_id, {
                    "type": "error",
                    "error": "Invalid message format",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}", exc_info=True)
            if session_id:
                await self.send_message(session_id, {
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
    
    async def _process_message(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Process a valid message and update the state.
        
        Args:
            session_id: The session ID
            data: The message data
        """
        # Get current state
        current_state = self.user_states.get(session_id)
        if not current_state:
            await self.send_message(session_id, {
                "type": "error",
                "error": "No state found for session",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            return
        
        # Get workflow executor
        workflow = self.workflow_executors.get(session_id)
        if not workflow:
            await self.send_message(session_id, {
                "type": "error",
                "error": "Workflow not initialized",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            return
            
        try:
            # Extract message data based on message type
            message_type = data.get("type", "")
            message_data = data.get("data", {})
            
            # Update state based on message type
            updated_state = await self._update_state(
                current_state=current_state,
                message_type=message_type,
                message_data=message_data,
                raw_data=data
            )
            
            # Execute workflow with updated state
            try:
                result = await workflow.arun(updated_state)
                
                # Update state
                self.user_states[session_id] = result
                
                # Send state update
                await self.send_message(session_id, {
                    "type": "state_update",
                    "data": result,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                logger.error(f"Error executing workflow: {str(e)}", exc_info=True)
                await self.send_message(session_id, {
                    "type": "error",
                    "error": f"Workflow execution error: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        except Exception as e:
            logger.error(f"Error processing message for session {session_id}: {str(e)}", exc_info=True)
            await self.send_message(session_id, {
                "type": "error",
                "error": "Failed to process message",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    async def _update_state(
        self, 
        current_state: Dict[str, Any], 
        message_type: str, 
        message_data: Dict[str, Any],
        raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update the state based on message type.
        
        Args:
            current_state: The current state
            message_type: The message type
            message_data: The message data
            raw_data: The raw message data
            
        Returns:
            Updated state
        """
        # Create a copy of the state to avoid modifying the original
        state = current_state.copy()
        
        # Handle different message types
        if message_type == "answer":
            # Extract the answer from the message
            answer = raw_data.get("answer")
            if answer is None and message_data:
                # Try to get answer from data object
                answer = message_data.get("answer") or message_data.get("user_answer")
            
            # Update state with answer
            if answer is not None:
                state["current_answer"] = answer
                state["last_updated"] = datetime.now(timezone.utc).isoformat()
                logger.debug(f"Updated answer to: {answer}")
            else:
                logger.error(f"Answer not found in message: {raw_data}")
                raise ValueError("Answer not found in message")
                
        elif message_type == "document_upload":
            # Handle document upload
            section = message_data.get("section")
            content = message_data.get("content")
            if section and content:
                state["sections"][section]["data"] = content
                state["current_section"] = section
                state["last_updated"] = datetime.now(timezone.utc).isoformat()
            else:
                logger.error(f"Invalid document upload data: {message_data}")
                raise ValueError("Invalid document upload data")
                
        elif message_type == "review_feedback":
            # Handle review feedback
            section = message_data.get("section")
            feedback = message_data.get("feedback")
            if section and feedback:
                # Find matching review request
                for i, request in enumerate(state.get("review_requests", [])):
                    if request.get("section") == section:
                        # Apply feedback to section
                        if feedback.get("approved"):
                            state["sections"][section]["status"] = "completed"
                        else:
                            state["sections"][section]["status"] = "in_progress"
                        # Remove the review request
                        state["review_requests"].pop(i)
                        break
            else:
                logger.error(f"Invalid review feedback data: {message_data}")
                raise ValueError("Invalid review feedback data")
        elif message_type == "switch_section":
            # Handle section switching
            section = message_data.get("section")
            if section:
                state["current_section"] = section
                state["last_updated"] = datetime.now(timezone.utc).isoformat()
                logger.debug(f"Switched to section: {section}")
            else:
                logger.error(f"Invalid section switch data: {message_data}")
                raise ValueError("Invalid section switch data")
        else:
            logger.warning(f"Unknown message type: {message_type}")
        
        # Increment interaction count
        state["interaction_count"] = state.get("interaction_count", 0) + 1
        
        # Return updated state
        return state
    
    async def send_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """
        Send a message to a specific client.
        
        Args:
            session_id: The session ID
            message: The message to send
        """
        try:
            if session_id in self.active_connections:
                await self.active_connections[session_id].send_json(message)
                logger.debug(f"Message sent to session {session_id}: {message}")
        except Exception as e:
            logger.error(f"Error sending message to session {session_id}: {str(e)}")
    
    def disconnect(self, session_id: str) -> None:
        """
        Disconnect a client.
        
        Args:
            session_id: The session ID
        """
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.workflow_executors:
            del self.workflow_executors[session_id]
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
        if session_id in self.user_states:
            del self.user_states[session_id]
        logger.info(f"WebSocket disconnected: session_id={session_id}")

    async def broadcast(self, message: Dict[str, Any], exclude: List[str] = None) -> None:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast
            exclude: List of session IDs to exclude from broadcast
        """
        exclude = exclude or []
        for session_id, websocket in self.active_connections.items():
            if session_id not in exclude:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to session {session_id}: {str(e)}")
                    continue

# Create a global connection manager instance
manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for profile building.
    
    Args:
        websocket: The WebSocket connection
        user_id: The user's ID
    """
    try:
        # Log connection attempt with detailed info
        x_api_key = websocket.query_params.get("x-api-key", "none")
        logger.info(f"WebSocket connection attempt from user_id={user_id} with api_key={x_api_key}")
        logger.debug(f"WebSocket headers: {websocket.headers}")
        logger.debug(f"WebSocket query params: {websocket.query_params}")
        
        # Get valid keys from app state
        from app.backend.api.main import VALID_API_KEYS
        
        # Validate API key
        if x_api_key not in VALID_API_KEYS:
            logger.warning(f"Invalid API key provided for user {user_id}: {x_api_key}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Accept the connection with valid API key
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for user_id={user_id}")
        
        # Connect and get session ID
        try:
            session_id = await manager.connect(websocket, user_id)
            logger.info(f"WebSocket session established: user_id={user_id}, session_id={session_id}")
            
            try:
                while True:
                    # Receive messages
                    message = await websocket.receive_text()
                    logger.debug(f"WebSocket message received from session {session_id}: {message[:100]}...")
                    await manager.receive_message(message, websocket)
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected by client: session_id={session_id}")
                manager.disconnect(session_id)
                
        except Exception as e:
            logger.error(f"WebSocket session handling error: {str(e)}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "error": f"Session error: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}", exc_info=True)
        try:
            # If we haven't accepted the connection yet, we can't send a message
            if websocket.client_state == WebSocket.client_state.CONNECTED:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Connection error: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception as close_error:
            logger.error(f"Error closing WebSocket: {str(close_error)}") 