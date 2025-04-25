"""
Tests for long conversations and context window management.

This module tests:
1. Maintaining context in long (10+ turn) conversations
2. Context window management with truncation of older messages
3. Performance in long conversations
4. Handling very long individual messages
"""

import unittest
import sys
import os
from pathlib import Path
import time
from typing import Dict, Any, List

# Add the root directory to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import modules for testing
from src.api.services.chat import process_chat, get_conversation_history
from src.core.agent import create_prompt_for_llm
from langchain.schema import Document
from langchain_core.messages import HumanMessage, AIMessage

class TestLongConversations(unittest.TestCase):
    """Test long conversations and context maintenance"""
    
    def test_10_turn_conversation(self):
        """Test a 10+ turn conversation about a consistent topic"""
        # Create a conversation for a student applying to Computer Science
        conversation_id = f"test_long_conv_{int(time.time())}"
        
        # List of queries for a 10-turn conversation
        queries = [
            "I'm interested in studying Computer Science at UBC, what programs do you offer?",
            "What are the admission requirements for the undergraduate program?",
            "Is there a co-op option available for CS students?",
            "What kind of projects do students work on in their final year?",
            "Are there research opportunities for undergraduate students?",
            "What scholarships are available for CS students?",
            "Can you tell me about the faculty members and their research areas?",
            "What computing resources are available to students?",
            "How does UBC's CS program compare to other top Canadian universities?",
            "What career support services are available for CS graduates?",
            "Based on what we've discussed, what would be your advice for me as an incoming CS student?"
        ]
        
        responses = []
        durations = []
        
        # Process all queries in sequence
        for i, query in enumerate(queries):
            print(f"\nTurn {i+1}: {query}")
            start_time = time.time()
            
            response, _, _, _, _ = process_chat(
                query,
                conversation_id=conversation_id,
                use_memory=True
            )
            
            duration = time.time() - start_time
            durations.append(duration)
            responses.append(response)
            
            print(f"Response: {response[:100]}...")
            print(f"Duration: {duration:.2f}s")
        
        # Verify the final response maintains context from earlier turns
        final_response = responses[-1]
        
        # It should reference CS program, which was mentioned in turn 1
        self.assertIn("CS", final_response)
        
        # Check for performance degradation
        first_half_avg = sum(durations[:5]) / 5
        second_half_avg = sum(durations[5:]) / 6
        
        print(f"Average duration (first 5 turns): {first_half_avg:.2f}s")
        print(f"Average duration (last 6 turns): {second_half_avg:.2f}s")
        
        # Allow for some performance degradation, but not excessive
        # Later turns should be at most 2x slower than early turns
        self.assertLess(second_half_avg, first_half_avg * 2,
                      "Excessive performance degradation in long conversation")
    
    def test_context_maintenance(self):
        """Verify context is maintained throughout a long conversation"""
        # Create a conversation with a unique ID to ensure no cache interference
        unique_time = int(time.time())
        conversation_id = f"test_context_nocache_{unique_time}"
        
        # Create a unique token that should be maintained in context
        unique_token = f"ZXTESTTOKEN{unique_time}"
        
        # Save original config for semantic cache and memory
        import src.api.services.chat as chat_service
        original_cache_enabled = chat_service._semantic_cache_enabled
        original_max_messages = chat_service._memory_max_messages
        original_max_recent_messages = chat_service._max_recent_messages
        
        try:
            # Disable semantic cache to avoid using cached responses
            chat_service._semantic_cache_enabled = False
            # Ensure we have enough messages in the memory window to maintain context
            chat_service._memory_max_messages = 10
            chat_service._max_recent_messages = 10
            
            # First turn: Introduce a unique topic with specific keywords
            # Make the first message very distinctive for easier recognition
            response1, _, _, _, _ = process_chat(
                f"I'm researching the impact of {unique_token} on CRYPTOGRAPHY for my THESIS at UBC",
                conversation_id=conversation_id,
                use_memory=True,
                use_web_search=True  # Let it use web search for realistic test
            )
            
            print(f"First response: {response1[:100]}...")
            
            # Middle turns: Add 6 turns of conversation on unrelated topics
            for i in range(6):
                process_chat(
                    f"Tell me about CS topic #{i+1}: data structures, algorithms, programming languages",
                    conversation_id=conversation_id,
                    use_memory=True,
                    use_web_search=True  # Let it use web search for realistic test
                )
            
            # Final turn: Reference the original topic without explicitly mentioning the keywords
            response, _, _, _, _ = process_chat(
                "What was the unique token I mentioned in my first message?",
                conversation_id=conversation_id,
                use_memory=True,
                use_web_search=True  # Let it use web search for realistic test
            )
            
            print(f"Final response: {response[:200]}...")
            
            # Look for the unique token in the response
            context_maintained = unique_token in response
            
            # Add detailed information to the assertion message
            assertion_message = f"Context from first message was lost after 6 turns"
            if not context_maintained:
                assertion_message += f"\nToken: {unique_token}\nResponse: {response}"
            
            self.assertTrue(context_maintained, assertion_message)
        finally:
            # Restore original config
            chat_service._semantic_cache_enabled = original_cache_enabled
            chat_service._memory_max_messages = original_max_messages
            chat_service._max_recent_messages = original_max_recent_messages

