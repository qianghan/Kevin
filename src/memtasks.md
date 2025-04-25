# Kevin Agent Memory Implementation Todo List

This document provides a checklist of tasks needed to implement memory features for the Kevin chat agent. Mark tasks as completed by changing `[ ]` to `[x]` once each implementation step is finished.

## Core Implementation Tasks

### Task 1: Modify `process_chat` to Include Conversation History
- [ ] 1.1. Locate `process_chat` function in `src/api/services/chat.py`
- [ ] 1.2. Add code to retrieve conversation history
- [ ] 1.3. Modify function to pass history to agent.query
- [ ] 1.4. Add logging for context inclusion

```python
def process_chat(
    query: str,
    use_web_search: bool = False,
    conversation_id: Optional[str] = None,
    callback_handler: Optional[Any] = None
) -> Tuple[str, str, List[Dict[str, Any]], List[Dict[str, Any]], float]:
    # Existing code to get or create conversation_id
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        logger.info(f"Created new conversation: {conversation_id}")
    else:
        logger.info(f"Using existing conversation: {conversation_id}")
    
    # Add the user message to the conversation history
    add_message_to_history(conversation_id, "user", query)
    
    # NEW: Get conversation history for context
    # Limit to last 10 messages to manage token usage
    history = get_conversation_history(conversation_id)
    recent_history = history[-10:] if len(history) > 10 else history
    logger.info(f"Including {len(recent_history)} previous messages for context")
    
    # Rest of function remains the same until the agent.query call
    
    # Process the query with conversation history
    result = agent.query(
        query, 
        use_web_search=use_web_search, 
        conversation_history=recent_history
    )
    
    # Remaining code stays the same
```

### Task 2: Update Agent Query Method
- [ ] 2.1. Locate `query` method in `UniversityAgent` class in `src/core/agent.py`
- [ ] 2.2. Add `conversation_history` parameter
- [ ] 2.3. Implement conversion of history to message objects
- [ ] 2.4. Update state initialization to include history messages

```python
def query(self, question: str, use_web_search: bool = False, conversation_history=None) -> Dict[str, Any]:
    """
    Process a query through the agent.
    
    Args:
        question: The query to process
        use_web_search: Whether to use web search
        conversation_history: Optional list of previous messages
            
    Returns:
        Dict containing the answer and other information
    """
    # Generate a unique ID for this query
    query_id = f"query_{int(time.time())}"
    logger.info(f"Processing query ID {query_id}: {question}")
    
    # Initialize messages with conversation history if available
    messages = []
    if conversation_history:
        logger.info(f"Including {len(conversation_history)} previous messages for context")
        for msg in conversation_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    
    # Add current question
    messages.append(HumanMessage(content=question))
    
    # Initialize state with full message history
    state = {
        "messages": messages,
        "documents": [],
        "web_documents": [],
        "has_answered": False,
        "use_web_search": use_web_search,
        "query": question,
        "search_starttime": time.time(),
        "thinking_steps": [],
        "output": None,
        "answer": None,
        "response": None
    }
    
    # Rest of the method remains unchanged
```

### Task 3: Enhance Prompt Creation
- [ ] 3.1. Locate `create_prompt_for_llm` function in `src/core/agent.py`
- [ ] 3.2. Modify function signature to accept messages parameter
- [ ] 3.3. Add code to format conversation history in prompt
- [ ] 3.4. Restructure prompt creation to use sectioned format

