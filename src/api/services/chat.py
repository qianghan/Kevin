"""
Chat service for Kevin API.

This module provides functions for processing chat queries and managing conversations.
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union

from src.core.agent import UniversityAgent
from src.utils.logger import get_logger
from src.api.services.documents import cache_document

# Global conversation storage (in-memory for now)
# In a production environment, this would be replaced with a database
_conversations: Dict[str, List[Dict[str, Any]]] = {}

# Global agent instance
_agent = None

logger = get_logger(__name__)


def get_agent() -> UniversityAgent:
    """
    Get the agent instance, creating it if it doesn't exist.
    
    Returns:
        The agent instance.
    """
    global _agent
    if _agent is None:
        logger.info("Initializing agent")
        _agent = UniversityAgent()
    return _agent


def get_conversation_history(conversation_id: str) -> List[Dict[str, Any]]:
    """
    Get the conversation history for a specific conversation.
    
    Args:
        conversation_id: The ID of the conversation.
        
    Returns:
        The conversation history as a list of messages.
    """
    return _conversations.get(conversation_id, [])


def add_message_to_history(
    conversation_id: str,
    role: str,
    content: str,
    thinking_steps: Optional[List[Dict[str, Any]]] = None,
    documents: Optional[List[Dict[str, Any]]] = None
) -> None:
    """
    Add a message to the conversation history.
    
    Args:
        conversation_id: The ID of the conversation.
        role: The role of the message sender (e.g., "user", "assistant").
        content: The content of the message.
        thinking_steps: Optional thinking steps for assistant messages.
        documents: Optional documents for assistant messages.
    """
    # Create the conversation if it doesn't exist
    if conversation_id not in _conversations:
        _conversations[conversation_id] = []
    
    # Create the message
    message = {
        "role": role,
        "content": content,
        "timestamp": time.time()
    }
    
    # Add thinking steps and documents if provided
    if role == "assistant":
        if thinking_steps:
            message["thinking_steps"] = thinking_steps
        if documents:
            message["documents"] = documents
    
    # Add to the conversation
    _conversations[conversation_id].append(message)


def process_chat(
    query: str,
    use_web_search: bool = False,
    conversation_id: Optional[str] = None,
    callback_handler: Optional[Any] = None
) -> Tuple[str, str, List[Dict[str, Any]], List[Dict[str, Any]], float]:
    """
    Process a chat query.
    
    Args:
        query: The query to process.
        use_web_search: Whether to use web search.
        conversation_id: Optional conversation ID for context.
        callback_handler: Optional callback handler for streaming.
        
    Returns:
        A tuple containing:
        - The answer text
        - The conversation ID
        - The thinking steps
        - The documents
        - The duration in seconds
    """
    # Get or create the conversation ID
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        logger.info(f"Created new conversation: {conversation_id}")
    else:
        logger.info(f"Using existing conversation: {conversation_id}")
    
    # Add the user message to the conversation history
    add_message_to_history(conversation_id, "user", query)
    
    try:
        # Get the agent
        agent = get_agent()
        
        # Start timing
        start_time = time.time()
        
        # Process the query
        logger.info(f"Processing query: {query}")
        
        # Configure the agent to use web search if requested
        agent.use_web = use_web_search
        
        # Add callback handler if provided
        if callback_handler:
            # Start thinking
            callback_handler.on_thinking_start({"query": query})
            
            # Process thinking steps
            def thinking_step_callback(step):
                callback_handler.on_thinking_update(step)
                
            # Set the thinking step callback
            agent.set_thinking_step_callback(thinking_step_callback)
            
        # Process the query
        result = agent.query(query)
        
        # Get the answer and metadata
        answer = result.get("answer", "I couldn't generate an answer.")
        thinking_steps = result.get("thinking_steps", [])
        documents = result.get("documents", [])
        
        # Cache any documents
        for doc in documents:
            cache_document(doc)
            
            # If we have a callback handler, send document events
            if callback_handler:
                callback_handler.on_document(doc)
        
        # Calculate duration
        duration = time.time() - start_time
        logger.info(f"Query processed in {duration:.2f} seconds")
        
        # If we have a callback handler, start streaming the answer
        if callback_handler:
            # End thinking
            callback_handler.on_thinking_end({"duration": duration})
            
            # Start answer
            callback_handler.on_answer_start()
            
            # For simplicity, we'll stream in chunks of a few characters
            # In a real implementation, you might get streaming directly from the LLM
            chunk_size = 10
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i:i+chunk_size]
                callback_handler.on_answer_chunk(chunk)
                time.sleep(0.05)  # Simulate some delay
                
            # End answer
            callback_handler.on_answer_end()
        
        # Add the assistant message to the conversation history
        add_message_to_history(
            conversation_id, 
            "assistant", 
            answer, 
            thinking_steps, 
            documents
        )
        
        # Return the result
        return answer, conversation_id, thinking_steps, documents, duration
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        error_message = f"An error occurred: {str(e)}"
        
        # If we have a callback handler, send an error event
        if callback_handler:
            callback_handler.on_error(error_message)
        
        # Add the error message to the conversation history
        add_message_to_history(conversation_id, "assistant", error_message)
        
        # Return an error result
        return error_message, conversation_id, [], [], 0.0 