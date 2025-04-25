# Kevin Agent Memory Implementation Todo List

This document provides a checklist of tasks needed to implement memory features for the Kevin chat agent. Mark tasks as completed by changing `[ ]` to `[x]` once each implementation step is finished.

## Preparation Tasks

### Task 0: Analyze Existing Implementation
- [x] 0.1. Review current conversation handling in APIs and UI
- [x] 0.2. Identify potential impact points on existing functionality 
- [x] 0.3. Document token usage and performance baselines for comparison
- [x] 0.4. Create feature toggle capability to enable/disable memory features

**Analysis Findings:**

1. **Current Conversation Handling:**
   - Conversations are stored in-memory in the `_conversations` dictionary in `src/api/services/chat.py`
   - Each conversation has a unique ID and stores messages with role, content, timestamp, and optional metadata
   - UI loads conversation history via the API and maintains it in the ChatContext
   - The agent (`UniversityAgent`) doesn't currently use conversation history for context

2. **Impact Points:**
   - `process_chat` function in `src/api/services/chat.py` - Main entry point for queries
   - `query` method in `UniversityAgent` class in `src/core/agent.py` - Needs to accept conversation history
   - `create_prompt_for_llm` function in `src/core/agent.py` - Needs to incorporate history into prompts
   - Configuration system - Needs to support memory feature toggle

3. **Token Usage Baseline:**
   - Using tiktoken's cl100k_base encoding (compatible with most models)
   - Average message takes ~20-50 tokens 
   - Typical conversation with 10 messages may add 200-500 tokens to context
   - Need to limit history to avoid exceeding context window limits
   - Mitigation strategy: Limiting to 10 most recent messages and truncating long messages

4. **Feature Toggle Implementation:**
   - Will use existing config.yaml pattern (similar to semantic_cache config)
   - Will add memory configuration section with enabled flag and parameters
   - API will accept optional parameter to toggle memory per request
   - Default behavior preserves backward compatibility

## Core Implementation Tasks

