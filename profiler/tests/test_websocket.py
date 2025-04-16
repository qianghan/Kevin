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
import time
from unittest.mock import patch, MagicMock, AsyncMock, ANY
from fastapi import WebSocket, WebSocketDisconnect, status
from datetime import datetime, timezone

from app.backend.api.websocket import (
    ConnectionManager,
    router,
    websocket_endpoint
)
from app.backend.core.models.state import create_initial_state
from app.backend.core.workflows.profile_workflow import WorkflowConfig
from app.backend.api.main import VALID_API_KEYS


@pytest.mark.asyncio
async def test_connection_manager_connect():
    """Test the connection manager's connect method."""
    manager = ConnectionManager()
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.client = MagicMock()
    mock_websocket.client.host = "127.0.0.1"
    
    user_id = "test-user"
    session_id = await manager.connect(mock_websocket, user_id)
    
    assert session_id in manager.active_connections
    assert manager.active_connections[session_id] == mock_websocket
    assert manager.session_metadata[session_id]["user_id"] == user_id


@pytest.mark.asyncio
async def test_connection_manager_disconnect():
    """Test the connection manager's disconnect method."""
    manager = ConnectionManager()
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.client = MagicMock()
    mock_websocket.client.host = "127.0.0.1"
    
    user_id = "test-user"
    session_id = await manager.connect(mock_websocket, user_id)
    manager.disconnect(session_id)
    
    assert session_id not in manager.active_connections


@pytest.mark.asyncio
async def test_connection_manager_send_message():
    """Test sending messages through the connection manager."""
    manager = ConnectionManager()
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.client = MagicMock()
    mock_websocket.client.host = "127.0.0.1"
    
    user_id = "test-user"
    test_message = {"type": "test", "content": "test message"}
    
    session_id = await manager.connect(mock_websocket, user_id)
    await manager.send_message(session_id, test_message)
    
    mock_websocket.send_json.assert_called_with(test_message)


@pytest.mark.asyncio
async def test_connection_manager_receive_message():
    """Test receiving messages through the connection manager."""
    manager = ConnectionManager()
    mock_websocket = AsyncMock()
    session_id = "test_session"
    
    # Initialize required components
    manager.active_connections[session_id] = mock_websocket
    manager.workflow_executors[session_id] = AsyncMock()
    manager.message_router = MagicMock()
    manager.message_router.route_message = AsyncMock()
    
    # Initialize session metadata (required by receive_message)
    manager.session_metadata[session_id] = {
        "user_id": "test-user",
        "connected_at": datetime.now(timezone.utc).isoformat(),
        "last_activity": datetime.now(timezone.utc).isoformat(),
        "client_info": {
            "ip": "127.0.0.1"
        }
    }

    # Test valid JSON message (will route to message router)
    test_message = {"type": "test", "data": "test_data"}
    message_str = json.dumps(test_message)
    
    # Add timeout to prevent hanging
    try:
        await asyncio.wait_for(manager.receive_message(message_str, mock_websocket), timeout=2.0)
    except asyncio.TimeoutError:
        pytest.fail("receive_message timed out")
    
    # Verify message was routed to message_router
    manager.message_router.route_message.assert_called_once_with(test_message, mock_websocket)
    
    # Reset mocks
    mock_websocket.reset_mock()
    manager.message_router.route_message.reset_mock()

    # Test invalid JSON message
    invalid_message = "invalid json"
    
    # Just verify no exceptions are raised for invalid JSON
    try:
        await asyncio.wait_for(manager.receive_message(invalid_message, mock_websocket), timeout=2.0)
    except asyncio.TimeoutError:
        pytest.fail("receive_message with invalid JSON timed out")
    except Exception as e:
        pytest.fail(f"Invalid JSON handling raised an exception: {e}")
    
    # Verify the route_message was not called for invalid JSON
    manager.message_router.route_message.assert_not_called()
    
    # Create a new manager for the invalid session test
    new_manager = ConnectionManager()
    new_manager.message_router = MagicMock()
    new_manager.message_router.route_message = AsyncMock()
    
    # Test message with invalid session
    invalid_session_socket = AsyncMock()
    test_message = {"type": "test", "data": "test_data"}
    message_str = json.dumps(test_message)
    
    try:
        await asyncio.wait_for(new_manager.receive_message(message_str, invalid_session_socket), timeout=2.0)
    except asyncio.TimeoutError:
        pytest.fail("receive_message with invalid session timed out")
    
    # No routing should happen for invalid session
    new_manager.message_router.route_message.assert_not_called()


