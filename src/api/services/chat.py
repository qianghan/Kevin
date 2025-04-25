"""
Chat service for Kevin API.

This module provides functions for processing chat queries and managing conversations.
"""

import time
import uuid
import yaml
import sys
import json
from functools import lru_cache
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
import threading

# Add path fix to ensure src is in the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.core.agent import UniversityAgent
from src.utils.logger import get_logger
from src.api.services.documents import cache_document
from src.api.services.cache.cache_service import get_from_cache, add_to_cache

# Global conversation storage (in-memory for now)
# In a production environment, this would be replaced with a database
_conversations: Dict[str, List[Dict[str, Any]]] = {}

# Memory cache to avoid repeated history processing
# Maps conversation_id to a tuple of (timestamp, formatted_history)
_memory_cache: Dict[str, Tuple[float, List[Any]]] = {}

# Global agent instance
_agent = None

# Enable/disable semantic cache (from config)
_semantic_cache_enabled = True

# Enable/disable memory feature (from config)
_memory_enabled = True
_memory_max_messages = 10  # Maximum number of messages to include in history
_memory_cache_ttl = 300.0   # Cache TTL in seconds (increased to 5 minutes)

# Maximum number of recent messages to process for better performance
_max_recent_messages = 5  # Reduced from 10 for better performance
# Cache lock for thread safety
_cache_lock = threading.RLock()

logger = get_logger(__name__)