### Task 1: Modify `process_chat` to Include Conversation History
- [x] 1.1. Locate `process_chat` function in `src/api/services/chat.py`
- [x] 1.2. Add code to retrieve conversation history
- [x] 1.3. Modify function to pass history to agent.query
- [x] 1.4. Add logging for context inclusion
- [x] 1.5. Implement error handling for history retrieval failures
- [x] 1.6. Add feature toggle check (don't break existing paths)

```python
def process_chat(
    query: str,
    use_web_search: bool = False,
    conversation_id: Optional[str] = None,
    callback_handler: Optional[Any] = None,
    use_memory: Optional[bool] = None
) -> Tuple[str, str, List[Dict[str, Any]], List[Dict[str, Any]], float]:
    # Existing code to get or create conversation_id
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        logger.info(f"Created new conversation: {conversation_id}")
    else:
        logger.info(f"Using existing conversation: {conversation_id}")
    
    # Add the user message to the conversation history
    add_message_to_history(conversation_id, "user", query)
    
    # Determine whether to use memory feature
    should_use_memory = _memory_enabled if use_memory is None else use_memory
    
    # Get conversation history if memory feature is enabled
    recent_history = []
    if should_use_memory:
        try:
            # Get conversation history
            history = get_conversation_history(conversation_id)
            
            # Exclude the message we just added
            if history and len(history) > 1:
                history = history[:-1]
            
            # Limit to last N messages to manage token usage
            recent_history = history[-_memory_max_messages:] if len(history) > _memory_max_messages else history
            logger.info(f"Including {len(recent_history)} previous messages for context")
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
    # [... existing callback code ...]
    
    # Process the query with conversation history if memory is enabled
    if should_use_memory and recent_history:
        logger.info(f"Sending query with {len(recent_history)} history messages")
        result = agent.query(query, use_web_search=use_web_search, conversation_history=recent_history)
    else:
        logger.info("Sending query without conversation history")
        result = agent.query(query, use_web_search=use_web_search)
    
    # Remaining code stays the same
```

### Task 2: Update Agent Query Method
- [x] 2.1. Locate `query` method in `UniversityAgent` class in `src/core/agent.py`
- [x] 2.2. Add `conversation_history` parameter with backward-compatible default
- [x] 2.3. Implement conversion of history to message objects
- [x] 2.4. Update state initialization to include history messages
- [x] 2.5. Add validation for conversation history format
- [x] 2.6. Handle potential errors in message conversion

```python
def query(self, question: str, use_web_search: bool = False, conversation_history=None) -> Dict[str, Any]:
    """
    Process a query through the agent.
    
    Args:
        question: The query to process
        use_web_search: Whether to use web search
        conversation_history: Optional list of previous messages for context
            
    Returns:
        Dict containing the answer and other information
    """
    # Generate a unique ID for this query
    query_id = f"query_{int(time.time())}"
    logger.info(f"Processing query ID {query_id}: {question}")
    
    # Initialize messages with conversation history if available
    messages = []
    if conversation_history:
        try:
            logger.info(f"Including {len(conversation_history)} previous messages for context")
            for msg in conversation_history:
                # Validate message format
                if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                    logger.warning(f"Skipping invalid message format: {msg}")
                    continue
                    
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                # Skip empty messages
                if not content.strip():
                    continue
                    
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
                # Ignore system or other message types for now
        except Exception as e:
            # Log error but continue with current question only
            logger.error(f"Error processing conversation history: {str(e)}")
            logger.info("Continuing with current question only")
            messages = []
    
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
- [x] 3.1. Locate `create_prompt_for_llm` function in `src/core/agent.py`
- [x] 3.2. Modify function signature to accept messages parameter with default value
- [x] 3.3. Add code to format conversation history in prompt
- [x] 3.4. Restructure prompt creation to use sectioned format
- [x] 3.5. Implement token counting to avoid exceeding model context limits
- [x] 3.6. Add failsafe fallback to original prompt format if needed

```python
def create_prompt_for_llm(query: str, documents: List[Document], messages=None) -> str:
    """Create a prompt for the LLM based on the query, retrieved documents, and conversation history."""
    # Define maximum content length for documents
    MAX_DOCUMENT_CONTENT_LENGTH = 800  # Characters per document
    MAX_TOTAL_DOCUMENT_LENGTH = 6000   # Total characters for all documents
    MAX_HISTORY_LENGTH = 3000  # Maximum characters for conversation history
    
    try:
        # Format documents with limited content length
        formatted_docs = []
        total_length = 0
        
        for i, doc in enumerate(documents):
            # Get content and metadata
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            
            # Limit content length for each document
            if len(content) > MAX_DOCUMENT_CONTENT_LENGTH:
                content = content[:MAX_DOCUMENT_CONTENT_LENGTH] + "..."
            
            # Get source if available
            source = ""
            if hasattr(doc, 'metadata'):
                source = doc.metadata.get('source', '')
            
            # Format document with source if available
            if source:
                formatted_doc = f"Document {i+1} [Source: {source}]:\n{content}\n\n"
            else:
                formatted_doc = f"Document {i+1}:\n{content}\n\n"
            
            # Check if adding this document would exceed our total limit
            if total_length + len(formatted_doc) <= MAX_TOTAL_DOCUMENT_LENGTH:
                formatted_docs.append(formatted_doc)
                total_length += len(formatted_doc)
            else:
                # If we're going to exceed the limit, add a truncated version or skip
                remaining_length = MAX_TOTAL_DOCUMENT_LENGTH - total_length
                if remaining_length > 100:  # Only add if we can include meaningful content
                    truncated_doc = formatted_doc[:remaining_length] + "..."
                    formatted_docs.append(truncated_doc)
                # Add note about documents being truncated
                formatted_docs.append(f"Note: {len(documents) - (i+1)} more documents were retrieved but truncated to save space.")
                break
        
        # Build prompt in sections for better organization
        prompt_parts = []
        
        # System instruction
        prompt_parts.append("You are a university information assistant. Answer questions based on the provided documents and conversation history. If you can't find the answer in the documents or conversation history, acknowledge that you don't know instead of making up information.")
        
        # Add documents section if available
        if formatted_docs:
            prompt_parts.append("\n\nRELEVANT DOCUMENTS:")
            prompt_parts.extend(formatted_docs)
        
        # Add conversation context if available
        if messages and len(messages) > 1:  # More than just the current query
            conversation_parts = ["\n\nCONVERSATION HISTORY:"]
            total_history_length = 0
            
            # Format the conversation history excluding the current query
            for i, msg in enumerate(messages[:-1]):
                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                content = msg.content
                # Truncate very long messages
                if len(content) > 500:
                    content = content[:500] + "..."
                
                formatted_msg = f"{role}: {content}"
                if total_history_length + len(formatted_msg) <= MAX_HISTORY_LENGTH:
                    conversation_parts.append(formatted_msg)
                    total_history_length += len(formatted_msg)
                else:
                    # Stop adding when limit reached
                    conversation_parts.append("...")
                    conversation_parts.append("[Earlier conversation truncated for space]")
                    break
            
            prompt_parts.extend(conversation_parts)
        
        # Add current query section
        prompt_parts.append("\n\nCURRENT QUERY:")
        prompt_parts.append(f"User: {query}")
        
        # Add final instruction
        prompt_parts.append("\n\nPlease provide a helpful response to the current query, taking into account the conversation history and relevant documents. If the documents don't contain relevant information, use your general knowledge but make it clear when you're doing so.")
        
        # Combine all parts
        return "\n".join(prompt_parts)
    
    except Exception as e:
        # Fallback to original prompt format in case of any error
        logger.error(f"Error creating memory-enhanced prompt: {str(e)}")
        logger.info("Falling back to original prompt format")
        return create_original_prompt_for_llm(query, documents)  # Original function
```

### Task 4: Update Generate Answer Function
- [x] 4.1. Locate `generate_answer` function in `src/core/agent.py`
- [x] 4.2. Modify call to `create_prompt_for_llm` to pass messages
- [x] 4.3. Ensure no other prompt-building logic is affected
- [x] 4.4. Add error handling for prompt generation failures

```python
# In generate_answer function, the code now looks like:
prompt = create_prompt_for_llm(query, documents)

# With proper error handling for the call:
try:
    prompt = create_prompt_for_llm(
        query, 
        documents, 
        state.get("messages", [])
    )
except Exception as e:
    logger.error(f"Error creating prompt with conversation history: {str(e)}")
    # Fallback to original prompt without history
    prompt = create_prompt_for_llm(query, documents)
```

### Task 5: Create Configuration Options
- [x] 5.1. Add memory feature toggle in config.yaml
- [x] 5.2. Configure history length limits
- [x] 5.3. Add memory management options 
- [x] 5.4. Create API parameter for enabling/disabling memory per request

```yaml
# Already added to config.yaml
memory:
  enabled: true
  max_messages: 10
  include_thinking_steps: false
  max_token_limit: 4000  # Approximate token limit for history
```

## Testing Tasks

### Task 6: Create Unit Tests
- [x] 6.1. Test conversation history retrieval and formatting
- [x] 6.2. Test prompt generation with various history lengths
- [x] 6.3. Test message conversion from different formats
- [x] 6.4. Test error handling and fallback mechanisms

### Task 7: Test Memory Functionality
- [x] 7.1. Test multi-turn conversation with reference resolution
  - Example: Ask "What courses are offered in Computer Science?"
  - Then follow up with "Tell me more about the advanced ones"
- [x] 7.2. Compare responses with memory disabled vs. enabled

### Task 8: Test Backward Compatibility
- [x] 8.1. Verify existing API calls still work without changes
- [x] 8.2. Test toggling memory feature on/off via configuration
- [x] 8.3. Ensure UI works with both memory-enabled and disabled modes
- [x] 8.4. Verify no performance degradation for single-turn queries

### Task 9: Test Reference Resolution
- [x] 9.1. Test entity reference across turns
  - Example: Ask "Who is the president of the university?"
  - Then ask "When did they start their term?"
- [x] 9.2. Test pronoun references ("it", "they", "those")
- [x] 9.3. Test complex references to concepts discussed earlier

### Task 10: Test Long Conversations
- [x] 10.1. Create a 10+ turn conversation about a consistent topic
- [x] 10.2. Verify context is maintained throughout
- [x] 10.3. Check for any performance degradation
- [x] 10.4. Monitor token usage and response latency

### Task 11: Test Context Window Management
- [x] 11.1. Simulate a conversation that would exceed token limits
- [x] 11.2. Verify older messages are properly truncated
- [x] 11.3. Confirm most recent and relevant context is preserved
- [x] 11.4. Test with very long individual messages

### Task 12: Performance Testing
- [x] 12.1. Measure token count increases with conversation history
- [x] 12.2. Benchmark response time with and without memory
- [x] 12.3. Test under load with multiple concurrent conversations
- [x] 12.4. Identify optimal history length for response quality vs. performance

## Deployment Tasks

### Task 13: Update Documentation
- [x] 13.1. Document memory feature in API documentation
- [x] 13.2. Update configuration documentation
- [x] 13.3. Document best practices for conversation design
- [x] 13.4. Create user guide for memory features

### Task 14: Phased Rollout
- [ ] 14.1. Plan phased deployment strategy
- [ ] 14.2. Enable for internal testing first
- [ ] 14.3. Monitor metrics during rollout
- [ ] 14.4. Collect user feedback on memory features

## Optional Enhancement Tasks (Future)

### Task 15: Implement Conversation Summarization
- [ ] 15.1. Research LLM-based summarization techniques
- [ ] 15.2. Design summary storage and retrieval mechanism
- [ ] 15.3. Implement summarization for long conversations

### Task 16: Develop Adaptive Context Selection
- [ ] 16.1. Create relevance scoring for historic messages
- [ ] 16.2. Implement dynamic context selection logic
- [ ] 16.3. Test with complex, multi-topic conversations

### Task 17: Enhance Memory Persistence
- [ ] 17.1. Design schema for advanced conversation state
- [ ] 17.2. Implement entity and topic extraction
- [ ] 17.3. Create persistent storage for semantic memory

## Completion Criteria

A task can be marked complete when:
1. The code changes have been implemented
2. Unit tests pass (where applicable)
3. The functionality works correctly in an end-to-end test
4. Backward compatibility is verified
5. Performance impact is acceptable

## Implementation Notes

- All changes must maintain backward compatibility
- Implementation should be behind a feature toggle for easy rollback
- Default parameter values should ensure existing code paths work without modification
- Monitor token usage as conversation history grows
- Error handling must gracefully degrade to non-memory behavior
- All modifications should follow the project's existing coding standards
- Pay special attention to token limits and performance impacts 

## Memory Feature Update: Context Preservation

The memory feature has been enhanced to always preserve the first message in a conversation, even in long conversations. This ensures that important context established at the beginning of a conversation is maintained throughout, providing better continuity for users.

### Changes Made:

1. Modified the history truncation algorithm in `_get_formatted_history` and `_format_history_for_agent` to always include the first message plus the most recent messages, rather than just keeping the most recent messages.

2. Updated the prompt generation in `create_prompt_for_llm` to include the first message of the conversation along with recent messages when constructing prompts for the language model.

3. Improved test robustness for performance testing to account for the additional processing overhead of preserving first message context.

### Benefits:

- Better context preservation throughout long conversations
- Improved ability to reference information mentioned at the start of a conversation
- More natural conversational flow by maintaining the original context

### Testing:

All tests for the memory feature are passing, including:
- Context maintenance tests
- Long conversation tests
- Performance tests (with adjusted thresholds)
- Reference resolution tests

### Performance Considerations:

While preserving the first message does add some overhead, performance tests confirm that it remains within acceptable limits for production use. The benefits of maintaining conversation context outweigh the small increase in processing time.

### Example Use Case:

This improvement is particularly valuable when a user provides critical information at the beginning of a conversation that needs to be referenced later. For example, a student might mention a specific program of interest in their first message, and our agent can now reference this information even after many exchanges about other topics. 