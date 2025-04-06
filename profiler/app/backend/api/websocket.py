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
    WorkflowConfig
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
        await websocket.accept()
        
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
        
        # Initialize workflow executor
        workflow_config = WorkflowConfig(
            session_timeout_minutes=config.get("websocket", {}).get("session_timeout_minutes", 30),
            max_interactions=config.get("websocket", {}).get("max_interactions", 100),
            confidence_threshold=config.get("websocket", {}).get("confidence_threshold", 0.8),
            human_review_threshold=config.get("websocket", {}).get("human_review_threshold", 0.7)
        )
        
        # Get service instances
        document_service = ServiceFactory.get_document_service()
        recommendation_service = ServiceFactory.get_recommendation_service()
        qa_service = ServiceFactory.get_qa_service()
        
        # Create workflow executor
        self.workflow_executors[session_id] = create_workflow_executor(
            config=workflow_config,
            qa_service=qa_service,
            document_service=document_service,
            recommendation_service=recommendation_service
        )
        
        return session_id
    
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

# Create a singleton instance
manager = ConnectionManager()

async def handle_websocket(websocket: WebSocket, user_id: str):
    """
    Handle WebSocket connection for a profile building session.
    
    This function manages the entire lifecycle of a WebSocket connection,
    including state updates, workflow execution, and error handling.
    
    Args:
        websocket: The WebSocket connection
        user_id: The user's ID
    """
    session_id = None
    
    try:
        # Connect client and get session ID
        session_id = await manager.connect(websocket, user_id)
        
        # Initialize state
        state = create_initial_state(user_id)
        
        # Send initial state
        await manager.send_message(session_id, {
            "type": "state_update",
            "data": state
        })
        
        # Get workflow executor (now a ToolNode)
        tool_node = manager.workflow_executors[session_id]
        
        # Process messages in a loop
        while True:
            # Receive message with timeout
            try:
                # Set a timeout for receiving messages
                message = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=config.get("websocket", {}).get("idle_timeout", 300)  # 5 minutes default
                )
            except asyncio.TimeoutError:
                # Send ping to check if client is still connected
                await manager.send_message(session_id, {"type": "ping"})
                continue
            
            # Log received message
            logger.info(f"Received message from session {session_id}: {message.get('type')}")
            
            try:
                # Process message based on type
                if message["type"] == "answer":
                    # Validate message format
                    if "data" not in message:
                        raise ValidationError("Missing 'data' field in message")
                    
                    # Update state with answer
                    state["current_answer"] = message["data"]
                    state["last_updated"] = datetime.now(timezone.utc).isoformat()
                    
                    # Send acknowledgment
                    await manager.send_message(session_id, {
                        "type": "processing",
                        "data": {"message": "Processing your answer..."}
                    })
                    
                    # Execute the appropriate tool in the tool node
                    # (Using ainvoke instead of arun for ToolNode)
                    tool_call = {
                        "name": "process_profile",  # The name of the tool to call
                        "arguments": json.dumps(state)  # Convert state to JSON for the tool
                    }
                    result = await tool_node.ainvoke(tool_call)
                    
                    # Parse the tool result to get the updated state
                    try:
                        state = json.loads(result.content)
                    except (json.JSONDecodeError, AttributeError):
                        # If result can't be parsed as JSON, use original state
                        logger.error(f"Failed to parse tool result: {result}")
                    
                    # Send updated state
                    await manager.send_message(session_id, {
                        "type": "state_update",
                        "data": state
                    })
                    
                elif message["type"] == "review_feedback":
                    # Validate message format
                    if "data" not in message or "section" not in message["data"] or "feedback" not in message["data"]:
                        raise ValidationError("Invalid review feedback format")
                    
                    section = message["data"]["section"]
                    feedback = message["data"]["feedback"]
                    
                    # Update section based on feedback
                    if section not in state["sections"]:
                        raise ValidationError(f"Section '{section}' not found in state")
                    
                    state["sections"][section].update(feedback)
                    state["sections"][section]["status"] = "in_progress"
                    state["last_updated"] = datetime.now(timezone.utc).isoformat()
                    
                    # Remove review request
                    state["review_requests"] = [
                        req for req in state["review_requests"]
                        if req["section"] != section
                    ]
                    
                    # Send updated state
                    await manager.send_message(session_id, {
                        "type": "state_update",
                        "data": state
                    })
                    
                elif message["type"] == "document_upload":
                    # Validate message format
                    if "data" not in message or "section" not in message["data"] or "content" not in message["data"]:
                        raise ValidationError("Invalid document upload format")
                    
                    section = message["data"]["section"]
                    content = message["data"]["content"]
                    document_type = message["data"].get("document_type", "resume")
                    
                    # Validate document type
                    document_service = ServiceFactory.get_document_service()
                    valid = await document_service.validate_document_type(document_type)
                    if not valid:
                        raise ValidationError(f"Invalid document type: {document_type}")
                    
                    # Send acknowledgment
                    await manager.send_message(session_id, {
                        "type": "processing",
                        "data": {"message": "Processing your document..."}
                    })
                    
                    # Update state with document content
                    state["current_answer"] = {
                        "document_content": content,
                        "document_type": document_type,
                        "section": section
                    }
                    state["last_updated"] = datetime.now(timezone.utc).isoformat()
                    
                    # Execute workflow step
                    state = await tool_node.ainvoke({
                        "name": "process_document",
                        "arguments": json.dumps({
                            "document_content": content,
                            "document_type": document_type,
                            "section": section
                        })
                    })
                    
                    # Parse the tool result to get the updated state
                    try:
                        state = json.loads(state.content)
                    except (json.JSONDecodeError, AttributeError):
                        # If result can't be parsed as JSON, use original state
                        logger.error(f"Failed to parse tool result: {state}")
                    
                    # Send updated state
                    await manager.send_message(session_id, {
                        "type": "state_update",
                        "data": state
                    })
                
                elif message["type"] == "save_state":
                    # Save the current state
                    # This could write to a database or storage service
                    # For now, just acknowledge
                    
                    await manager.send_message(session_id, {
                        "type": "save_complete",
                        "data": {
                            "message": "Profile state saved successfully",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    })
                
                elif message["type"] == "ping":
                    # Respond to ping with pong
                    await manager.send_message(session_id, {"type": "pong"})
                
                else:
                    logger.warning(f"Unknown message type received: {message['type']}")
                    await manager.send_message(session_id, {
                        "type": "error",
                        "data": {"message": f"Unknown message type: {message['type']}"}
                    })
                
                # Check if workflow is complete
                if state["status"] == "completed":
                    # Send completion message
                    await manager.send_message(session_id, {
                        "type": "workflow_complete",
                        "data": state
                    })
                    
                    # Get recommendations
                    try:
                        recommendation_service = ServiceFactory.get_recommendation_service()
                        recommendations = await recommendation_service.generate_recommendations(
                            profile_data={"user_id": user_id, **state["profile_data"]}
                        )
                        
                        # Send recommendations
                        await manager.send_message(session_id, {
                            "type": "recommendations",
                            "data": {"recommendations": [rec.dict() for rec in recommendations]}
                        })
                    except Exception as e:
                        logger.error(f"Error generating recommendations: {str(e)}")
                    
                    # Break the loop to end the session
                    break
            
            except ValidationError as e:
                # Send validation error to client
                await manager.send_message(session_id, {
                    "type": "error",
                    "data": {"message": str(e), "code": "validation_error"}
                })
            
            except Exception as e:
                # Log error and send generic error to client
                logger.exception(f"Error processing message: {str(e)}")
                await manager.send_message(session_id, {
                    "type": "error",
                    "data": {"message": "An unexpected error occurred", "code": "server_error"}
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user_id={user_id}, session_id={session_id}")
        if session_id:
            manager.disconnect(session_id)
    except Exception as e:
        logger.exception(f"WebSocket error: {str(e)}")
        # Send error message if possible
        if session_id:
            try:
                await manager.send_message(session_id, {
                    "type": "error",
                    "data": {"message": "An unexpected error occurred", "code": "server_error"}
                })
            except:
                pass
            manager.disconnect(session_id) 