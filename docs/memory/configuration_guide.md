# Memory Feature Configuration Guide

This document explains how to configure the memory features in the Kevin chat agent.

## Table of Contents

1. [Overview](#overview)
2. [Configuration File](#configuration-file)
3. [Memory Configuration Options](#memory-configuration-options)
4. [Per-Request Configuration](#per-request-configuration)
5. [Environment Variables](#environment-variables)
6. [Examples](#examples)

## Overview

The memory feature allows the chat agent to maintain conversation context across multiple turns. The feature can be configured globally through the `config.yaml` file and overridden on a per-request basis.

## Configuration File

The memory feature settings are defined in the `config.yaml` file in the root directory of the project:

```yaml
# config.yaml

# Other configuration sections...

memory:
  enabled: true           # Global toggle for memory feature
  max_messages: 10        # Maximum number of messages to include in history
  include_thinking_steps: false  # Whether to include thinking steps in context
  max_token_limit: 4000   # Approximate token limit for history
```

## Memory Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Global toggle to enable/disable the memory feature |
| `max_messages` | integer | `10` | Maximum number of messages to include in the conversation history. This helps manage token usage and prevents context windows from being exceeded |
| `include_thinking_steps` | boolean | `false` | Whether to include thinking steps in the context. When true, the agent can reference its own reasoning process |
| `max_token_limit` | integer | `4000` | Approximate maximum token limit for the conversation history. Messages will be truncated to stay within this limit |

## Per-Request Configuration

The memory feature can be enabled or disabled on a per-request basis by using the `use_memory` parameter in the `process_chat` function:

```python
from src.api.services.chat import process_chat

# Enable memory for this request (regardless of global setting)
response = process_chat(
    "What are the admission requirements?",
    use_memory=True
)

# Disable memory for this request (regardless of global setting)
response = process_chat(
    "Tell me about scholarships",
    use_memory=False
)

# Use global setting from config.yaml
response = process_chat(
    "What programs are offered?",
    use_memory=None  # or omit the parameter
)
```

## Environment Variables

You can also use environment variables to override configuration settings:

| Environment Variable | Description |
|----------------------|-------------|
| `KEVIN_MEMORY_ENABLED` | Set to `0` or `false` to disable memory feature, `1` or `true` to enable |
| `KEVIN_MEMORY_MAX_MESSAGES` | Maximum messages to include in history |

Example:

```bash
# Disable memory feature
export KEVIN_MEMORY_ENABLED=0

# Set maximum messages to 5
export KEVIN_MEMORY_MAX_MESSAGES=5

# Run the application
python app.py
```

## Examples

### Basic Configuration

```yaml
# config.yaml
memory:
  enabled: true
  max_messages: 10
```

### Configuration for Production Environment

```yaml
# config.yaml
memory:
  enabled: true
  max_messages: 8
  max_token_limit: 3000  # Reduce token usage in production
  include_thinking_steps: false
```

### Configuration for Development/Testing

```yaml
# config.yaml
memory:
  enabled: true
  max_messages: 20        # Use more context for testing
  max_token_limit: 8000   # Higher limit for testing
  include_thinking_steps: true  # Include thinking for debugging
``` 