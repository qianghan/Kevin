"""
Chat service for Kevin API.

This module provides functions for processing chat queries and managing conversations.
"""

import time
import uuid
import yaml
import sys
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path

# Add path fix to ensure src is in the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.core.agent import UniversityAgent
from src.utils.logger import get_logger
from src.api.services.documents import cache_document
from src.api.services.cache.cache_service import get_from_cache, add_to_cache

# Global conversation storage (in-memory for now)
# In a production environment, this would be replaced with a database
_conversations: Dict[str, List[Dict[str, Any]]] = {}

# Global agent instance
_agent = None

# Enable/disable semantic cache (from config)
_semantic_cache_enabled = True

logger = get_logger(__name__)

# Load configuration
try:
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if config is not None and "semantic_cache" in config:
            _semantic_cache_enabled = config.get('semantic_cache', {}).get('enabled', True)
    
    logger.info(f"Semantic cache enabled: {_semantic_cache_enabled}")
except Exception as e:
    logger.error(f"Error loading config for semantic cache: {str(e)}")
    logger.warning("Defaulting to semantic_cache_enabled=True")
    _semantic_cache_enabled = True


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
    documents: Optional[List[Dict[str, Any]]] = None,
    is_cached: bool = False
) -> None:
    """
    Add a message to the conversation history.
    
    Args:
        conversation_id: The ID of the conversation.
        role: The role of the message sender (e.g., "user", "assistant").
        content: The content of the message.
        thinking_steps: Optional thinking steps for assistant messages.
        documents: Optional documents for assistant messages.
        is_cached: Whether this response came from cache.
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
        if is_cached:
            message["from_cache"] = True
    
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
        # Start timing
        start_time = time.time()
        
        # Try to get response from semantic cache if enabled
        cached_response = None
        if _semantic_cache_enabled:
            logger.info(f"Checking semantic cache for query: '{query}'")
            metadata = {
                "use_web_search": use_web_search,
                "conversation_id": conversation_id
            }
            
            try:
                cached_response = get_from_cache(query, metadata)
            except Exception as e:
                logger.error(f"Error retrieving from semantic cache: {str(e)}", exc_info=True)
                cached_response = None
            
            if cached_response:
                logger.info(f"Cache hit for query: '{query}'")
                
                # Extract data from cached response
                answer = cached_response.get("answer", "")
                thinking_steps = cached_response.get("thinking_steps", [])
                documents = cached_response.get("documents", [])
                
                # If streaming, send the cached response through the streaming channel
                if callback_handler:
                    # Start thinking with cached flag
                    callback_handler.on_thinking_start({"query": query, "cached": True})
                    
                    # Send cached thinking steps if available
                    if thinking_steps:
                        for step in thinking_steps:
                            callback_handler.on_thinking_update(step)
                    
                    # Send thinking end event
                    callback_handler.on_thinking_end({"query": query, "cached": True})
                    
                    # Signal the start of the answer
                    callback_handler.on_answer_start()
                    
                    # Simulate streaming by chunking the answer
                    # This ensures frontend compatibility without frontend changes
                    if answer:
                        # Split answer into chunks (e.g., by spaces or chunks of characters)
                        # Using character chunks of 10-20 chars for more natural streaming feel
                        chunk_size = 15
                        for i in range(0, len(answer), chunk_size):
                            chunk = answer[i:i+chunk_size]
                            callback_handler.on_answer_chunk(chunk)
                            # Small delay to simulate realistic typing speed
                            time.sleep(0.01)
                    
                    # For compatibility, still send the full answer too
                    callback_handler.on_answer(answer)
                    
                    # Send documents if available
                    if documents:
                        callback_handler.on_documents(documents)
                        
                    # Send completion event
                    callback_handler.on_complete()
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Add to conversation history
                add_message_to_history(
                    conversation_id, 
                    "assistant", 
                    answer, 
                    thinking_steps=thinking_steps, 
                    documents=documents,
                    is_cached=True
                )
                
                logger.info(f"Returned cached response in {duration:.2f}s")
                return answer, conversation_id, thinking_steps, documents, duration
        
        # No cache hit, process normally
        logger.info(f"Processing query without cache: '{query}'")
        
        # Get the agent
        agent = get_agent()
        
        # Configure the agent to use web search if requested
        agent.use_web = use_web_search
        
        # Add callback handler if provided
        thinking_steps = []
        if callback_handler:
            # Start thinking
            callback_handler.on_thinking_start({"query": query})
            
            # Process thinking steps
            def thinking_step_callback(step):
                thinking_steps.append(step)
                callback_handler.on_thinking_update(step)
                
            # Set the thinking step callback
            agent.set_thinking_step_callback(thinking_step_callback)
            
        # Process the query
        result = agent.query(query)
        
        # Extract information from the result
        answer = result["answer"]
        retrieved_documents = result.get("documents", [])
        
        # Format documents
        documents = []
        for doc in retrieved_documents:
            # Cache the document
            doc_id = cache_document(doc)
            
            # Add to formatted documents
            documents.append({
                "id": doc_id,
                "title": doc.metadata.get("title", "Unknown"),
                "url": doc.metadata.get("url", ""),
                "source": doc.metadata.get("source", "Unknown"),
                "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            })
            
        # Add to conversation history
        add_message_to_history(
            conversation_id,
            "assistant",
            answer,
            thinking_steps=thinking_steps if thinking_steps else result.get("thinking_steps", []),
            documents=documents
        )
        
        # Send final answer through callback handler if provided
        if callback_handler:
            callback_handler.on_answer(answer)
            
            # Send documents if available
            if documents:
                callback_handler.on_documents(documents)
                
            # Send completion event
            callback_handler.on_complete()
            
        # Calculate duration
        duration = time.time() - start_time
        
        # Cache the response if semantic cache is enabled
        if _semantic_cache_enabled:
            logger.info(f"Adding response to semantic cache for query: '{query}'")
            
            # Create a cacheable version of the response
            cache_data = {
                "answer": answer,
                "thinking_steps": thinking_steps if thinking_steps else result.get("thinking_steps", []),
                "documents": documents
            }
            
            # Add metadata for the cache
            cache_metadata = {
                "use_web_search": use_web_search,
                "conversation_id": conversation_id,
                "duration": duration,
                "has_documents": len(documents) > 0
            }
            
            # Store in cache
            try:
                add_to_cache(query, cache_data, cache_metadata)
            except Exception as e:
                logger.error(f"Error adding to semantic cache: {str(e)}", exc_info=True)
        
        logger.info(f"Query processed in {duration:.2f} seconds")
        return answer, conversation_id, thinking_steps if thinking_steps else result.get("thinking_steps", []), documents, duration
    except Exception as e:
        logger.error(f"Error processing chat query: {e}", exc_info=True)
        error_message = f"I'm sorry, but I encountered an error processing your request: {str(e)}"
        
        # Signal error through callback if provided
        if callback_handler:
            callback_handler.on_error(str(e))
            callback_handler.on_complete()
            
        # Calculate duration
        duration = time.time() - start_time if 'start_time' in locals() else 0
        
        return error_message, conversation_id, [], [], duration 