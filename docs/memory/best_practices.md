# Memory Feature: Best Practices for Conversation Design

This document outlines best practices for designing conversations that leverage the Kevin chat agent's memory features effectively.

## Table of Contents

1. [Introduction](#introduction)
2. [Designing Multi-Turn Conversations](#designing-multi-turn-conversations)
3. [Managing Context](#managing-context)
4. [Reference Resolution Patterns](#reference-resolution-patterns)
5. [Memory Limitations](#memory-limitations)
6. [Performance Considerations](#performance-considerations)
7. [Testing Strategies](#testing-strategies)

## Introduction

The memory feature allows the Kevin chat agent to maintain context across multiple turns of conversation. When used effectively, this can create more natural, coherent conversations that require less repetition from users. However, there are important considerations to keep in mind for optimal results.

## Designing Multi-Turn Conversations

### Do:
- **Design conversation flows with logical progression** - Build conversations that naturally flow from broad topics to specific details
- **Use clear references to previous information** - When follow-up queries reference previous information, make the connections logical
- **Break complex requests into multiple turns** - Instead of one huge query, use multiple turns to incrementally build context

### Don't:
- **Switch topics abruptly** - Sudden topic changes can confuse the context management
- **Overwhelm with too many questions at once** - This can make it harder for the system to track all information
- **Assume perfect recall** - Very early messages in a long conversation may be truncated

### Example:

**Effective conversation flow:**
```
User: "What undergraduate Computer Science programs does UBC offer?"
Agent: [Responds with CS programs]
User: "Which ones include co-op opportunities?"
Agent: [Responds about co-op options]
User: "What are the admission requirements for those programs?"
```

## Managing Context

### Do:
- **Periodically summarize** - For long conversations, occasionally summarize what's been discussed
- **Explicitly state a topic change** - When changing topics, clearly indicate the shift
- **Use specific references** - Use specific terms rather than vague pronouns when possible

### Don't:
- **Rely on implicit references** - "What about the other ones?" is less clear than "What about the other scholarship options?"
- **Build assumptions on old context** - After 10+ turns, early context may be lost
- **Overload with too much information** - Keep queries focused and manageable

### Example:

**Clear context transitions:**
```
User: "Let's switch from discussing CS programs to talk about housing options. What on-campus housing is available for first-year students?"
```

## Reference Resolution Patterns

### Effective Referencing Patterns:

| Pattern | Example | Notes |
|---------|---------|-------|
| Direct reference | "Tell me more about UBC's Computer Science program" | Most reliable |
| Named entities | "Does the Engineering program have similar requirements?" | Good for comparing |
| Pronouns | "When was it established?" | Works for recent and unambiguous references |
| Implied context | "What are the deadlines?" | Works if context is clear |

### Tips for Reference Resolution:

1. **Use the most specific reference needed** - The more specific, the better the resolution
2. **Prefer entity names over pronouns** for complex conversations
3. **Establish clear antecedents** before using pronouns
4. **Reset context explicitly** when starting a new topic

## Memory Limitations

### Be Aware Of:

1. **Token limits** - Conversation history contributes to token usage, which has limits
2. **Message count limits** - By default, only the last 10 messages are retained
3. **Truncation** - Long messages may be truncated to manage token usage
4. **Recency bias** - Most recent messages have higher weight than older ones

### Strategies:

- For critical context, **restate important information** if it was mentioned many turns ago
- Use **explicit references** for important information
- **Summarize** complex background information in a single message rather than across many turns

## Performance Considerations

### Optimizing Memory Usage:

1. **Be concise** - Keep messages focused and to the point
2. **Avoid repetition** - No need to repeat information the agent already knows
3. **Consider disabling memory** for standalone queries that don't depend on context
4. **Batch related questions** together to minimize turns

### Balance Between Detail and Performance:

- More history provides better context but increases token usage and response time
- Testing showed that 5-10 messages offers the best balance between context and performance
- For complex topics, consider creating a new conversation after 15-20 turns

## Testing Strategies

### Testing Multi-Turn Conversations:

1. **Create test scripts** with predefined conversation flows
2. **Test reference resolution** with different reference types (pronouns, entity names)
3. **Test long conversations** to ensure context is maintained appropriately
4. **Test context boundaries** by referencing information at different distances (1 turn ago, 5 turns ago, etc.)

### Example Test Cases:

- **Pronoun resolution** - "Who is the department head?" → "When did they start in that role?"
- **Entity reference** - "Tell me about CS programs" → "What about Engineering programs?"
- **Implicit references** - "What scholarships are available?" → "What are the deadlines?"
- **Topic switching** - "Tell me about housing" → [5 turns later] → "Going back to academics, what programs are offered?" 