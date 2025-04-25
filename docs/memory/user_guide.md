# Memory Feature User Guide

This guide explains how to use the conversation memory features in the Kevin chat agent system from a user perspective.

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Basic Concepts](#basic-concepts)
4. [Using Memory Features](#using-memory-features)
5. [Common Use Cases](#common-use-cases)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

## Introduction

The Kevin chat agent now includes memory features that allow it to remember the context of your conversation across multiple messages. This enables more natural, flowing conversations where you can ask follow-up questions without having to repeat information.

## Getting Started

The memory feature is enabled by default, so you can start using it immediately. When you ask a question, the agent will respond as usual. When you ask a follow-up question, the agent will automatically use the context from your previous interactions to provide a relevant response.

### Example:

```
You: What undergraduate programs does UBC offer in Computer Science?
Kevin: UBC offers several undergraduate Computer Science programs including...

You: Which ones have co-op opportunities?
Kevin: Among UBC's Computer Science programs, the following offer co-op opportunities...
```

Notice that in the second question, you didn't need to specify that you were asking about UBC's Computer Science programs - the agent remembered this from the previous exchange.

## Basic Concepts

### Conversation ID

Each conversation has a unique identifier (ID) that helps the system keep track of your interactions. This ID is generated automatically when you start a new conversation, and it's used to retrieve your conversation history when you send follow-up messages.

### Conversation History

The conversation history includes both your messages and the agent's responses, stored in chronological order. By default, the agent remembers the last 10 messages in your conversation, but this can be configured differently depending on your specific setup.

### Message Context

The context includes not just the text of messages, but also:
- The role of each message (user or assistant)
- The timestamp of each message
- Any associated documents or thinking steps

## Using Memory Features

### Starting a New Conversation

To start a new conversation, simply send a message without specifying a conversation ID. The system will generate a new ID automatically.

```python
from src.api.services.chat import process_chat

# Start a new conversation
response, conversation_id, thinking_steps, documents, duration = process_chat(
    "What admission requirements does UBC have?"
)

# The conversation_id can be saved and used for future messages
print(f"Conversation ID: {conversation_id}")
```

### Continuing a Conversation

To continue an existing conversation, provide the conversation ID when sending your message:

```python
# Continue the previous conversation
follow_up, _, _, _, _ = process_chat(
    "Are the requirements different for international students?",
    conversation_id=conversation_id
)
```

### Controlling Memory Usage

You can explicitly enable or disable the memory feature for specific queries:

```python
# Disable memory for this specific query
response = process_chat(
    "What are the general admission requirements for Canadian universities?",
    conversation_id=conversation_id,
    use_memory=False
)

# Enable memory for this query (even if globally disabled)
response = process_chat(
    "Tell me more about UBC specifically",
    conversation_id=conversation_id,
    use_memory=True
)
```

## Common Use Cases

### Multi-Turn Information Gathering

Break down complex information needs into a series of simpler questions:

```
You: What scholarships are available at UBC?
Kevin: [Lists available scholarships]

You: Which ones are available for international students?
Kevin: [Filters to international scholarships]

You: What are the application deadlines?
Kevin: [Provides deadlines for the previously mentioned international scholarships]
```

### Follow-Up Questions with Pronouns

Use pronouns to refer to previously mentioned entities:

```
You: Who is the current president of UBC?
Kevin: [Provides information about the president]

You: When did they start their term?
Kevin: [Provides the start date of the president's term]
```

### Complex Reference Resolution

The system can handle more complex references to previous content:

```
You: What are the differences between UBC and McGill's Computer Science programs?
Kevin: [Compares the programs]

You: Which would you recommend for someone interested in AI research?
Kevin: [Provides recommendation based on AI research strengths]
```

## Troubleshooting

### Memory Limitations

The system has some limitations to be aware of:

1. **Limited History** - By default, only the last 10 messages are remembered
2. **Recency Bias** - The system may prioritize more recent messages
3. **Context Window Limits** - Very long conversations may see older messages truncated

### Solutions:

- If the agent seems to have forgotten important context, try rephrasing your question with more explicit references
- For very long conversations, consider summarizing key points or starting a new conversation
- Use specific references rather than vague pronouns for important information

## FAQ

### How long does the system remember my conversation?

The system remembers the most recent messages in your conversation (typically the last 10 messages). The exact number can be configured by system administrators.

### Do I need to enable memory features explicitly?

No, the memory feature is enabled by default. You can disable it for specific queries if needed.

### Can I retrieve my conversation history?

Yes, the conversation history can be retrieved using the conversation ID. This feature would typically be implemented in a user interface where you can view your past conversations.

### Is my conversation data stored securely?

Yes, conversation data is stored securely. In the current implementation, conversations are stored in memory on the server. In a production environment, conversations would typically be stored in a secure database with appropriate access controls.

### Does the memory feature slow down responses?

The memory feature adds a small amount of overhead to response generation, but it's typically negligible for most applications. For very long conversations, there might be a slight increase in response time, but this is usually outweighed by the benefits of contextual understanding. 