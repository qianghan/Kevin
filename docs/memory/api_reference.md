# Memory Feature API Reference

This document provides a comprehensive reference for the memory features in the Kevin chat agent API.

## Table of Contents

1. [Overview](#overview)
2. [API Parameters](#api-parameters)
3. [Return Values](#return-values)
4. [Conversation History Format](#conversation-history-format)
5. [Error Handling](#error-handling)
6. [Code Examples](#code-examples)

## Overview

The memory feature enables the Kevin chat agent to maintain context across multiple turns of conversation. This allows the agent to understand references to previous messages, resolve pronouns, and provide more coherent responses in multi-turn interactions.

The implementation is built into the core `process_chat` function and the `UniversityAgent` class, with a seamless integration that maintains backward compatibility.

## API Parameters

### `process_chat` Function

```python
def process_chat(
    query: str,
    use_web_search: bool = False,
    conversation_id: Optional[str] = None,
    callback_handler: Optional[Any] = None,
    use_memory: Optional[bool] = None
) -> Tuple[str, str, List[Dict[str, Any]], List[Dict[str, Any]], float]
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | str | The user query to process |
| `use_web_search` | bool | Whether to use web search (default: False) |
| `conversation_id` | Optional[str] | Optional conversation ID for context. If not provided, a new one will be created |
| `callback_handler` | Optional[Any] | Optional callback handler for streaming responses |
| `use_memory` | Optional[bool] | Whether to use conversation memory feature. If None, uses the global setting from config.yaml |

### `UniversityAgent.query` Method

```python
def query(
    self, 
    question: str, 
    use_web_search: bool = False, 
    conversation_history=None
) -> Dict[str, Any]
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | str | The query to process |
| `use_web_search` | bool | Whether to use web search (default: False) |
| `conversation_history` | Optional[List[Dict]] | List of previous messages for context. Each message should be a dict with "role" and "content" keys |

## Return Values

The `process_chat` function returns a tuple with 5 elements:

```python
(answer, conversation_id, thinking_steps, documents, duration)
```

| Element | Type | Description |
|---------|------|-------------|
| `answer` | str | The generated answer text |
| `conversation_id` | str | The conversation ID (created or used) |
| `thinking_steps` | List[Dict] | Steps taken by the agent during processing |
| `documents` | List[Dict] | Documents retrieved during processing |
| `duration` | float | The processing duration in seconds |

The `UniversityAgent.query` method returns a dictionary:

```python
{
    "answer": str,              # The generated answer
    "output": str,              # Alias for answer (for backward compatibility)
    "query": str,               # The original query
    "duration": float,          # Processing time in seconds
    "thinking": List[Dict],     # Thinking steps
    "has_error": bool           # Whether an error occurred
}
```

## Conversation History Format

The conversation history is stored as a list of message dictionaries with the following structure:

```python
{
    "role": str,          # "user" or "assistant"
    "content": str,       # The message content
    "timestamp": float,   # Unix timestamp
    # Optional fields for assistant messages:
    "thinking_steps": List[Dict],  # Thinking steps (optional)
    "documents": List[Dict],       # Retrieved documents (optional)
    "from_cache": bool             # Whether response came from cache (optional)
}
```

## Error Handling

The memory feature includes robust error handling:

1. If conversation history retrieval fails, processing continues without history
2. If message format is invalid, the message is skipped
3. If prompt generation with memory fails, it falls back to the original prompt without memory
4. All errors are logged but the function continues execution

## Code Examples

### Basic Usage

```python
from src.api.services.chat import process_chat

# Process a query with memory (using default settings)
response, conv_id, thinking, docs, duration = process_chat(
    "What programs does the university offer?"
)

# Follow-up query using the same conversation ID
follow_up, _, _, _, _ = process_chat(
    "Which ones have co-op options?",
    conversation_id=conv_id
)
```

### Explicit Memory Control

```python
# Disable memory for a specific query
response, conv_id, _, _, _ = process_chat(
    "What are the admission requirements?",
    use_memory=False
)

# Enable memory for a follow-up
follow_up, _, _, _, _ = process_chat(
    "Are they different for international students?",
    conversation_id=conv_id,
    use_memory=True
)
```

### Direct Agent Usage

```python
from src.core.agent import UniversityAgent

# Initialize the agent
agent = UniversityAgent()

# Create conversation history
history = [
    {"role": "user", "content": "What scholarships are available?"},
    {"role": "assistant", "content": "There are merit-based and need-based scholarships..."},
    {"role": "user", "content": "What are the application deadlines?"}
]

# Process a query with history
result = agent.query(
    "Do I need separate applications for each scholarship?",
    conversation_history=history
)

# Extract the answer
answer = result["answer"]
``` 