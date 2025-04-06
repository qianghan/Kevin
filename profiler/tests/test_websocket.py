"""
Tests for WebSocket functionality in the Student Profiler.

This module tests:
- WebSocket connection and disconnection
- Message handling
- State updates
- Profile workflow execution
- Error handling
"""

import json
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import WebSocket, WebSocketDisconnect

from app.backend.api.websocket import (
    handle_websocket,
    ConnectionManager,
    manager
)
from app.backend.core.models.state import create_initial_state
from app.backend.core.workflows.profile_workflow import WorkflowConfig


@pytest.mark.asyncio
async def test_connection_manager_connect():
    """Test ConnectionManager.connect method."""
    # Create test objects
    cm = ConnectionManager()
    mock_websocket = AsyncMock(spec=WebSocket)
    
    # Call connect
    session_id = await cm.connect(mock_websocket, "test_user")
    
    # Verify
    assert session_id in cm.active_connections
    assert session_id in cm.workflow_executors
    assert session_id in cm.session_metadata
    assert cm.session_metadata[session_id]["user_id"] == "test_user"
    mock_websocket.accept.assert_called_once()


def test_connection_manager_disconnect():
    """Test ConnectionManager.disconnect method."""
    # Create test objects
    cm = ConnectionManager()
    mock_websocket = MagicMock()
    
    # Setup state
    session_id = "test_session"
    cm.active_connections[session_id] = mock_websocket
    cm.workflow_executors[session_id] = MagicMock()
    cm.session_metadata[session_id] = {"user_id": "test_user"}
    
    # Call disconnect
    cm.disconnect(session_id)
    
    # Verify
    assert session_id not in cm.active_connections
    assert session_id not in cm.workflow_executors
    assert session_id not in cm.session_metadata


@pytest.mark.asyncio
async def test_connection_manager_send_message():
    """Test ConnectionManager.send_message method."""
    # Create test objects
    cm = ConnectionManager()
    mock_websocket = AsyncMock(spec=WebSocket)
    
    # Setup state
    session_id = "test_session"
    cm.active_connections[session_id] = mock_websocket
    
    # Call send_message
    await cm.send_message(session_id, {"type": "test", "data": "test_data"})
    
    # Verify
    mock_websocket.send_json.assert_called_once()
    args, kwargs = mock_websocket.send_json.call_args
    assert args[0]["type"] == "test"
    assert args[0]["data"] == "test_data"
    assert "timestamp" in args[0]


@pytest.mark.asyncio
async def test_connection_manager_send_message_error():
    """Test ConnectionManager.send_message error handling."""
    # Create test objects
    cm = ConnectionManager()
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.send_json.side_effect = Exception("Test error")
    
    # Setup state
    session_id = "test_session"
    cm.active_connections[session_id] = mock_websocket
    
    # Call send_message
    await cm.send_message(session_id, {"type": "test", "data": "test_data"})
    
    # Verify disconnection on error
    assert session_id not in cm.active_connections


@pytest.mark.asyncio
async def test_connection_manager_broadcast():
    """Test ConnectionManager.broadcast method."""
    # Create test objects
    cm = ConnectionManager()
    mock_websocket1 = AsyncMock(spec=WebSocket)
    mock_websocket2 = AsyncMock(spec=WebSocket)
    
    # Setup state
    session_id1 = "test_session1"
    session_id2 = "test_session2"
    cm.active_connections[session_id1] = mock_websocket1
    cm.active_connections[session_id2] = mock_websocket2
    
    # Call broadcast
    await cm.broadcast({"type": "broadcast", "data": "all_clients"})
    
    # Verify both received
    mock_websocket1.send_json.assert_called_once()
    mock_websocket2.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_connection_manager_broadcast_with_exclude():
    """Test ConnectionManager.broadcast with exclude list."""
    # Create test objects
    cm = ConnectionManager()
    mock_websocket1 = AsyncMock(spec=WebSocket)
    mock_websocket2 = AsyncMock(spec=WebSocket)
    
    # Setup state
    session_id1 = "test_session1"
    session_id2 = "test_session2"
    cm.active_connections[session_id1] = mock_websocket1
    cm.active_connections[session_id2] = mock_websocket2
    
    # Call broadcast with exclude
    await cm.broadcast(
        {"type": "broadcast", "data": "selected_clients"},
        exclude=[session_id1]
    )
    
    # Verify only websocket2 received
    mock_websocket1.send_json.assert_not_called()
    mock_websocket2.send_json.assert_called_once()