class TestContextWindowManagement(unittest.TestCase):
    """Test context window management and truncation"""
    
    def test_message_truncation(self):
        """Test that older messages are properly truncated"""
        # Create a conversation with more messages than the limit
        conversation_id = f"test_truncation_{int(time.time())}"
        
        # Add 15 message pairs (30 total messages)
        for i in range(15):
            process_chat(
                f"User query {i+1} with some content to fill up the history",
                conversation_id=conversation_id,
                use_memory=True
            )
        
        # Get conversation history
        history = get_conversation_history(conversation_id)
        
        # Check the total number of messages
        print(f"Total messages in history: {len(history)}")
        
        # Add one more message and check if the memory feature limits history
        response, _, _, _, _ = process_chat(
            "This is the final message. Can you recall what we discussed in the first few messages?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        print(f"Final response: {response[:200]}...")
        
        # The response should indicate inability to recall earliest messages
        # or should mention truncation of history
        earliest_recalled = False
        for i in range(1, 4):  # Check if it recalls messages 1-3
            if f"query {i}" in response.lower():
                earliest_recalled = True
                break
        
        self.assertFalse(earliest_recalled,
                       "System incorrectly recalled messages that should have been truncated")
    
    def test_long_individual_messages(self):
        """Test handling of very long individual messages"""
        # Create a conversation
        conversation_id = f"test_long_msg_{int(time.time())}"
        
        # Add a first message of reasonable length
        process_chat(
            "I'm researching Canadian universities",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        # Add a very long message (5000+ characters)
        long_query = "This is a very long query about universities " * 200  # ~5000 chars
        process_chat(
            long_query,
            conversation_id=conversation_id,
            use_memory=True
        )
        
        # Add a follow-up message
        response, _, _, _, _ = process_chat(
            "Based on what I just told you, what universities would you recommend?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        print(f"Response after long message: {response[:200]}...")
        
        # The response should still be relevant despite the long previous message
        self.assertIn("universit", response.lower())
        
        # Test prompt generation with long messages
        messages = [
            HumanMessage(content="Short message 1"),
            AIMessage(content="Short response 1"),
            HumanMessage(content=long_query),
            AIMessage(content="Response to long query"),
            HumanMessage(content="Final short query")
        ]
        
        documents = [Document(page_content="Test document content", metadata={"source": "test"})]
        
        # Generate prompt with long messages
        prompt = create_prompt_for_llm("Final short query", documents, messages)
        
        # Check that the prompt contains truncation indicator
        self.assertIn("...", prompt)

if __name__ == "__main__":
    unittest.main() 