"""
Tests for WebSocket functionality in the Student Profiler.

This module tests the WebSocket endpoints for:
- Connection establishment
- Message handling
- Session state management
- Error handling
"""

import json
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from profiler.app.backend.api.main import app as fastapi_app


# Test WebSocket connection
def test_websocket_connect(client: TestClient):
    """Test establishing a WebSocket connection."""
    with client.websocket_connect("/ws/profile?user_id=test_user") as websocket:
        # Connection should be established
        data = websocket.receive_json()
        assert data["type"] == "connection_established"
        assert "session_id" in data
        assert data["user_id"] == "test_user"


def test_websocket_connect_missing_user_id(client: TestClient):
    """Test that WebSocket connection requires user_id parameter."""
    # Should fail to connect without user_id
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws/profile") as websocket:
            websocket.receive_text()
    
    assert excinfo.value.code == 1008  # Policy violation


# Test WebSocket authentication
def test_websocket_authentication(client: TestClient):
    """Test that WebSocket connections require API key authentication."""
    # Without API key
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws/profile?user_id=test_user") as websocket:
            websocket.receive_text()
    
    # With invalid API key
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            "/ws/profile?user_id=test_user",
            headers={"X-API-Key": "invalid_key"}
        ) as websocket:
            websocket.receive_text()
    
    # With valid API key
    with client.websocket_connect(
        "/ws/profile?user_id=test_user",
        headers={"X-API-Key": "test_api_key"}  # Set in fixture
    ) as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connection_established"


# Test message sending and receiving
@pytest.mark.parametrize(
    "message_type,message_data,expected_type",
    [
        ("question", {"text": "What are your academic achievements?"}, "response"),
        ("update_section", {"section": "academic", "data": {"gpa": 3.8}}, "section_updated"),
        ("request_recommendations", {"section": "academic"}, "recommendations"),
    ],
)
def test_websocket_messages(client: TestClient, message_type, message_data, expected_type):
    """Test sending different types of messages over WebSocket."""
    # Connect to WebSocket
    with client.websocket_connect(
        "/ws/profile?user_id=test_user",
        headers={"X-API-Key": "test_api_key"}
    ) as websocket:
        # Skip the connection established message
        websocket.receive_json()
        
        # Send message
        message = {
            "type": message_type,
            "data": message_data
        }
        websocket.send_json(message)
        
        # Receive response
        response = websocket.receive_json()
        assert response["type"] == expected_type


# Test error handling
def test_websocket_error_handling(client: TestClient):
    """Test handling of errors in WebSocket communication."""
    with client.websocket_connect(
        "/ws/profile?user_id=test_user",
        headers={"X-API-Key": "test_api_key"}
    ) as websocket:
        # Skip the connection established message
        websocket.receive_json()
        
        # Send invalid message type
        websocket.send_json({
            "type": "invalid_type",
            "data": {"some": "data"}
        })
        
        # Should receive error response
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "message" in response


# Test state management
def test_websocket_state_persistence(client: TestClient):
    """Test that state is maintained across messages in a WebSocket session."""
    with client.websocket_connect(
        "/ws/profile?user_id=test_user",
        headers={"X-API-Key": "test_api_key"}
    ) as websocket:
        # Skip the connection established message
        initial_msg = websocket.receive_json()
        session_id = initial_msg["session_id"]
        
        # Update academic section
        websocket.send_json({
            "type": "update_section",
            "data": {
                "section": "academic",
                "data": {"gpa": 3.9, "courses": ["Math", "Physics"]}
            }
        })
        
        # Get update confirmation
        update_response = websocket.receive_json()
        assert update_response["type"] == "section_updated"
        
        # Request profile data
        websocket.send_json({
            "type": "get_profile",
            "data": {}
        })
        
        # Receive profile with updated data
        profile_response = websocket.receive_json()
        assert profile_response["type"] == "profile"
        assert "academic" in profile_response["data"]
        assert profile_response["data"]["academic"]["gpa"] == 3.9


# Test concurrent connections
@pytest.mark.asyncio
async def test_multiple_websocket_connections(client: TestClient):
    """Test handling multiple WebSocket connections simultaneously."""
    async def connect_and_interact(user_id):
        with client.websocket_connect(
            f"/ws/profile?user_id={user_id}",
            headers={"X-API-Key": "test_api_key"}
        ) as websocket:
            # Skip connection message
            initial_msg = websocket.receive_json()
            assert initial_msg["user_id"] == user_id
            
            # Send a message
            websocket.send_json({
                "type": "question",
                "data": {"text": f"Question from {user_id}"}
            })
            
            # Get response
            response = websocket.receive_json()
            assert response["type"] == "response"
            
            return initial_msg["session_id"]
    
    # Connect with 3 different users
    session_ids = await asyncio.gather(
        connect_and_interact("user1"),
        connect_and_interact("user2"),
        connect_and_interact("user3")
    )
    
    # Ensure each got a different session
    assert len(set(session_ids)) == 3


# Test WebSocket disconnection
def test_websocket_disconnection_handling(client: TestClient):
    """Test proper handling of WebSocket disconnection."""
    # This test simulates a client disconnecting and reconnecting
    
    # First connection to establish a session
    with client.websocket_connect(
        "/ws/profile?user_id=test_user",
        headers={"X-API-Key": "test_api_key"}
    ) as websocket:
        initial_msg = websocket.receive_json()
        session_id = initial_msg["session_id"]
        
        # Update state
        websocket.send_json({
            "type": "update_section",
            "data": {
                "section": "academic",
                "data": {"gpa": 4.0}
            }
        })
        websocket.receive_json()  # Consume response
    
    # Reconnect with same user_id
    with client.websocket_connect(
        "/ws/profile?user_id=test_user",
        headers={"X-API-Key": "test_api_key"}
    ) as websocket:
        new_initial_msg = websocket.receive_json()
        new_session_id = new_initial_msg["session_id"]
        
        # Session ID should be different
        assert new_session_id != session_id
        
        # But state should be loaded
        websocket.send_json({
            "type": "get_profile",
            "data": {}
        })
        
        profile_response = websocket.receive_json()
        assert profile_response["type"] == "profile"
        
        # Check if academic data was preserved
        if "academic" in profile_response["data"]:
            assert profile_response["data"]["academic"]["gpa"] == 4.0 