@pytest.mark.asyncio
async def test_handle_websocket_connection():
    """Test the WebSocket connection handler."""
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.client = MagicMock()
    mock_websocket.client.host = "127.0.0.1"
    mock_websocket.query_params = {"x-api-key": "test-key-123"}
    
    # Mock the connection_manager to avoid actual connections
    with patch('app.backend.api.websocket.ConnectionManager.connect') as mock_connect, \
         patch('app.backend.api.main.VALID_API_KEYS', ["test-key-123"]):
        # Setup mock session ID return
        session_id = "test-session-id"
        mock_connect.return_value = session_id
        
        # Mock receive_json to return a sequence of messages then disconnect
        mock_websocket.receive_json.side_effect = [
            {"type": "test", "data": "test message"},
            WebSocketDisconnect()
        ]
        
        # Call the endpoint with a timeout
        try:
            await asyncio.wait_for(websocket_endpoint(mock_websocket, "test-user"), timeout=2.0)
        except WebSocketDisconnect:
            # Expected when we simulate disconnect
            pass
        except asyncio.TimeoutError:
            pytest.fail("websocket_endpoint timed out")
        
        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()
        mock_connect.assert_called_once()


@pytest.mark.asyncio
async def test_handle_websocket_invalid_message():
    """Test handling invalid messages in the WebSocket connection."""
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.client = MagicMock()
    mock_websocket.client.host = "127.0.0.1"
    mock_websocket.query_params = {"x-api-key": "test-key"}
    mock_websocket.receive_json.side_effect = [
        {"type": "invalid"},  # Invalid message type
        WebSocketDisconnect()
    ]
    
    # Call the endpoint
    with pytest.raises(WebSocketDisconnect):
        await websocket_endpoint(mock_websocket, "test-user")


@pytest.mark.asyncio
async def test_connection_manager_broadcast():
    """Test ConnectionManager.broadcast method."""
    manager = ConnectionManager()
    mock_websocket1 = AsyncMock(spec=WebSocket)
    mock_websocket2 = AsyncMock(spec=WebSocket)
    mock_websocket1.client = MagicMock()
    mock_websocket2.client = MagicMock()
    mock_websocket1.client.host = "127.0.0.1"
    mock_websocket2.client.host = "127.0.0.1"
    
    # Connect two clients
    session_id1 = await manager.connect(mock_websocket1, "user1")
    session_id2 = await manager.connect(mock_websocket2, "user2")
    
    # Broadcast a message
    test_message = {"type": "broadcast", "data": "all_clients"}
    await manager.broadcast(test_message)
    
    # Verify both received the message
    mock_websocket1.send_json.assert_called_with(test_message)
    mock_websocket2.send_json.assert_called_with(test_message)


@pytest.mark.asyncio
async def test_connection_manager_broadcast_with_exclude():
    """Test ConnectionManager.broadcast with exclude list."""
    manager = ConnectionManager()
    mock_websocket1 = AsyncMock(spec=WebSocket)
    mock_websocket2 = AsyncMock(spec=WebSocket)
    mock_websocket1.client = MagicMock()
    mock_websocket2.client = MagicMock()
    mock_websocket1.client.host = "127.0.0.1"
    mock_websocket2.client.host = "127.0.0.1"
    
    # Connect two clients
    session_id1 = await manager.connect(mock_websocket1, "user1")
    session_id2 = await manager.connect(mock_websocket2, "user2")
    
    # Broadcast with exclude
    test_message = {"type": "broadcast", "data": "selected_clients"}
    await manager.broadcast(test_message, exclude=[session_id1])
    
    # Verify only websocket2 received
    mock_websocket1.send_json.assert_not_called()
    mock_websocket2.send_json.assert_called_with(test_message)


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
        await websocket_endpoint(mock_websocket, "test_user")
        
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
        await websocket_endpoint(mock_websocket, "test_user")
        
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
        await websocket_endpoint(mock_websocket, "test_user")
        
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
        await websocket_endpoint(mock_websocket, "test_user")
        
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
        await websocket_endpoint(mock_websocket, "test_user")
        
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


@pytest.mark.asyncio
async def test_websocket_endpoint():
    """Test the WebSocket endpoint."""
    # Create mocks
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.receive_json.side_effect = WebSocketDisconnect()
    
    # Patch manager methods
    with patch("app.backend.api.websocket.ConnectionManager") as mock_manager_class, \
         patch("app.backend.api.websocket.create_initial_state", return_value={"sections": {}}):
        
        # Setup mock manager
        mock_manager = AsyncMock()
        mock_manager_class.return_value = mock_manager
        mock_manager.connect.return_value = "test_session"
        
        # Get the WebSocket endpoint
        endpoint = router.routes[0].endpoint
        
        # Call the endpoint
        await endpoint(mock_websocket, "test_user")
        
        # Verify connection handling
        mock_manager.connect.assert_called_once_with(mock_websocket, "test_user")
        mock_manager.send_message.assert_called_once()
        mock_manager.disconnect.assert_called_once_with("test_session")