@pytest.mark.asyncio
async def test_handle_websocket_connection():
    """Test handle_websocket for successful connection."""
    # Create mocks
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.receive_json.side_effect = WebSocketDisconnect()
    
    # Patch manager methods
    with patch("app.backend.api.websocket.manager.connect", return_value="test_session") as mock_connect, \
         patch("app.backend.api.websocket.manager.send_message") as mock_send, \
         patch("app.backend.api.websocket.manager.disconnect") as mock_disconnect, \
         patch("app.backend.api.websocket.create_initial_state", return_value={"sections": {}}):
        
        # Call handle_websocket and expect WebSocketDisconnect
        await handle_websocket(mock_websocket, "test_user")
        
        # Verify connection handling
        mock_connect.assert_called_once_with(mock_websocket, "test_user")
        mock_send.assert_called_once()
        mock_disconnect.assert_called_once_with("test_session")


@pytest.mark.asyncio
async def test_handle_websocket_answer_message():
    """Test handle_websocket for processing an answer message."""
    # Create mocks
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.receive_json.side_effect = [
        {"type": "answer", "data": "Test answer"},
        WebSocketDisconnect()
    ]
    
    mock_executor = AsyncMock()
    mock_executor.arun.return_value = {"status": "updated", "sections": {"academic": {"status": "complete"}}}
    
    # Patch manager methods
    with patch("app.backend.api.websocket.manager.connect", return_value="test_session") as mock_connect, \
         patch("app.backend.api.websocket.manager.send_message") as mock_send, \
         patch("app.backend.api.websocket.manager.disconnect") as mock_disconnect, \
         patch("app.backend.api.websocket.create_initial_state", return_value={"sections": {}}), \
         patch("app.backend.api.websocket.manager.workflow_executors", {"test_session": mock_executor}):
        
        # Call handle_websocket
        await handle_websocket(mock_websocket, "test_user")
        
        # Verify
        mock_connect.assert_called_once()
        assert mock_send.call_count >= 3  # Initial state, processing, and updated state
        mock_executor.arun.assert_called_once()
        assert "current_answer" in mock_executor.arun.call_args[0][0]
        assert mock_executor.arun.call_args[0][0]["current_answer"] == "Test answer"


@pytest.mark.asyncio
async def test_handle_websocket_review_feedback():
    """Test handle_websocket for processing a review_feedback message."""
    # Create mocks
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.receive_json.side_effect = [
        {
            "type": "review_feedback", 
            "data": {
                "section": "academic", 
                "feedback": {"comment": "Looks good"}
            }
        },
        WebSocketDisconnect()
    ]
    
    mock_executor = AsyncMock()
    mock_executor.arun.return_value = {"status": "updated", "sections": {"academic": {"status": "complete"}}}
    
    # Patch manager methods
    with patch("app.backend.api.websocket.manager.connect", return_value="test_session") as mock_connect, \
         patch("app.backend.api.websocket.manager.send_message") as mock_send, \
         patch("app.backend.api.websocket.manager.disconnect") as mock_disconnect, \
         patch("app.backend.api.websocket.create_initial_state", return_value={"sections": {"academic": {"status": "review"}}}), \
         patch("app.backend.api.websocket.manager.workflow_executors", {"test_session": mock_executor}):
        
        # Call handle_websocket
        await handle_websocket(mock_websocket, "test_user")
        
        # Verify
        mock_connect.assert_called_once()
        assert mock_send.call_count >= 3  # Initial state, processing, and updated state
        mock_executor.arun.assert_called_once()
        sections = mock_executor.arun.call_args[0][0]["sections"]
        assert sections["academic"]["comment"] == "Looks good"


@pytest.mark.asyncio
async def test_handle_websocket_timeout():
    """Test handle_websocket timeout handling with ping."""
    # Create mocks
    mock_websocket = AsyncMock(spec=WebSocket)
    # First call times out, second returns message, third disconnects
    mock_websocket.receive_json.side_effect = [
        asyncio.TimeoutError(),
        {"type": "answer", "data": "Test answer"},
        WebSocketDisconnect()
    ]
    
    mock_executor = AsyncMock()
    mock_executor.arun.return_value = {"status": "updated", "sections": {}}
    
    # Patch manager methods
    with patch("app.backend.api.websocket.manager.connect", return_value="test_session") as mock_connect, \
         patch("app.backend.api.websocket.manager.send_message") as mock_send, \
         patch("app.backend.api.websocket.manager.disconnect") as mock_disconnect, \
         patch("app.backend.api.websocket.create_initial_state", return_value={"sections": {}}), \
         patch("app.backend.api.websocket.manager.workflow_executors", {"test_session": mock_executor}):
        
        # Call handle_websocket
        await handle_websocket(mock_websocket, "test_user")
        
        # Verify ping was sent
        ping_call = False
        for call in mock_send.call_args_list:
            args, kwargs = call
            if args[1]["type"] == "ping":
                ping_call = True
                break
        assert ping_call


