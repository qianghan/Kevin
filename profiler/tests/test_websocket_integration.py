import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from app.backend.api.main import app
from app.backend.api.websocket import ConnectionManager
from app.backend.services.interfaces import IDocumentService, IRecommendationService, IQAService
from app.backend.services.mock_services import MockDocumentService, MockRecommendationService, MockQAService

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_services():
    return {
        'document': MockDocumentService(),
        'recommendation': MockRecommendationService(),
        'qa': MockQAService()
    }

@pytest.fixture
def manager():
    return ConnectionManager()

@pytest.mark.asyncio
async def test_websocket_authentication(client, manager):
    """Test WebSocket authentication with API key"""
    # Connect with valid API key
    with client.websocket_connect("/ws/test-user-1?x-api-key=test-key-123") as websocket:
        # Receive welcome message
        data = websocket.receive_json()
        assert data["type"] == "connected"
        assert "Successfully connected" in data["message"]

    # Connect with invalid API key
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/test-user-1?x-api-key=invalid-key") as websocket:
            pass

@pytest.mark.asyncio
async def test_websocket_message_flow(client, manager, mock_services):
    """Test complete message flow through services"""
    with client.websocket_connect("/ws/test-user-1?x-api-key=test-key-123") as websocket:
        # Send document analysis request
        websocket.send_json({
            "type": "analyze_document",
            "data": {
                "document_id": "doc1",
                "content": "Test document content"
            }
        })
        
        # Receive analysis result
        response = websocket.receive_json()
        assert response["type"] == "document_analysis"
        assert "summary" in response["data"]
        
        # Send QA request
        websocket.send_json({
            "type": "ask_question",
            "data": {
                "question": "What is the main topic?"
            }
        })
        
        # Receive QA response
        response = websocket.receive_json()
        assert response["type"] == "qa_response"
        assert "answer" in response["data"]
        
        # Send recommendation request
        websocket.send_json({
            "type": "get_recommendations",
            "data": {
                "context": "Test context"
            }
        })
        
        # Receive recommendations
        response = websocket.receive_json()
        assert response["type"] == "recommendations"
        assert "suggestions" in response["data"]

@pytest.mark.asyncio
async def test_websocket_error_handling(client, manager):
    """Test WebSocket error handling"""
    with client.websocket_connect("/ws/test-user-1?x-api-key=test-key-123") as websocket:
        # Send invalid message
        websocket.send_json({
            "type": "invalid_type",
            "data": {}
        })
        
        # Receive error response
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "error" in response

@pytest.mark.asyncio
async def test_websocket_reconnection(client, manager):
    """Test WebSocket reconnection handling"""
    with client.websocket_connect("/ws/test-user-1?x-api-key=test-key-123") as websocket:
        # Simulate connection drop
        websocket.close()
        
        # Attempt to send message after disconnection
        with pytest.raises(Exception):
            websocket.send_json({
                "type": "test",
                "data": {}
            }) 