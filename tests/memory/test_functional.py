"""
Functional tests for memory features of the Kevin chat agent.

This module contains tests for memory functionality and backward compatibility:
1. Multi-turn conversation with reference resolution
2. Comparing responses with memory disabled vs. enabled
3. Verifying backward compatibility
4. Ensuring no performance degradation for single-turn queries
"""

import unittest
import sys
import os
from pathlib import Path
import time
import json
from typing import Dict, Any, List

# Add the root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import modules for testing
from src.api.services.chat import get_conversation_history, add_message_to_history, process_chat
from src.core.agent import UniversityAgent

class TestMemoryFunctionality(unittest.TestCase):
    """Test memory functionality with multi-turn conversations"""
    
    def test_multi_turn_conversation(self):
        """Test multi-turn conversation with reference resolution"""
        # Create a new conversation
        conversation_id = f"test_multi_turn_{int(time.time())}"
        
        # Turn 1: Ask about programs
        response1, _, _, _, _ = process_chat(
            "What programs does the university offer in Computer Science?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        # Save response for comparison
        print(f"Response 1: {response1[:100]}...")
        
        # Turn 2: Ask about the advanced ones (reference resolution)
        response2, _, _, _, _ = process_chat(
            "Tell me more about the advanced ones",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        # Save response for comparison
        print(f"Response 2: {response2[:100]}...")
        
        # The second response should understand the reference to "advanced ones" in context of CS programs
        self.assertIsNotNone(response2)
        self.assertNotEqual(response2, "I'm sorry, but I'm not sure what you're referring to.")
        
        # Turn 3: Ask for prerequisites (continuing the conversation)
        response3, _, _, _, _ = process_chat(
            "What are the prerequisites for these programs?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        # Save response for comparison
        print(f"Response 3: {response3[:100]}...")
        
        # The third response should maintain context from the previous turns
        self.assertIsNotNone(response3)
    
    def test_memory_enabled_vs_disabled(self):
        """Compare responses with memory enabled vs. disabled"""
        # Create two conversation IDs
        conversation_with_memory = f"test_with_memory_{int(time.time())}"
        conversation_without_memory = f"test_without_memory_{int(time.time())}"
        
        # Turn 1: Ask about admission requirements (same for both)
        process_chat(
            "What are the admission requirements for UBC?",
            conversation_id=conversation_with_memory,
            use_memory=True
        )
        
        process_chat(
            "What are the admission requirements for UBC?",
            conversation_id=conversation_without_memory,
            use_memory=False
        )
        
        # Turn 2: Ask a follow-up question with a reference
        response_with_memory, _, _, _, _ = process_chat(
            "What documents do I need to submit for my application?",
            conversation_id=conversation_with_memory,
            use_memory=True
        )
        
        response_without_memory, _, _, _, _ = process_chat(
            "What documents do I need to submit for my application?",
            conversation_id=conversation_without_memory,
            use_memory=False
        )
        
        # Save responses for comparison
        print(f"Response with memory: {response_with_memory[:100]}...")
        print(f"Response without memory: {response_without_memory[:100]}...")
        
        # Responses should be different due to context
        # The one with memory should understand we're talking about UBC application
        # The one without memory might be more generic
        self.assertIsNotNone(response_with_memory)
        self.assertIsNotNone(response_without_memory)

class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility of memory features"""
    
    def test_existing_api_calls(self):
        """Verify existing API calls still work without changes"""
        # Call process_chat without specifying use_memory (should use default)
        response, conversation_id, thinking_steps, documents, duration = process_chat(
            "What programs are offered at the university?"
        )
        
        # Check that we got a valid response
        self.assertIsNotNone(response)
        self.assertIsNotNone(conversation_id)
        self.assertIsInstance(duration, float)
    
    def test_memory_feature_toggle(self):
        """Test toggling memory feature on/off via parameter"""
        # Create a conversation ID
        conversation_id = f"test_toggle_{int(time.time())}"
        
        # First message with memory on
        response1, _, _, _, _ = process_chat(
            "What is the university ranking?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        # Second message with memory off
        response2, _, _, _, _ = process_chat(
            "Tell me more about that",
            conversation_id=conversation_id,
            use_memory=False
        )
        
        # Both should return valid responses
        self.assertIsNotNone(response1)
        self.assertIsNotNone(response2)
    
    def test_performance_single_turn(self):
        """Verify no performance degradation for single-turn queries"""
        # Measure performance with memory disabled
        start_time = time.time()
        process_chat(
            "What is the application deadline?",
            use_memory=False
        )
        no_memory_duration = time.time() - start_time
        
        # Measure performance with memory enabled (but only one turn)
        start_time = time.time()
        process_chat(
            "What is the application deadline?",
            use_memory=True
        )
        with_memory_duration = time.time() - start_time
        
        # Log times for comparison
        print(f"Duration without memory: {no_memory_duration:.4f}s")
        print(f"Duration with memory: {with_memory_duration:.4f}s")
        
        # There should not be a significant performance difference for single-turn queries
        # Allow up to 20% overhead for the memory feature
        self.assertLess(
            with_memory_duration, 
            no_memory_duration * 1.2,  # Allow 20% overhead
            f"Memory feature adds significant overhead: {with_memory_duration:.4f}s vs {no_memory_duration:.4f}s"
        )

if __name__ == "__main__":
    unittest.main() 