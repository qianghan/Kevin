"""
JSON schema definitions for chat-related models.

These schemas are used for validating API requests and responses.
"""

# Chat message schema
chat_message_schema = {
    "type": "object",
    "required": ["id", "conversationId", "content", "role", "createdAt"],
    "properties": {
        "id": {
            "type": "string",
            "format": "uuid",
            "description": "Unique identifier for the message"
        },
        "conversationId": {
            "type": "string",
            "format": "uuid",
            "description": "ID of the conversation this message belongs to"
        },
        "content": {
            "type": "string",
            "description": "Content of the message"
        },
        "role": {
            "type": "string",
            "enum": ["user", "assistant"],
            "description": "Role of the message sender"
        },
        "createdAt": {
            "type": "string",
            "format": "date-time",
            "description": "When the message was created"
        },
        "metadata": {
            "type": "object",
            "description": "Additional metadata about the message"
        }
    }
}

# Chat conversation schema
chat_conversation_schema = {
    "type": "object",
    "required": ["id", "userId", "title", "createdAt", "updatedAt"],
    "properties": {
        "id": {
            "type": "string",
            "format": "uuid",
            "description": "Unique identifier for the conversation"
        },
        "userId": {
            "type": "string",
            "format": "uuid",
            "description": "ID of the user who owns this conversation"
        },
        "title": {
            "type": "string",
            "description": "Title of the conversation"
        },
        "messages": {
            "type": "array",
            "items": chat_message_schema,
            "description": "Messages in the conversation"
        },
        "createdAt": {
            "type": "string",
            "format": "date-time",
            "description": "When the conversation was created"
        },
        "updatedAt": {
            "type": "string",
            "format": "date-time",
            "description": "When the conversation was last updated"
        }
    }
}

# Chat query request schema
chat_query_request_schema = {
    "type": "object",
    "required": ["query"],
    "properties": {
        "query": {
            "type": "string",
            "description": "The query to process"
        },
        "conversationId": {
            "type": "string",
            "format": "uuid",
            "description": "ID of an existing conversation to continue"
        },
        "stream": {
            "type": "boolean",
            "default": False,
            "description": "Whether to stream the response"
        },
        "useWebSearch": {
            "type": "boolean",
            "default": False,
            "description": "Whether to use web search for answering the query"
        }
    }
}

# Chat query response schema
chat_query_response_schema = {
    "type": "object",
    "required": ["answer", "conversationId", "durationSeconds"],
    "properties": {
        "answer": {
            "type": "string",
            "description": "The answer to the query"
        },
        "conversationId": {
            "type": "string",
            "format": "uuid",
            "description": "The conversation ID"
        },
        "thinkingSteps": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["description"],
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of the thinking step"
                    },
                    "duration": {
                        "type": "number",
                        "description": "Duration of the step in seconds"
                    },
                    "result": {
                        "description": "Result of the thinking step"
                    },
                    "error": {
                        "type": "string",
                        "description": "Error message if the step failed"
                    }
                }
            },
            "description": "The thinking steps used to generate the answer"
        },
        "documents": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["content", "metadata"],
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The content of the document"
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Metadata about the document"
                    }
                }
            },
            "description": "The documents retrieved during processing"
        },
        "durationSeconds": {
            "type": "number",
            "description": "Time taken to process the query"
        }
    }
}

# List conversations request schema
list_conversations_schema = {
    "type": "object",
    "properties": {
        "page": {
            "type": "integer",
            "minimum": 1,
            "default": 1,
            "description": "Page number"
        },
        "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "default": 20,
            "description": "Number of items per page"
        },
        "sortBy": {
            "type": "string",
            "enum": ["createdAt", "updatedAt", "title"],
            "default": "updatedAt",
            "description": "Field to sort by"
        },
        "sortDirection": {
            "type": "string",
            "enum": ["asc", "desc"],
            "default": "desc",
            "description": "Sort direction"
        }
    }
}

# List conversations response schema
list_conversations_response_schema = {
    "type": "object",
    "required": ["items", "total", "page", "limit", "pages"],
    "properties": {
        "items": {
            "type": "array",
            "items": chat_conversation_schema,
            "description": "Conversations in the current page"
        },
        "total": {
            "type": "integer",
            "description": "Total number of conversations"
        },
        "page": {
            "type": "integer",
            "description": "Current page number"
        },
        "limit": {
            "type": "integer",
            "description": "Number of items per page"
        },
        "pages": {
            "type": "integer",
            "description": "Total number of pages"
        }
    }
} 