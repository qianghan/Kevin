"""
Tests for reference resolution capabilities of the memory feature.

This module tests:
1. Entity reference across turns
2. Pronoun references
3. Complex references to concepts discussed earlier
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
from src.api.services.chat import process_chat

class TestReferenceResolution(unittest.TestCase):
    """Test reference resolution capabilities"""
    
    def test_entity_reference(self):
        """Test entity reference across turns"""
        # Create a conversation
        conversation_id = f"test_entity_ref_{int(time.time())}"
        
        # First turn: Ask about a specific entity
        response1, _, _, _, _ = process_chat(
            "Who is the president of the University of British Columbia?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        print(f"Response 1: {response1[:100]}...")
        
        # Second turn: Reference the entity using "they"
        response2, _, _, _, _ = process_chat(
            "When did they start their term?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        print(f"Response 2: {response2[:100]}...")
        
        # Verify that response2 maintains context about the president
        # It should not ask "who are you referring to" or similar
        self.assertNotIn("who are you referring to", response2.lower())
        self.assertNotIn("unclear who", response2.lower())
        self.assertNotIn("specify who", response2.lower())
    
    def test_pronoun_references(self):
        """Test pronoun references (it, they, those)"""
        # Create a conversation
        conversation_id = f"test_pronouns_{int(time.time())}"
        
        # First turn: Ask about multiple items
        response1, _, _, _, _ = process_chat(
            "What scholarships are available for international students?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        print(f"Response 1: {response1[:100]}...")
        
        # Second turn: Reference using "they"
        response2, _, _, _, _ = process_chat(
            "Are they available for graduate students too?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        print(f"Response 2: {response2[:100]}...")
        
        # Third turn: Reference using "those"
        response3, _, _, _, _ = process_chat(
            "Which of those have the highest award amounts?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        print(f"Response 3: {response3[:100]}...")
        
        # Verify responses maintain context
        self.assertNotIn("which scholarships", response2.lower())
        self.assertNotIn("what are you referring to", response3.lower())
    
    def test_complex_references(self):
        """Test complex references to concepts discussed earlier"""
        # Create a conversation
        conversation_id = f"test_complex_ref_{int(time.time())}"
        
        # First turn: Establish a complex context
        response1, _, _, _, _ = process_chat(
            "How does the co-op program work for Engineering students at UBC and what are the benefits?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        print(f"Response 1: {response1[:100]}...")
        
        # Second turn: Reference a concept from first turn
        response2, _, _, _, _ = process_chat(
            "How does this compare with the work experience opportunities at other Canadian universities?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        print(f"Response 2: {response2[:100]}...")
        
        # Third turn: Further reference building on previous turns
        response3, _, _, _, _ = process_chat(
            "Which approach would better prepare me for a career in artificial intelligence?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        print(f"Response 3: {response3[:100]}...")
        
        # Verify the response maintains the complex context about co-op programs
        # and makes the connection to AI careers
        self.assertNotIn("what approach", response3.lower())
        self.assertNotIn("unclear what you're asking", response3.lower())
    
    def test_reference_with_topic_shift(self):
        """Test reference resolution when topic partially shifts"""
        # Create a conversation
        conversation_id = f"test_topic_shift_{int(time.time())}"
        
        # First turn: Establish context about UBC
        response1, _, _, _, _ = process_chat(
            "Tell me about the Computer Science department at UBC",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        print(f"Response 1: {response1[:100]}...")
        
        # Second turn: Shift to a related topic but maintain institution reference
        response2, _, _, _, _ = process_chat(
            "What about their Electrical Engineering program?",
            conversation_id=conversation_id,
            use_memory=True
        )
        
        print(f"Response 2: {response2[:100]}...")
        
        # Verify the response understands we're talking about UBC's EE program
        self.assertNotIn("which institution", response2.lower())
        self.assertNotIn("unclear which", response2.lower())

if __name__ == "__main__":
    unittest.main() 