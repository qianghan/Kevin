"""
Unit tests for the chat API with semantic cache integration.

These tests verify that the chat API correctly uses the semantic cache.
"""

import unittest
import time
import json
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from starlette.responses import StreamingResponse

from src.api.app import create_app
from src.api.routers.chat import process_chat
from src.api.services.streaming import StreamCallbackHandler
from src.api.services.cache.cache_service import add_to_cache, get_from_cache, clear_semantic_cache


class TestChatAPI(unittest.TestCase):
    """Tests for the chat API with semantic cache integration"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a test app
        self.app = create_app()
        self.client = TestClient(self.app)
        
        # Test data
        self.test_query = "What is the admission process for University of Toronto?"
        self.similar_query = "How do I apply to University of Toronto?"
        
        self.test_response = {
            "answer": "The admission process involves submitting your application online...",
            "thinking_steps": [{"step": 1, "content": "First I'll look up the admission requirements."}],
            "documents": [{"title": "Admissions", "url": "example.com/admissions"}],
            "duration_seconds": 1.5
        }
        
        # Clear cache at the start
        clear_semantic_cache()
    
    def tearDown(self):
        """Clean up test environment"""
        clear_semantic_cache()
    
    @patch('src.api.routers.chat.process_chat')
    def test_chat_query_with_cache(self, mock_process_chat):
        """Test /api/chat/query endpoint"""
        # Mock process_chat to return a successful response
        mock_process_chat.return_value = (
            self.test_response["answer"],
            "test-conversation-id",
            self.test_response["thinking_steps"],
            self.test_response["documents"],
            self.test_response["duration_seconds"]
        )
        
        # Send request
        response = self.client.post(
            "/api/chat/query",
            json={"query": self.test_query, "stream": False}
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["answer"], self.test_response["answer"])
        
        # Verify process_chat was called
        mock_process_chat.assert_called_once()
    
    @patch('src.api.services.chat.get_from_cache')
    @patch('src.api.services.streaming.StreamCallbackHandler')
    @patch('src.api.services.streaming.StreamManager.get_stream')
    def test_chat_query_stream_with_cache(self, mock_get_stream, MockCallbackHandler, mock_get_from_cache):
        """Test streaming endpoint with cache hit"""
        # Mock cache behavior for a hit
        mock_get_from_cache.return_value = self.test_response
        
        # Mock callback handler
        mock_handler = MagicMock()
        MockCallbackHandler.return_value = mock_handler
        
        # Mock the stream generator to return a simple event
        async def mock_stream_generator():
            yield "data: {}\n\n"
            
        mock_get_stream.return_value = mock_stream_generator()
        
        # Make streaming request
        response = self.client.get(
            f"/api/chat/query/stream?query={self.test_query}"
        )
        
        # Just verify it's a streaming response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["content-type"].startswith("text/event-stream"))
        
        # Verify the cache was checked
        mock_get_from_cache.assert_called()


class TestProcessChat(unittest.TestCase):
    """Tests specifically for the process_chat function with cache integration"""
    
    def setUp(self):
        """Set up test environment"""
        # Clear cache
        clear_semantic_cache()
        
        # Test data
        self.test_query = "What is the admission process?"
        self.test_response = {
            "answer": "Test answer",
            "thinking_steps": [{"step": 1, "content": "Thinking..."}],
            "documents": []
        }
    
    def tearDown(self):
        """Clean up test environment"""
        clear_semantic_cache()
    
    @patch('src.api.services.chat.get_agent')
    @patch('src.api.services.chat.add_to_cache')
    @patch('src.api.services.chat.get_from_cache')
    def test_process_chat_cache_hit(self, mock_get_from_cache, mock_add_to_cache, mock_get_agent):
        """Test process_chat with a cache hit"""
        # Mock a cache hit
        mock_get_from_cache.return_value = self.test_response
        
        # Call process_chat
        answer, conv_id, thinking_steps, docs, duration = process_chat(self.test_query)
        
        # Verify cache was checked
        mock_get_from_cache.assert_called_once()
        
        # Verify agent was not used
        mock_get_agent.assert_not_called()
        
        # Verify we got the cached response
        self.assertEqual(answer, self.test_response["answer"])
        self.assertEqual(thinking_steps, self.test_response["thinking_steps"])
    
    @patch('src.api.services.chat.get_agent')
    @patch('src.api.services.chat.add_to_cache')
    @patch('src.api.services.chat.get_from_cache')
    def test_process_chat_cache_miss(self, mock_get_from_cache, mock_add_to_cache, mock_get_agent):
        """Test process_chat with a cache miss"""
        # Mock a cache miss
        mock_get_from_cache.return_value = None
        
        # Mock the agent
        mock_agent = MagicMock()
        mock_agent.query.return_value = {
            "answer": "Test answer from agent",
            "thinking_steps": [{"step": 1, "content": "Agent thinking..."}],
            "documents": []
        }
        mock_get_agent.return_value = mock_agent
        
        # Call process_chat
        answer, conv_id, thinking_steps, docs, duration = process_chat(self.test_query)
        
        # Verify cache was checked
        mock_get_from_cache.assert_called_once()
        
        # Verify agent was used
        mock_agent.query.assert_called_once()
        
        # Verify response was added to cache
        mock_add_to_cache.assert_called_once()
        
        # Verify we got the agent's response
        self.assertEqual(answer, "Test answer from agent")
    
    @patch('src.api.services.chat.get_agent')
    @patch('src.api.services.chat.add_to_cache')
    @patch('src.api.services.chat.get_from_cache')
    def test_process_chat_with_streaming(self, mock_get_from_cache, mock_add_to_cache, mock_get_agent):
        """Test process_chat with streaming and cache hit"""
        # Mock a cache hit
        mock_get_from_cache.return_value = self.test_response
        
        # Create a mock callback handler
        mock_callback = MagicMock()
        
        # Call process_chat with callback handler
        process_chat(self.test_query, callback_handler=mock_callback)
        
        # Verify streaming callbacks were called with cached response
        mock_callback.on_thinking_start.assert_called_once()
        mock_callback.on_answer.assert_called_once_with(self.test_response["answer"])
        mock_callback.on_complete.assert_called_once()


if __name__ == '__main__':
    unittest.main() 