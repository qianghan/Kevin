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

logger = get_logger(__name__)
config = ConfigManager().get_all()

# Create router
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
        try:
            # Parse message
            data = json.loads(message)
            
            # Validate session ID
            session_id = data.get("session_id")
            if not self.validate_session(session_id):
                await self.send_message(session_id, {
                    "type": "error",
                    "error": "Invalid session ID",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                return
            
            # Get current state
            current_state = self.user_states.get(session_id)
            if not current_state:
                await self.send_message(session_id, {
                    "type": "error",
                    "error": "No state found for session",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                return
            
            # Process message through workflow
            workflow = self.workflow_executors.get(session_id)
            if workflow:
                try:
                    # Update state with message data
                    current_state["current_answer"] = data.get("answer")
                    current_state["last_updated"] = datetime.now(timezone.utc).isoformat()
                    
                    # Run workflow
                    result = await workflow.arun(current_state)
                    
                    # Update state
                    self.user_states[session_id] = result
                    
                    # Send state update
                    await self.send_message(session_id, {
                        "type": "state_update",
                        "data": result,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                except Exception as e:
                    logger.error(f"Error processing message for session {session_id}: {str(e)}")
                    await self.send_message(session_id, {
                        "type": "error",
                        "error": "Failed to process message",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            else:
                await self.send_message(session_id, {
                    "type": "error",
                    "error": "Workflow not initialized",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
        except json.JSONDecodeError:
            await self.send_message(session_id, {
                "type": "error",
                "error": "Invalid message format",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await self.send_message(session_id, {
                "type": "error",
                "error": "Internal server error",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
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
        # Accept connection
        await websocket.accept()
        
        # Connect and get session ID
        session_id = await manager.connect(websocket, user_id)
        
        try:
            while True:
                # Receive messages
                message = await websocket.receive_text()
                await manager.receive_message(message, websocket)
                
        except WebSocketDisconnect:
            manager.disconnect(session_id)
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass 