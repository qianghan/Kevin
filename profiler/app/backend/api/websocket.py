"""
WebSocket handler for real-time profile building.

This module provides functionality for WebSocket connections,
enabling real-time interaction during the profile building process.
"""

from fastapi import WebSocket, WebSocketDisconnect, Depends, status
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
from ..core.models.state import create_initial_state
from .dependencies import ServiceFactory

logger = get_logger(__name__)
config = ConfigManager().get_all()

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
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """
        Connect a new WebSocket client.
        
        Args:
            websocket: The WebSocket connection
            user_id: The user's ID
            
        Returns:
            Session ID for the connection
        """
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
            self.workflow_executors[session_id] = create_profile_workflow(
                config=workflow_config,
                qa_service=qa_service,
                document_service=document_service,
                recommender_service=recommendation_service
            )
            
            # Send initial messages
            await self.send_message(session_id, {
                "type": "connected",
                "session_id": session_id,
                "message": "Connected to profile builder"
            })
            
            # Send an initial empty state to the client
            await self.send_message(session_id, {
                "type": "state_update",
                "data": {
                    "user_id": user_id,
                    "current_section": "academic",
                    "current_questions": [
                        "What courses are you currently taking?",
                        "What are your strongest academic subjects?",
                        "Do you have any academic achievements you'd like to highlight?"
                    ],
                    "current_answer": None,
                    "sections": {
                        "academic": {"status": "not_started", "grades": [], "courses": [], "achievements": []},
                        "extracurricular": {"status": "not_started", "activities": [], "leadership": [], "service": []},
                        "personal": {"status": "not_started", "background": {"nationality": "", "languages": [], "interests": []}, "goals": {"short_term": [], "long_term": [], "target_schools": []}, "interests": []},
                        "essays": {"status": "not_started", "topics": [], "content": {"main_theme": "", "key_points": [], "style": ""}, "style": {"tone": "", "structure": "", "unique_elements": []}}
                    },
                    "context": {},
                    "review_requests": [],
                    "interaction_count": 0,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "status": "in_progress",
                    "error": None,
                    "summary": None
                }
            })
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error initializing workflow executor: {str(e)}")
            self.disconnect(session_id)  # Clean up the connection we just added
            raise
    
    def disconnect(self, session_id: str):
        """
        Disconnect a WebSocket client.
        
        Args:
            session_id: The session ID to disconnect
        """
        if session_id in self.active_connections:
            user_id = self.session_metadata.get(session_id, {}).get("user_id", "unknown")
            logger.info(f"WebSocket disconnected: user_id={user_id}, session_id={session_id}")
            
            del self.active_connections[session_id]
            
        if session_id in self.workflow_executors:
            del self.workflow_executors[session_id]
            
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """
        Send message to a specific client.
        
        Args:
            session_id: The session ID to send to
            message: The message to send
        """
        if session_id in self.active_connections:
            # Add timestamp to all messages
            if "timestamp" not in message:
                message["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            try:
                await self.active_connections[session_id].send_json(message)
                logger.debug(f"Message sent to session {session_id}: {message['type']}")
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {str(e)}")
                # If send fails, disconnect the client
                self.disconnect(session_id)
    
    async def broadcast(self, message: Dict[str, Any], exclude: Optional[List[str]] = None):
        """
        Broadcast message to all connected clients.
        
        Args:
            message: The message to broadcast
            exclude: Optional list of session IDs to exclude
        """
        exclude = exclude or []
        sent_count = 0
        
        # Add timestamp to all messages
        if "timestamp" not in message:
            message["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        for session_id, connection in self.active_connections.items():
            if session_id not in exclude:
                try:
                    await connection.send_json(message)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Error broadcasting to session {session_id}: {str(e)}")
                    # Don't disconnect here to avoid modifying dict during iteration
        
        logger.info(f"Broadcast message sent to {sent_count} clients: {message['type']}")

    async def receive_message(self, message: str, websocket: WebSocket) -> None:
        """Handle incoming WebSocket messages"""
        try:
            # Parse message
            data = json.loads(message)
            session_id = data.get("session_id")
            
            if not session_id or session_id not in self.workflow_executors:
                await websocket.send_json({
                    "error": "Invalid session ID"
                })
                return
            
            # Get workflow executor
            executor = self.workflow_executors[session_id]
            
            # Convert message to state
            state = create_initial_state(
                user_id=data.get("user_id", "default"),
                current_section=data.get("section", "background"),
                current_answer=data.get("answer", {}),
                context=data.get("context", {})
            )
            
            # Process state through workflow
            try:
                result = await executor.ainvoke({
                    "state_dict": state.model_dump()
                })
                
                # Send result back
                await websocket.send_json(result)
            except Exception as e:
                logger.error(f"Error executing workflow: {str(e)}")
                await websocket.send_json({
                    "error": f"Workflow execution failed: {str(e)}"
                })
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message: {str(e)}")
            await websocket.send_json({
                "error": "Invalid JSON message"
            })
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await websocket.send_json({
                "error": f"Message processing failed: {str(e)}"
            })

# Create a global connection manager instance
manager = ConnectionManager() 