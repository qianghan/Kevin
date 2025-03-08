"""
Tests for the chat router endpoints.

This module contains tests for the chat router endpoints in the Kevin API.
"""

import json
import pytest
import uuid
from unittest.mock import patch, MagicMock, AsyncMock

# Import fixtures from conftest.py
from .conftest import test_client, mock_agent, mock_conversation_history, mock_streaming


def test_chat_query_success(test_client, mock_agent):
    """Test a successful chat query."""
    # Define a test query
    test_data = {
        "query": "What is the University of British Columbia?",
        "use_web_search": False,
        "conversation_id": None,
        "stream": False
    }
    
    # Make the request
    response = test_client.post("/api/chat/query", json=test_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["answer"] == "This is a test answer"
    assert "thinking_steps" in data
    assert len(data["thinking_steps"]) == 1
    assert "documents" in data
    assert len(data["documents"]) == 1
    assert "conversation_id" in data
    assert "duration_seconds" in data


def test_chat_query_with_web_search(test_client, mock_agent):
    """Test a chat query with web search enabled."""
    # Define a test query with web search
    test_data = {
        "query": "What is the University of British Columbia?",
        "use_web_search": True,
        "conversation_id": None,
        "stream": False
    }
    
    # Make the request
    response = test_client.post("/api/chat/query", json=test_data)
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["answer"] == "This is a test answer"
    
    # Verify that the mock agent's use_web was set to True
    assert mock_agent.use_web == True


def test_chat_query_with_existing_conversation(test_client):
    """Test a chat query with an existing conversation ID."""
    # Generate a test conversation ID
    conversation_id = str(uuid.uuid4())
    
    # Configure process_chat mock without autospec
    with patch('src.api.routers.chat.process_chat') as mock_process_chat:
        # Set up the return value
        mock_process_chat.return_value = (
            "This is a test answer",
            conversation_id,  # Use the same ID we passed
            [{"description": "Test thinking step", "duration": 0.5}],
            [{"content": "Test content", "metadata": {"source": "test"}}],
            0.5
        )
        
        # Define a test query with conversation ID
        test_data = {
            "query": "What is the University of British Columbia?",
            "use_web_search": False,
            "conversation_id": conversation_id,
            "stream": False
        }
        
        # Make the request
        response = test_client.post("/api/chat/query", json=test_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert data["conversation_id"] == conversation_id


def test_chat_query_with_streaming(test_client):
    """Test a chat query with streaming enabled, which should redirect."""
    # Define a test query with streaming
    test_data = {
        "query": "What is the University of British Columbia?",
        "use_web_search": False,
        "conversation_id": None,
        "stream": True
    }
    
    # Make the request with follow_redirects=False
    response = test_client.post("/api/chat/query", json=test_data)
    
    # Check for redirect response (HTTP 307)
    assert response.status_code == 307
    assert "location" in response.headers
    assert "/api/chat/query/stream?query=" in response.headers["location"]


@pytest.mark.asyncio
async def test_chat_query_stream(test_client):
    """Test the streaming chat query endpoint."""
    # Apply patches directly at the chat_query_stream function to ensure they're called
    with patch('src.api.routers.chat.StreamManager') as MockManager, \
         patch('src.api.routers.chat.StreamCallbackHandler') as MockHandler, \
         patch('src.api.routers.chat.SyncToAsyncAdapter') as MockAdapter:
        
        # Configure the mock StreamManager
        mock_manager = MagicMock()
        
        async def mock_get_stream():
            yield "event: thinking_start\n"
            yield f'data: {{"query": "Test query"}}\n\n'
            yield "event: answer_start\n"
            yield "data: {}\n\n"
            yield "event: answer_chunk\n" 
            yield f'data: {{"chunk": "This is a test"}}\n\n'
            yield "event: done\n"
            yield f'data: {{"conversation_id": "test-id", "duration_seconds": 0.5}}\n\n'
        
        mock_manager.get_stream.return_value = mock_get_stream()
        MockManager.return_value = mock_manager
        
        # Configure the mock adapter
        mock_adapter = MagicMock()
        MockAdapter.return_value = mock_adapter
        
        # Configure the mock handler
        mock_handler = MagicMock()
        MockHandler.return_value = mock_handler
        
        # Make the request
        response = test_client.get("/api/chat/query/stream?query=What%20is%20UBC?")
        
        # Check response
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        
        # Verify that the adapter's run_in_background method was called
        # This checks that MockAdapter was not only instantiated but its method was called
        assert MockAdapter.return_value.run_in_background.called


def test_get_conversation_success(test_client):
    """Test retrieving a conversation by ID."""
    # Create a mock for the conversation history
    with patch('src.api.routers.chat.get_conversation_history') as mock_get_history:
        # Configure the mock to return a sample conversation history
        conversation_history = [
            {
                "role": "user",
                "content": "What is UBC?",
                "timestamp": 1600000000.0
            },
            {
                "role": "assistant",
                "content": "UBC is a university in Vancouver, Canada.",
                "timestamp": 1600000010.0,
                "thinking_steps": [
                    {
                        "description": "Thinking about the query",
                        "duration": 0.5
                    }
                ]
            }
        ]
        mock_get_history.return_value = conversation_history
        
        # Make the request
        conversation_id = "test-conversation-id"
        response = test_client.get(f"/api/chat/conversations/{conversation_id}")
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert data["conversation_id"] == conversation_id
        assert "messages" in data
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"


def test_get_conversation_not_found(test_client):
    """Test retrieving a non-existent conversation."""
    # Use patch to mock get_conversation_history
    with patch('src.api.services.chat.get_conversation_history') as mock_get_history:
        # Configure the mock to return an empty list (conversation not found)
        mock_get_history.return_value = []
        
        # Make the request
        conversation_id = "non-existent-id"
        response = test_client.get(f"/api/chat/conversations/{conversation_id}")
        
        # Check response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()


def test_chat_query_error(test_client):
    """Test handling of errors in chat query."""
    with patch('src.api.routers.chat.process_chat') as mock_process_chat:
        # Configure the mock to raise an exception with a clear message
        mock_process_chat.side_effect = Exception("Test error")
        
        # Define a test query
        test_data = {
            "query": "What is the University of British Columbia?", 
            "use_web_search": False,
            "conversation_id": None,
            "stream": False
        }
        
        # Make the request
        response = test_client.post("/api/chat/query", json=test_data)
        
        # Check response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Test error" in data["detail"] 