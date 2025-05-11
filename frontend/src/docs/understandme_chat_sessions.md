# KAI Chat Session Management Documentation

This document outlines the architecture, implementation, and compatibility strategy for chat session management in the KAI frontend application, ensuring a seamless transition between the existing `/ui` implementation and the new frontend.

## Table of Contents

1. [Overview](#overview)
2. [Session Architecture](#session-architecture)
3. [Data Model and Interfaces](#data-model-and-interfaces)
4. [Session Adapter Layer](#session-adapter-layer)
5. [Session Search](#session-search)
6. [Session Export](#session-export)
7. [Migration Strategy](#migration-strategy)
8. [Integration Testing](#integration-testing)

## Overview

The Chat Session Management system handles the creation, listing, searching, and interaction with chat conversations in the KAI application. It is designed to provide a unified experience between the existing `/ui` implementation and the new frontend, allowing for a gradual migration without disrupting user workflows or data integrity.

## Session Architecture

The session management system follows a layered architecture:

```
┌────────────────────────────────────────────────────────────┐
│                     UI Components                          │
│    (SessionBrowser, SessionList, SessionExportModal)       │
└───────────────────────────┬────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────┐
│                     Session Context                        │
│         (provides state management and operations)         │
└───────────────────────────┬────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────┐
│                     Session Adapter                        │
│         (translates between UI and frontend models)        │
└───────────────────────────┬────────────────────────────────┘
                            │
┌──────────────┬────────────▼─────────────┬─────────────────┐
│  UI Session  │  Session Search Index    │ Session Export  │
│   Service    │  (client-side indexing)  │    Service      │
└──────────────┴──────────────────────────┴─────────────────┘
```

This architecture provides several advantages:

1. **Decoupling**: UI components are decoupled from the underlying data services
2. **Adaptability**: The adapter layer allows for seamless transition between implementations
3. **Extensibility**: New features can be added without modifying existing code
4. **Testability**: Each layer can be tested independently

## Data Model and Interfaces

The session management system uses the following key interfaces:

### ChatSession

```typescript
interface ChatSession {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
  firstMessage?: ChatMessage;
  lastMessage?: ChatMessage;
  preview?: string;
  tags?: string[];
  starred?: boolean;
  metadata?: Record<string, any>;
}
```

### ChatSessionService

```typescript
interface ChatSessionService {
  getSessions(): Promise<ChatSession[]>;
  getSession(sessionId: string): Promise<ChatSession>;
  createSession(name?: string, metadata?: Record<string, any>): Promise<ChatSession>;
  updateSession(sessionId: string, updates: Partial<ChatSession>): Promise<ChatSession>;
  deleteSession(sessionId: string): Promise<void>;
  getSessionMessages(sessionId: string): Promise<ChatMessage[]>;
  searchSessions(query: string): Promise<ChatSession[]>;
  exportSession(sessionId: string, format: ExportFormat): Promise<ExportResult>;
}
```

### SessionContextProps

```typescript
interface SessionContextProps {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  isLoading: boolean;
  error: Error | null;
  createSession: (name?: string) => Promise<ChatSession>;
  selectSession: (sessionId: string) => Promise<void>;
  updateSession: (sessionId: string, updates: Partial<ChatSession>) => Promise<ChatSession>;
  deleteSession: (sessionId: string) => Promise<void>;
  exportSession: (sessionId: string, format: ExportFormat) => Promise<ExportResult>;
  searchSessions: (query: string) => Promise<ChatSession[]>;
  refreshSessions: () => Promise<void>;
}
```

## Session Adapter Layer

The session adapter layer provides compatibility between the UI and frontend implementations of the chat session services. It translates between the different data models and ensures that operations performed in either implementation are properly synchronized.

Key mapping functions in the adapter:

1. `mapUISessionToFrontend`: Converts UI session format to frontend format
2. `mapFrontendSessionToUI`: Converts frontend session format to UI format
3. `mapUIMessageToFrontend`: Converts UI message format to frontend format
4. `mapFrontendMessageToUI`: Converts frontend message format to UI format

The adapter implements the `ChatSessionService` interface and wraps the UI session service, translating calls between the two systems:

```typescript
export class SessionAdapter implements ChatSessionService {
  private uiSessionService: any;
  
  constructor(uiSessionService: any) {
    this.uiSessionService = uiSessionService;
  }

  async getSessions(): Promise<ChatSession[]> {
    const uiSessions = await this.uiSessionService.getSessions();
    return uiSessions.map(mapUISessionToFrontend);
  }
  
  // ... other methods that translate between UI and frontend formats
}
```

## Session Search

The session search functionality is provided through a `SessionSearchIndex` implementation that uses Lunr.js for fast, client-side full-text search. The index is built from session metadata and content, allowing for efficient searching without requiring server-side implementation.

Key features of the search implementation:

1. **Field Boosting**: Important fields like title and tags are given higher weight
2. **Real-time Updates**: The index is automatically updated when sessions change
3. **Fallback Mode**: If search library fails, a simple string matching algorithm is used
4. **Progressive Enhancement**: Results are returned even as the index is being built

Example usage:

```typescript
// Create and populate the index
const searchIndex = new SessionSearchIndex();
searchIndex.addSessions(sessions);

// Perform a search
const results = searchIndex.search("machine learning");
```

## Session Export

The session export system supports multiple export formats, providing users with flexibility in how they save and share their conversations. The `SessionExporter` class handles the conversion of session data into various formats:

1. **JSON**: Full session data with metadata
2. **Text**: Plain text representation
3. **Markdown**: Formatted document with proper headings
4. **HTML**: Rich formatted document with styling
5. **PDF**: Document format (requires additional library)

Each export format has a specific MIME type and naming convention. The export result contains the data, filename, and MIME type for browser download.

## Migration Strategy

The migration from the UI implementation to the frontend implementation follows these steps:

1. **Dual Operation**: Both implementations run simultaneously during transition
2. **Adapter Layer**: The Session Adapter provides a bridge between implementations
3. **Progressive Replacement**: UI components are gradually replaced with frontend versions
4. **Data Integrity**: Session data is synchronized between implementations
5. **Feature Parity**: All features from UI are implemented in frontend before full migration

The migration is designed to be transparent to users, with no data loss or workflow disruption.

## Integration Testing

The session management system includes comprehensive tests to ensure compatibility:

1. **Unit Tests**: Individual components and services are tested in isolation
2. **Integration Tests**: Components are tested working together
3. **Cross-Implementation Tests**: Tests verify that UI and frontend implementations work correctly together
4. **BDD Tests**: Behavior-driven tests verify that user workflows function as expected

Example integration test for session operations:

```typescript
describe('Session Operations', () => {
  it('should allow creating, updating, and deleting sessions', async () => {
    // Setup test environment
    const { sessionService } = setupTest();
    
    // Create session
    const session = await sessionService.createSession('Test Session');
    expect(session.name).toBe('Test Session');
    
    // Update session
    const updatedSession = await sessionService.updateSession(session.id, { name: 'Updated Session' });
    expect(updatedSession.name).toBe('Updated Session');
    
    // Delete session
    await sessionService.deleteSession(session.id);
    
    // Verify deletion
    try {
      await sessionService.getSession(session.id);
      fail('Session should have been deleted');
    } catch (error) {
      expect(error.message).toMatch(/not found/);
    }
  });
}); 