@pytest.mark.asyncio
async def test_websocket_api_key_validation():
    """Test WebSocket connection with API key validation."""
    from app.backend.api.main import websocket_endpoint as main_websocket_endpoint
    
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.client = MagicMock()
    mock_websocket.client.host = "127.0.0.1"
    
    # Test with valid API key
    with patch('app.backend.api.main.VALID_API_KEYS', ["test-key-123"]):
        mock_websocket.query_params = {"x-api-key": "test-key-123"}
        
        # Mock the connection_manager
        with patch('app.backend.api.main.manager.connect') as mock_connect:
            # Setup mock session ID return
            session_id = "test-session-id"
            mock_connect.return_value = session_id
            
            # Mock receive_text to end test after one message
            mock_websocket.receive_text.side_effect = WebSocketDisconnect
            
            try:
                await asyncio.wait_for(main_websocket_endpoint(mock_websocket, "test-user"), timeout=2.0)
            except WebSocketDisconnect:
                pass  # Expected
            
            # Verify connection was accepted
            mock_websocket.accept.assert_called_once()
    
    # Reset mock
    mock_websocket.reset_mock()
    
    # Test with invalid API key
    with patch('app.backend.api.main.VALID_API_KEYS', ["test-key-123"]):
        mock_websocket.query_params = {"x-api-key": "invalid-key"}
        try:
            await asyncio.wait_for(main_websocket_endpoint(mock_websocket, "test-user"), timeout=2.0)
        except WebSocketDisconnect:
            pass  # Expected
        mock_websocket.accept.assert_not_called()
    
    # Test without API key
    mock_websocket.reset_mock()
    with patch('app.backend.api.main.VALID_API_KEYS', ["test-key-123"]):
        mock_websocket.query_params = {}
        try:
            await asyncio.wait_for(main_websocket_endpoint(mock_websocket, "test-user"), timeout=2.0)
        except WebSocketDisconnect:
            pass  # Expected
        mock_websocket.accept.assert_not_called()


@pytest.mark.asyncio
async def test_connection_manager_message_validation():
    """Test message validation in the connection manager."""
    manager = ConnectionManager()
    mock_websocket = AsyncMock(spec=WebSocket)
    mock_websocket.client = MagicMock()
    mock_websocket.client.host = "127.0.0.1"
    
    session_id = await manager.connect(mock_websocket, "test-user")
    
    # Test valid message structure
    valid_message = {
        "type": "test",
        "data": {"key": "value"},
        "timestamp": "2025-04-13T00:00:00Z"
    }
    await manager.send_message(session_id, valid_message)
    mock_websocket.send_json.assert_called_with(valid_message)
    
    # Test message with missing required fields
    invalid_message = {"data": "test"}
    with pytest.raises(ValueError):
        await manager.send_message(session_id, invalid_message)
    
    # Test message with invalid type
    invalid_type_message = {
        "type": 123,  # Should be string
        "data": "test"
    }
    with pytest.raises(ValueError):
        await manager.send_message(session_id, invalid_type_message)


@pytest.mark.asyncio
async def test_connection_manager_concurrent_connections():
    """Test handling multiple concurrent WebSocket connections."""
    manager = ConnectionManager()
    num_connections = 5
    mock_websockets = []
    session_ids = []
    
    # Create multiple connections
    for i in range(num_connections):
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.client = MagicMock()
        mock_ws.client.host = f"127.0.0.1"
        mock_websockets.append(mock_ws)
        
        user_id = f"test-user-{i}"
        session_id = await manager.connect(mock_ws, user_id)
        session_ids.append(session_id)
    
    # Verify all connections are active
    assert len(manager.active_connections) == num_connections
    
    # Test broadcasting to all connections
    test_message = {"type": "broadcast", "data": "test"}
    await manager.broadcast(test_message)
    
    # Verify all websockets received the message
    for mock_ws in mock_websockets:
        mock_ws.send_json.assert_called_with(test_message)
    
    # Disconnect half of the connections
    for session_id in session_ids[:num_connections//2]:
        manager.disconnect(session_id)
    
    # Verify correct number of connections remain
    assert len(manager.active_connections) == num_connections - num_connections//2
    
    # Test broadcasting after disconnections
    test_message_2 = {"type": "broadcast", "data": "test2"}
    await manager.broadcast(test_message_2)
    
    # Verify only connected websockets received the message
    for mock_ws in mock_websockets[num_connections//2:]:
        mock_ws.send_json.assert_called_with(test_message_2) 