```python
def create_prompt_for_llm(query: str, documents: List[Document], messages=None) -> str:
    """Create a prompt for the LLM based on the query, retrieved documents, and conversation history."""
    # Define maximum content length for documents
    MAX_DOCUMENT_CONTENT_LENGTH = 800  # Characters per document
    MAX_TOTAL_DOCUMENT_LENGTH = 6000   # Total characters for all documents
    
    # Format documents with limited content length
    formatted_docs = []
    total_length = 0
    
    for i, doc in enumerate(documents):
        # Existing document formatting code
        # ...
    
    # Combine formatted documents
    prompt_parts = []
    
    # System instruction
    prompt_parts.append("You are a helpful AI assistant that answers questions based on provided documents and conversation history. Provide accurate information and acknowledge when you don't know something.")
    
    # Add documents section if available
    if formatted_docs:
        prompt_parts.append("\n\nRELEVANT DOCUMENTS:")
        prompt_parts.extend(formatted_docs)
    
    # NEW: Add conversation context if available
    if messages and len(messages) > 1:  # More than just the current query
        prompt_parts.append("\n\nCONVERSATION HISTORY:")
        # Format the conversation history excluding the current query
        for i, msg in enumerate(messages[:-1]):
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            content = msg.content
            # Truncate very long messages
            if len(content) > 500:
                content = content[:500] + "..."
            prompt_parts.append(f"{role}: {content}")
    
    # Add current query section
    prompt_parts.append("\n\nCURRENT QUERY:")
    prompt_parts.append(f"User: {query}")
    
    # Add final instruction
    prompt_parts.append("\n\nPlease provide a helpful response to the current query, taking into account the conversation history and relevant documents. If the documents don't contain relevant information, use your general knowledge but make it clear when you're doing so.")
    
    # Combine all parts
    return "\n".join(prompt_parts)
```

### Task 4: Update Generate Answer Function
- [ ] 4.1. Locate `generate_answer` function in `src/core/agent.py`
- [ ] 4.2. Modify call to `create_prompt_for_llm` to pass messages
- [ ] 4.3. Ensure no other prompt-building logic is affected

```python
# Find this code in generate_answer:
prompt = create_prompt_for_llm(query, documents)

# Replace it with:
prompt = create_prompt_for_llm(
    query, 
    documents, 
    state.get("messages", [])
)
```

## Testing Tasks

### Task 5: Test Basic Memory Functionality
- [ ] 5.1. Test multi-turn conversation with reference resolution
  - Example: Ask "What courses are offered in Computer Science?"
  - Then follow up with "Tell me more about the advanced ones"
  
### Task 6: Test Reference Resolution
- [ ] 6.1. Test entity reference across turns
  - Example: Ask "Who is the president of the university?"
  - Then ask "When did they start their term?"

### Task 7: Test Long Conversations
- [ ] 7.1. Create a 10+ turn conversation about a consistent topic
- [ ] 7.2. Verify context is maintained throughout
- [ ] 7.3. Check for any performance degradation

### Task 8: Test Context Window Management
- [ ] 8.1. Simulate a conversation that would exceed token limits
- [ ] 8.2. Verify older messages are properly truncated
- [ ] 8.3. Confirm most recent and relevant context is preserved

## Optional Enhancement Tasks (Future)

### Task 9: Implement Conversation Summarization
- [ ] 9.1. Research LLM-based summarization techniques
- [ ] 9.2. Design summary storage and retrieval mechanism
- [ ] 9.3. Implement summarization for long conversations

### Task 10: Develop Adaptive Context Selection
- [ ] 10.1. Create relevance scoring for historic messages
- [ ] 10.2. Implement dynamic context selection logic
- [ ] 10.3. Test with complex, multi-topic conversations

### Task 11: Enhance Memory Persistence
- [ ] 11.1. Design schema for advanced conversation state
- [ ] 11.2. Implement entity and topic extraction
- [ ] 11.3. Create persistent storage for semantic memory

## Completion Criteria

A task can be marked complete when:
1. The code changes have been implemented
2. Unit tests pass (where applicable)
3. The functionality works correctly in an end-to-end test

## Implementation Notes

- Changes should maintain the existing architecture and backward compatibility
- Monitor token usage as conversation history grows
- Consider limiting message inclusion based on relevance if performance issues arise
- All modifications should follow the project's existing coding standards 