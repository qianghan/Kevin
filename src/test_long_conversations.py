"""
Test script to verify first message preservation in conversation context.
"""

import time
import uuid
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add necessary path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.services.chat import (
    process_chat, 
    get_conversation_history,
    _get_formatted_history
)

def test_first_message_preservation():
    """Test that the first message is preserved in the conversation history even after many exchanges."""
    # Create unique ID for this test
    test_id = str(uuid.uuid4())
    conversation_id = f"test_preserve_first_{test_id}"
    
    # First message with unique token
    unique_token = f"UNIQUE_PRESERVE_TOKEN_{test_id}"
    first_query = f"This is the first message with a unique token: {unique_token}"
    
    # Process first message
    process_chat(
        first_query,
        conversation_id=conversation_id,
        use_memory=True
    )
    
    # Add 10 more messages to create a long conversation
    for i in range(10):
        process_chat(
            f"This is message number {i+2} without the unique token",
            conversation_id=conversation_id,
            use_memory=True
        )
    
    # Get complete conversation history
    history = get_conversation_history(conversation_id)
    print(f"Total messages in history: {len(history)}")
    
    # Check if the first message is still in the raw history
    first_message_preserved = False
    for msg in history:
        if msg["role"] == "user" and unique_token in msg["content"]:
            first_message_preserved = True
            print("First message found in raw history!")
            break
    
    assert first_message_preserved, "First message not found in raw history"
    
    # Get formatted history used by the agent
    formatted_history = _get_formatted_history(conversation_id)
    print(f"Total messages in formatted history: {len(formatted_history)}")
    
    # Check if the first message is in the formatted history
    first_message_formatted = False
    for msg in formatted_history:
        if hasattr(msg, 'content') and unique_token in msg.content:
            first_message_formatted = True
            print("First message found in formatted history!")
            break
    
    assert first_message_formatted, "First message not preserved in formatted history"
    print("Test passed: First message is preserved in conversation history")

if __name__ == "__main__":
    test_first_message_preservation() 