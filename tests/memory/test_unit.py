"""
Unit tests for memory features of the Kevin chat agent.

This module contains tests for:
1. Conversation history retrieval and formatting
2. Prompt generation with various history lengths
3. Message conversion from different formats
4. Error handling and fallback mechanisms
"""

import unittest
import sys
import os
from pathlib import Path
import time
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Add the root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import modules for testing
from src.api.services.chat import get_conversation_history, add_message_to_history
from src.api.services.chat import process_chat
from src.core.agent import create_prompt_for_llm, create_original_prompt_for_llm, UniversityAgent, create_prompt_with_fallback
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage

class TestConversationRetrieval(unittest.TestCase):
    """Test conversation history retrieval and formatting"""
    
    def setUp(self):
        # Create a unique conversation ID for testing
        self.conversation_id = f"test_{int(time.time())}"
        
        # Add test messages to the conversation
        add_message_to_history(self.conversation_id, "user", "Test message 1")
        add_message_to_history(self.conversation_id, "assistant", "Test response 1")
        add_message_to_history(self.conversation_id, "user", "Test message 2")
        add_message_to_history(self.conversation_id, "assistant", "Test response 2")
    
    def test_conversation_retrieval(self):
        """Test that conversation history can be retrieved correctly"""
        # Get the conversation history
        history = get_conversation_history(self.conversation_id)
        
        # Check that the history contains the correct number of messages
        self.assertEqual(len(history), 4)
        
        # Check that the messages have the correct roles and content
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "Test message 1")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "Test response 1")
        self.assertEqual(history[2]["role"], "user")
        self.assertEqual(history[2]["content"], "Test message 2")
        self.assertEqual(history[3]["role"], "assistant")
        self.assertEqual(history[3]["content"], "Test response 2")

class TestPromptGeneration(unittest.TestCase):
    """Test prompt generation with various history lengths"""
    
    def test_prompt_with_no_history(self):
        """Test prompt generation without conversation history"""
        query = "What are the admission requirements?"
        documents = [
            Document(page_content="Admission requires a GPA of 3.0", metadata={"source": "doc1"})
        ]
        
        # Generate prompt without history
        prompt = create_prompt_for_llm(query, documents)
        
        # Check that the prompt contains the query and document
        self.assertIn(query, prompt)
        self.assertIn("Admission requires a GPA of 3.0", prompt)
        
        # Check that the prompt does not contain conversation history section
        self.assertNotIn("CONVERSATION HISTORY", prompt)
    
    def test_prompt_with_history(self):
        """Test prompt generation with conversation history"""
        query = "What are the admission requirements?"
        documents = [
            Document(page_content="Admission requires a GPA of 3.0", metadata={"source": "doc1"})
        ]
        
        # Create conversation history
        messages = [
            HumanMessage(content="What programs do you offer?"),
            AIMessage(content="We offer Computer Science, Engineering, and Business programs."),
            HumanMessage(content=query)
        ]
        
        # Generate prompt with history
        prompt = create_prompt_for_llm(query, documents, messages)
        
        # Check that the prompt contains the query, document, and conversation history
        self.assertIn(query, prompt)
        self.assertIn("Admission requires a GPA of 3.0", prompt)
        self.assertIn("CONVERSATION HISTORY", prompt)
        self.assertIn("User: What programs do you offer?", prompt)
        self.assertIn("Assistant: We offer Computer Science, Engineering, and Business programs.", prompt)
    
    def test_prompt_with_long_history(self):
        """Test that long conversation history is truncated"""
        query = "Summarize our conversation"
        documents = []
        
        # Create a very long conversation history
        messages = []
        for i in range(20):
            messages.append(HumanMessage(content=f"User message {i} with a lot of content " * 10))
            messages.append(AIMessage(content=f"Assistant response {i} that is also quite lengthy " * 10))
        
        # Add final query
        messages.append(HumanMessage(content=query))
        
        # Generate prompt with history
        prompt = create_prompt_for_llm(query, documents, messages)
        
        # Check that truncation message is included
        self.assertIn("conversation truncated", prompt.lower())

class TestMessageConversion(unittest.TestCase):
    """Test message conversion from different formats"""
    
    def test_valid_message_format(self):
        """Test conversion of valid message format"""
        agent = UniversityAgent()
        
        # Create test conversation history
        history = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"}
        ]
        
        # Process the query with the history
        result = agent.query("Final question", conversation_history=history)
        
        # Check that the result contains an answer
        self.assertIn("answer", result)
        self.assertIsNotNone(result["answer"])
    
    def test_invalid_message_format(self):
        """Test that invalid message formats are handled gracefully"""
        agent = UniversityAgent()
        
        # Create history with invalid format
        history = [
            {"invalid": "format"},
            {"role": "user", "wrong_key": "Question 1"},
            None,
            "Just a string"
        ]
        
        # Process the query with the invalid history
        result = agent.query("Test question", conversation_history=history)
        
        # Check that the result contains an answer despite invalid history
        self.assertIn("answer", result)
        self.assertIsNotNone(result["answer"])

class TestErrorHandling(unittest.TestCase):
    """Test error handling and fallback mechanisms"""
    
    def test_fallback_to_original_prompt(self):
        """Test fallback to original prompt format when an error occurs"""
        # Store original functions
        original_prompt_func = create_prompt_for_llm
        original_fallback_func = create_original_prompt_for_llm
        
        try:
            # Create a mock for the create_prompt_for_llm function that throws an error
            def mock_create_prompt(*args, **kwargs):
                raise ValueError("Test error to force fallback")
            
            # Create a mock for original prompt function that we can track
            def mock_original_prompt(query, documents):
                # Return a distinctive prompt without conversation history
                return f"TEST_ORIGINAL_PROMPT_FORMAT\nQuestion: {query}\nNo conversation history here."
            
            # Apply the mocks
            import src.core.agent
            src.core.agent.create_prompt_for_llm = mock_create_prompt
            src.core.agent.create_original_prompt_for_llm = mock_original_prompt
            
            # Create test data
            query = "Test query"
            documents = [Document(page_content="Test content", metadata={"source": "test"})]
            messages = [HumanMessage(content="Previous message"), HumanMessage(content=query)]
            
            # Call the fallback function which should use our mocked original prompt function
            prompt = create_prompt_with_fallback(query, documents, messages)
            
            # Verify we got the original prompt format
            self.assertIn("TEST_ORIGINAL_PROMPT_FORMAT", prompt)
            self.assertNotIn("CONVERSATION HISTORY", prompt)
            
        finally:
            # Restore the original functions
            src.core.agent.create_prompt_for_llm = original_prompt_func
            src.core.agent.create_original_prompt_for_llm = original_fallback_func
    
    def test_process_chat_error_handling(self):
        """Test that process_chat handles errors in conversation history retrieval"""
        # Add a test message
        conversation_id = f"test_error_{int(time.time())}"
        add_message_to_history(conversation_id, "user", "Test message")
        
        # Process a chat with a valid conversation ID
        result = process_chat("Test query", conversation_id=conversation_id, use_memory=True)
        
        # Check that we got a valid result
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 5)  # Should have 5 return values
        
        # Test with an invalid conversation ID but with error handling
        result = process_chat("Test query", conversation_id="invalid_id", use_memory=True)
        
        # Check that we still got a valid result despite the error
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 5)

if __name__ == "__main__":
    unittest.main() 