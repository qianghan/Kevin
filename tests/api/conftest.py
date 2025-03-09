"""
Pytest fixtures for API testing.

This module provides fixtures for testing the Kevin API.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

# Set up all necessary mocks BEFORE imports
# Create mock for core modules
sys.modules['src.core.agent'] = MagicMock()
sys.modules['src.core.agent'].UniversityAgent = MagicMock

# Create mock for vectorstore
sys.modules['src.core.vectorstore'] = MagicMock()
sys.modules['src.core.vectorstore'].get_vectorstore = MagicMock()

# Create mock for web search
sys.modules['src.core.web_search'] = MagicMock()
sys.modules['src.core.web_search'].web_search = MagicMock()

# Add the project root to Python path
from pathlib import Path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import FastAPI TestClient
from fastapi.testclient import TestClient

# Import app with proper patching
with patch.multiple(
    'src.core.agent',
    UniversityAgent=MagicMock()
), patch.multiple(
    'src.core.vectorstore',
    get_vectorstore=MagicMock()
), patch.multiple(
    'src.core.web_search',
    web_search=MagicMock()
):
    from src.api.app import app


@pytest.fixture
def test_client():
    """
    Create a test client for the FastAPI application.
    
    This fixture provides a TestClient that can be used to make
    requests to the API endpoints without starting a server.
    """
    with TestClient(app) as client:
        client.follow_redirects = False  # Disable automatic redirect following
        yield client


@pytest.fixture
def mock_agent():
    """
    Create a mock agent for testing.
    
    This fixture provides a mock UniversityAgent that returns
    predefined responses for testing without using actual LLM calls.
    """
    with patch('src.api.services.chat.get_agent', autospec=True) as mock_get_agent:
        # Create a mock agent
        mock_agent = MagicMock()
        
        # Configure the mock agent to return a sample response
        mock_response = {
            "answer": "This is a test answer",
            "thinking_steps": [
                {
                    "description": "Thinking about the query",
                    "duration": 0.5,
                    "result": "Some result"
                }
            ],
            "documents": [
                {
                    "content": "Test document content",
                    "metadata": {
                        "source": "test_source",
                        "title": "Test Document"
                    }
                }
            ]
        }
        mock_agent.query.return_value = mock_response
        mock_agent.use_web = False
        mock_agent.last_answer = "This is a test answer"
        mock_agent.set_thinking_step_callback = MagicMock()
        
        # Ensure get_agent returns our mock
        mock_get_agent.return_value = mock_agent
        
        # Make sure process_chat doesn't actually run code
        with patch('src.api.services.chat.process_chat', autospec=True) as mock_process_chat:
            # Set up the mock to return a valid chat response
            mock_process_chat.return_value = (
                "This is a test answer",
                "test-conversation-id",
                mock_response["thinking_steps"],
                mock_response["documents"],
                0.5
            )
            yield mock_agent


@pytest.fixture
def mock_search():
    """
    Create a mock for search functionality.
    
    This fixture provides mocks for search_documents and search_web
    functions to avoid making actual search requests during testing.
    """
    # Create patch for the vector store and web search module imports
    with patch('src.api.services.search.search_documents', autospec=True) as mock_search_docs, \
         patch('src.api.services.search.search_web', autospec=True) as mock_search_web:
        
        # Configure mock search_documents
        mock_docs = [
            {
                "id": "doc1",
                "content": "Test document content 1",
                "metadata": {
                    "source": "test_source_1",
                    "title": "Test Document 1"
                }
            },
            {
                "id": "doc2",
                "content": "Test document content 2",
                "metadata": {
                    "source": "test_source_2",
                    "title": "Test Document 2"
                }
            }
        ]
        mock_search_docs.return_value = mock_docs
        
        # Configure mock search_web
        mock_web_docs = [
            {
                "id": "web1",
                "content": "Test web content 1",
                "metadata": {
                    "source": "test_web_source_1",
                    "title": "Test Web Page 1"
                }
            }
        ]
        mock_search_web.return_value = mock_web_docs
        
        yield (mock_search_docs, mock_search_web)


@pytest.fixture
def mock_documents():
    """
    Create a mock for document services.
    
    This fixture provides mocks for get_document and get_document_by_url
    functions to avoid making actual document retrieval requests during testing.
    """
    with patch('src.api.services.documents.get_document', autospec=True) as mock_get_doc, \
         patch('src.api.services.documents.get_document_by_url', autospec=True) as mock_get_doc_url, \
         patch('src.api.services.documents.cache_document', autospec=True) as mock_cache_doc, \
         patch('src.api.services.documents.clear_document_cache', autospec=True) as mock_clear_cache:
        
        # Configure mock get_document
        doc1 = {
            "id": "doc1",
            "content": "Test document content 1",
            "metadata": {
                "source": "test_source_1",
                "title": "Test Document 1"
            }
        }
        mock_get_doc.return_value = doc1
        
        # Configure mock get_document_by_url
        doc2 = {
            "id": "doc2",
            "content": "Test document content 2",
            "metadata": {
                "source": "https://example.com",
                "title": "Test Document 2"
            }
        }
        mock_get_doc_url.return_value = doc2
        
        # Configure mock cache_document
        mock_cache_doc.return_value = "doc3"
        
        # Configure mock clear_document_cache
        mock_clear_cache.return_value = 5
        
        # Set up error cases for testing
        mock_get_doc.side_effect = None  # Reset any previous side effects
        mock_get_doc_url.side_effect = None  # Reset any previous side effects
        
        yield (mock_get_doc, mock_get_doc_url, mock_cache_doc, mock_clear_cache)


@pytest.fixture
def mock_admin():
    """
    Create a mock for admin services.
    
    This fixture provides mocks for admin functions to avoid
    making actual administrative changes during testing.
    """
    with patch('src.api.services.admin.rebuild_index', autospec=True) as mock_rebuild, \
         patch('src.api.services.admin.clear_caches', autospec=True) as mock_clear, \
         patch('src.api.services.admin.get_system_status', autospec=True) as mock_status:
        
        # Configure mock rebuild_index
        mock_rebuild.return_value = {
            "message": "Index rebuilt successfully",
            "details": {
                "duration_seconds": 0.5
            }
        }
        
        # Configure mock clear_caches
        mock_clear.return_value = {
            "message": "Caches cleared successfully",
            "details": {
                "documents_cleared": 5,
                "agent_cache_cleared": True
            }
        }
        
        # Configure mock get_system_status
        mock_status.return_value = {
            "message": "System status retrieved",
            "details": {
                "cpu_usage": 10.5,
                "memory_usage": 50.2,
                "disk_usage": 30.8,
                "python_version": "3.9.0",
                "system": "darwin"
            }
        }
        
        yield (mock_rebuild, mock_clear, mock_status)


@pytest.fixture
def mock_conversation_history():
    """
    Create a mock for conversation history.
    
    This fixture provides a mock for the conversation history
    function to test conversation-related endpoints.
    """
    with patch('src.api.services.chat.get_conversation_history', autospec=True) as mock_history:
        # Sample conversation history
        conversation = [
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
        
        # Configure the mock to return the sample conversation by default
        mock_history.return_value = conversation
        
        yield mock_history


@pytest.fixture
def mock_streaming():
    """
    Create mocks for streaming functionality.
    
    This fixture provides mocks for the streaming classes
    to test streaming endpoints without actual streaming.
    """
    with patch('src.api.services.streaming.StreamManager', autospec=True) as mock_manager_class, \
         patch('src.api.services.streaming.StreamCallbackHandler', autospec=True) as mock_handler_class, \
         patch('src.api.services.streaming.SyncToAsyncAdapter', autospec=True) as mock_adapter_class:
        
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
        mock_manager.add_event = AsyncMock()
        mock_manager_class.return_value = mock_manager
        
        # Configure the mock StreamCallbackHandler
        mock_handler = MagicMock()
        mock_handler_class.return_value = mock_handler
        
        # Configure the mock SyncToAsyncAdapter
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter
        
        yield (mock_manager, mock_handler, mock_adapter) 