@pytest.mark.asyncio
async def test_handle_websocket_validation_error():
    """Test handle_websocket with validation error."""
    # Create mocks
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.receive_json.side_effect = [
        {"type": "answer", "wrong_field": "Test answer"},  # Missing 'data'
        WebSocketDisconnect()
    ]
    
    # Patch manager methods
    with patch("app.backend.api.websocket.manager.connect", return_value="test_session") as mock_connect, \
         patch("app.backend.api.websocket.manager.send_message") as mock_send, \
         patch("app.backend.api.websocket.manager.disconnect") as mock_disconnect, \
         patch("app.backend.api.websocket.create_initial_state", return_value={"sections": {}}):
        
        # Call handle_websocket
        await handle_websocket(mock_websocket, "test_user")
        
        # Verify error was sent
        error_sent = False
        for call in mock_send.call_args_list:
            args, kwargs = call
            if args[1]["type"] == "error":
                error_sent = True
                break
        assert error_sent


# UI use case tests
@pytest.mark.asyncio
async def test_ui_profile_building_workflow():
    """Test complete UI workflow for profile building over WebSocket."""
    # Create mocks
    mock_websocket = AsyncMock(spec=WebSocket)
    
    # Sequence of messages simulating user interaction
    mock_websocket.receive_json.side_effect = [
        # Academic section
        {"type": "answer", "data": "I have a 3.9 GPA with honors courses"},
        # Extracurricular section
        {"type": "answer", "data": "I am the president of the debate club"},
        # Personal section
        {"type": "answer", "data": "My goal is to study computer science"},
        # Review feedback
        {"type": "review_feedback", "data": {"section": "academic", "feedback": {"approve": True}}},
        # Disconnect
        WebSocketDisconnect()
    ]
    
    # Create a realistic workflow executor that updates state based on messages
    class MockWorkflowExecutor:
        def __init__(self):
            self.state = {}
            self.step_count = 0
            self.sections = ["academic", "extracurricular", "personal"]
        
        async def arun(self, state):
            self.state = state.copy()
            self.step_count += 1
            
            # Process based on what we received
            if "current_answer" in state:
                # Update current section based on step count
                current_section = self.sections[min(self.step_count - 1, len(self.sections) - 1)]
                
                if current_section not in self.state.get("sections", {}):
                    self.state["sections"] = self.state.get("sections", {})
                    self.state["sections"][current_section] = {}
                
                self.state["sections"][current_section]["content"] = state["current_answer"]
                self.state["sections"][current_section]["status"] = "complete"
                
                # If all sections complete, move to review
                if self.step_count >= len(self.sections):
                    self.state["status"] = "review"
                    self.state["current_section"] = "academic"  # Review first section
            
            # Handle review feedback
            if "sections" in state and any(section.get("approve", False) for section in state["sections"].values()):
                self.state["status"] = "complete"
                self.state["profile_complete"] = True
            
            return self.state
    
    mock_executor = MockWorkflowExecutor()
    
    # Patch manager methods
    with patch("app.backend.api.websocket.manager.connect", return_value="test_session") as mock_connect, \
         patch("app.backend.api.websocket.manager.send_message") as mock_send, \
         patch("app.backend.api.websocket.manager.disconnect") as mock_disconnect, \
         patch("app.backend.api.websocket.create_initial_state", return_value={
             "status": "in_progress",
             "sections": {},
             "current_section": "academic"
         }), \
         patch("app.backend.api.websocket.manager.workflow_executors", {"test_session": mock_executor}):
        
        # Call handle_websocket
        await handle_websocket(mock_websocket, "test_user")
        
        # Verify full workflow
        assert mock_executor.step_count >= 4  # 3 sections + 1 review
        assert mock_send.call_count >= 8  # Initial + at least 2 for each step
        
        # Check sections were completed
        assert "academic" in mock_executor.state["sections"]
        assert "extracurricular" in mock_executor.state["sections"]
        assert "personal" in mock_executor.state["sections"]
        
        # Check for completion state
        assert mock_executor.state.get("profile_complete", False)


@pytest.mark.asyncio
async def test_workflow_config_propagation():
    """Test that workflow configuration is properly propagated."""
    # Create test objects
    cm = ConnectionManager()
    mock_websocket = AsyncMock(spec=WebSocket)
    
    # Patch workflow creation
    with patch("app.backend.api.websocket.create_workflow_executor") as mock_create_workflow:
        # Call connect
        await cm.connect(mock_websocket, "test_user")
        
        # Verify workflow creation
        mock_create_workflow.assert_called_once()
        args, kwargs = mock_create_workflow.call_args
        
        # Verify config was passed
        assert "config" in kwargs
        assert isinstance(kwargs["config"], WorkflowConfig)
        assert "qa_service" in kwargs
        assert "document_service" in kwargs
        assert "recommendation_service" in kwargs 