# Load configuration
try:
    config_path = Path("config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if config is not None:
            # Load semantic cache config
            if "semantic_cache" in config:
                _semantic_cache_enabled = config.get('semantic_cache', {}).get('enabled', True)
            
            # Load memory feature config
            if "memory" in config:
                memory_config = config.get('memory', {})
                _memory_enabled = memory_config.get('enabled', True)
                _memory_max_messages = memory_config.get('max_messages', 10)
                _memory_cache_ttl = memory_config.get('cache_ttl', 300.0)
    
    logger.info(f"Semantic cache enabled: {_semantic_cache_enabled}")
    logger.info(f"Memory feature enabled: {_memory_enabled}")
    logger.info(f"Memory max messages: {_memory_max_messages}")
    logger.info(f"Memory cache TTL: {_memory_cache_ttl}")
except Exception as e:
    logger.error(f"Error loading config: {str(e)}")
    logger.warning("Defaulting to semantic_cache_enabled=True and memory_enabled=True")
    _semantic_cache_enabled = True
    _memory_enabled = True


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
    Get the conversation history for a given conversation ID.
    
    Args:
        conversation_id: The conversation ID.
        
    Returns:
        The conversation history.
    """
    if conversation_id not in _conversations:
        _conversations[conversation_id] = []
    
    return _conversations[conversation_id]


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
        conversation_id: The conversation ID.
        role: The role of the message sender (user or assistant).
        content: The message content.
        thinking_steps: Optional thinking steps.
        documents: Optional documents.
        is_cached: Whether the message was retrieved from cache.
    """
    # Use cache lock for thread safety
    with _cache_lock:
        if conversation_id not in _conversations:
            _conversations[conversation_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        
        if role == "assistant":
            message["thinking_steps"] = thinking_steps if thinking_steps else []
            # Store only document IDs rather than full documents to reduce memory
            message["documents"] = documents if documents else [] 
            message["from_cache"] = is_cached
        
        _conversations[conversation_id].append(message)
        
        # Invalidate memory cache when a new message is added
        if conversation_id in _memory_cache:
            del _memory_cache[conversation_id]


def _format_history_for_agent(history: List[Dict[str, Any]], max_messages: int = 5) -> List[Any]:
    """
    Format conversation history for the agent.
    This is an optimized internal function that converts the history to the format expected by the agent.
    
    Args:
        history: The conversation history.
        max_messages: Maximum number of messages to include.
        
    Returns:
        Formatted history for the agent.
    """
    # Import here to avoid circular imports
    from langchain_core.messages import HumanMessage, AIMessage
    
    # Efficient slicing for most recent messages - optimize for performance
    if len(history) > max_messages * 2:  # *2 because each turn has user+assistant messages
        # Keep first message plus most recent messages to maintain conversation context
        first_message = history[0:1]
        recent_messages = history[-(max_messages*2-1):]
        history = first_message + recent_messages
    
    # Pre-allocate memory for the formatted history - more efficient
    total_msgs = len(history)
    formatted_history = [None] * total_msgs
    
    # Process messages in one pass with direct indexing
    for i in range(total_msgs):
        msg = history[i]
        if msg["role"] == "user":
            formatted_history[i] = HumanMessage(content=msg["content"])
        else:
            formatted_history[i] = AIMessage(content=msg["content"])
    
    return formatted_history


def _get_formatted_history(conversation_id: str) -> List[Any]:
    """
    Get the formatted history for a conversation, using cache if available.
    
    Args:
        conversation_id: The conversation ID.
        
    Returns:
        Formatted history for the agent.
    """
    current_time = time.time()
    
    # Use cache lock for thread safety
    with _cache_lock:
        # Check if we have a valid cached version
        if conversation_id in _memory_cache:
            cache_time, formatted_history = _memory_cache[conversation_id]
            if current_time - cache_time < _memory_cache_ttl:
                return formatted_history
        
        # Get and format the history
        history = get_conversation_history(conversation_id)
        
        # Exclude the most recent message (it's the query we're processing)
        if history and len(history) > 1:
            history = history[:-1]
        
        # Optimize history length for performance
        if len(history) > _max_recent_messages * 2:  # *2 because each turn has user+assistant messages
            # Modified approach: Always keep the first message plus most recent messages
            # This ensures context from the start of the conversation is maintained
            first_message = history[0:1]  # Get the first message
            recent_messages = history[-((_max_recent_messages * 2) - 1):]  # Get recent messages, leaving room for the first
            history = first_message + recent_messages
        
        # Format the history
        formatted_history = _format_history_for_agent(history, _max_recent_messages)
        
        # Cache the formatted history
        _memory_cache[conversation_id] = (current_time, formatted_history)
        
        return formatted_history


def process_chat(
    query: str,
    use_web_search: bool = False,
    conversation_id: Optional[str] = None,
    callback_handler: Optional[Any] = None,
    use_memory: Optional[bool] = None
) -> Tuple[str, str, List[Dict[str, Any]], List[Dict[str, Any]], float]:
    """
    Process a chat query.
    
    Args:
        query: The query to process.
        use_web_search: Whether to use web search.
        conversation_id: Optional conversation ID for context.
        callback_handler: Optional callback handler for streaming.
        use_memory: Whether to use conversation memory feature. If None, uses global setting.
        
    Returns:
        A tuple containing:
        - The answer text
        - The conversation ID
        - The thinking steps
        - The documents
        - The duration in seconds
    """
    # Start timing immediately for accurate performance measurement
    start_time = time.time()
    
    # Get or create the conversation ID
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        logger.info(f"Created new conversation: {conversation_id}")
    else:
        logger.info(f"Using existing conversation: {conversation_id}")
    
    # Determine whether to use memory feature
    should_use_memory = _memory_enabled if use_memory is None else use_memory
    
    # Check semantic cache before adding to history (optimization)
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
    
    # Add the user message to the conversation history (must happen before cache processing)
    add_message_to_history(conversation_id, "user", query)
    
    try:
        # Process cache hit if we have one
        if _semantic_cache_enabled and cached_response:
            logger.info(f"Cache hit for query: '{query}'")
            
            # Extract data from cached response
            answer = cached_response.get("answer", "")
            thinking_steps = cached_response.get("thinking_steps", [])
            documents = cached_response.get("documents", [])
            
            # Add to conversation history
            add_message_to_history(
                conversation_id, 
                "assistant", 
                answer, 
                thinking_steps=thinking_steps, 
                documents=documents,
                is_cached=True
            )
            
            # Calculate duration
            duration = time.time() - start_time
            
            logger.info(f"Returned cached response in {duration:.2f}s")
            return answer, conversation_id, thinking_steps, documents, duration
        
        # No cache hit, process normally
        logger.info(f"Processing query without cache: '{query}'")
        
        # Get conversation history if memory feature is enabled - with optimized caching
        recent_history = []
        if should_use_memory:
            try:
                # Performance optimization: Only get history if needed
                # Get formatted history - uses internal caching for performance
                history_start_time = time.time()
                recent_history = _get_formatted_history(conversation_id)
                history_duration = time.time() - history_start_time
                
                # Log history processing time for performance monitoring
                logger.info(f"History processing took {history_duration:.4f}s for {len(recent_history)} messages")
                
                if recent_history:
                    logger.info(f"Including {len(recent_history)} previous messages for context")
                else:
                    logger.info("No previous messages to include")
            except Exception as e:
                # Log error but continue without history
                logger.error(f"Error retrieving conversation history: {str(e)}")
                logger.info("Continuing without conversation history")
                recent_history = []
        
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
        
        # Process the query with conversation history if memory is enabled
        if should_use_memory and recent_history:
            logger.info(f"Sending query with {len(recent_history)} history messages")
            result = agent.query(query, use_web_search=use_web_search, conversation_history=recent_history)
        else:
            logger.info("Sending query without conversation history")
            result = agent.query(query, use_web_search=use_web_search)
        
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
                "conversation_id": conversation_id
            }
            
            try:
                add_to_cache(query, cache_data, cache_metadata)
            except Exception as e:
                logger.error(f"Error adding to cache: {str(e)}")
        
        logger.info(f"Processed query in {duration:.2f}s")
        return answer, conversation_id, thinking_steps if thinking_steps else result.get("thinking_steps", []), documents, duration
    
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}", exc_info=True)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Return a simple error message
        answer = f"I encountered an error processing your request. Please try again."
        add_message_to_history(conversation_id, "assistant", answer)
        
        return answer, conversation_id, [], [], duration 