/**
 * Session Adapter
 * 
 * This adapter provides compatibility between the UI and frontend chat session implementations,
 * enabling a smooth transition while maintaining functionality during the migration.
 */

import { 
  ChatSession, 
  ChatSessionService, 
  ExportFormat, 
  ExportResult,
  SessionFilterOptions 
} from '../../interfaces/services/chat.session';
import { ChatMessage } from '../../interfaces/services/chat.service';

/**
 * UI Session structure for mapping from existing implementation
 */
interface UISession {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  messages?: UIMessage[];
  first_message?: UIMessage;
  last_message?: UIMessage;
  preview?: string;
  tags?: string[];
  is_starred?: boolean;
  metadata?: Record<string, any>;
}

/**
 * UI Message structure for mapping 
 */
interface UIMessage {
  id: string;
  session_id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  created_at: string;
  metadata?: Record<string, any>;
}

/**
 * Maps a UI session to the frontend ChatSession format
 */
export const mapUISessionToFrontend = (uiSession: UISession): ChatSession => {
  return {
    id: uiSession.id,
    name: uiSession.name,
    createdAt: uiSession.created_at,
    updatedAt: uiSession.updated_at,
    messageCount: uiSession.message_count,
    firstMessage: uiSession.first_message ? mapUIMessageToFrontend(uiSession.first_message) : undefined,
    lastMessage: uiSession.last_message ? mapUIMessageToFrontend(uiSession.last_message) : undefined,
    preview: uiSession.preview,
    tags: uiSession.tags,
    starred: uiSession.is_starred,
    metadata: uiSession.metadata
  };
};

/**
 * Maps a frontend ChatSession to the UI session format
 */
export const mapFrontendSessionToUI = (session: ChatSession): UISession => {
  return {
    id: session.id,
    name: session.name,
    created_at: session.createdAt,
    updated_at: session.updatedAt,
    message_count: session.messageCount,
    first_message: session.firstMessage ? mapFrontendMessageToUI(session.firstMessage) : undefined,
    last_message: session.lastMessage ? mapFrontendMessageToUI(session.lastMessage) : undefined,
    preview: session.preview,
    tags: session.tags,
    is_starred: session.starred,
    metadata: session.metadata
  };
};

/**
 * Maps a UI message to the frontend ChatMessage format
 */
export const mapUIMessageToFrontend = (uiMessage: UIMessage): ChatMessage => {
  return {
    id: uiMessage.id,
    content: uiMessage.content,
    role: uiMessage.role,
    timestamp: uiMessage.created_at,
    metadata: uiMessage.metadata
  };
};

/**
 * Maps a frontend ChatMessage to the UI message format
 */
export const mapFrontendMessageToUI = (message: ChatMessage): UIMessage => {
  return {
    id: message.id,
    session_id: message.metadata?.session_id || '',
    content: typeof message.content === 'string' ? message.content : JSON.stringify(message.content),
    role: message.role,
    created_at: message.timestamp,
    metadata: message.metadata
  };
};

/**
 * Session adapter class that wraps the UI session service 
 * to provide a frontend-compatible interface
 */
export class SessionAdapter implements ChatSessionService {
  private uiSessionService: any; // Type for the UI session service
  
  constructor(uiSessionService: any) {
    this.uiSessionService = uiSessionService;
  }

  /**
   * Get all sessions
   */
  async getSessions(): Promise<ChatSession[]> {
    const uiSessions = await this.uiSessionService.getSessions();
    return uiSessions.map(mapUISessionToFrontend);
  }
  
  /**
   * Get a specific session by ID
   */
  async getSession(sessionId: string): Promise<ChatSession> {
    const uiSession = await this.uiSessionService.getSession(sessionId);
    return mapUISessionToFrontend(uiSession);
  }
  
  /**
   * Create a new session
   */
  async createSession(name?: string, metadata?: Record<string, any>): Promise<ChatSession> {
    const uiSession = await this.uiSessionService.createSession(name, metadata);
    return mapUISessionToFrontend(uiSession);
  }
  
  /**
   * Update an existing session
   */
  async updateSession(sessionId: string, updates: Partial<ChatSession>): Promise<ChatSession> {
    // Convert updates to UI format
    const uiUpdates: Partial<UISession> = {};
    
    if (updates.name !== undefined) uiUpdates.name = updates.name;
    if (updates.tags !== undefined) uiUpdates.tags = updates.tags;
    if (updates.starred !== undefined) uiUpdates.is_starred = updates.starred;
    if (updates.metadata !== undefined) uiUpdates.metadata = updates.metadata;
    
    const uiSession = await this.uiSessionService.updateSession(sessionId, uiUpdates);
    return mapUISessionToFrontend(uiSession);
  }
  
  /**
   * Delete a session
   */
  async deleteSession(sessionId: string): Promise<void> {
    await this.uiSessionService.deleteSession(sessionId);
  }
  
  /**
   * Get all messages for a session
   */
  async getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
    const uiMessages = await this.uiSessionService.getSessionMessages(sessionId);
    return uiMessages.map(mapUIMessageToFrontend);
  }
  
  /**
   * Search for sessions
   */
  async searchSessions(query: string): Promise<ChatSession[]> {
    const uiSessions = await this.uiSessionService.searchSessions(query);
    return uiSessions.map(mapUISessionToFrontend);
  }
  
  /**
   * Export a session to a specific format
   */
  async exportSession(sessionId: string, format: ExportFormat): Promise<ExportResult> {
    const result = await this.uiSessionService.exportSession(sessionId, format);
    
    return {
      data: result.data,
      filename: result.filename,
      mimeType: result.mimeType || this.getMimeTypeForFormat(format)
    };
  }
  
  /**
   * Filter sessions by criteria
   */
  async filterSessions(options: SessionFilterOptions): Promise<ChatSession[]> {
    // Map frontend options to UI options
    const uiOptions = {
      search: options.search,
      sort_by: options.sortBy,
      sort_direction: options.sortDirection,
      starred_only: options.showStarredOnly,
      tags: options.tags,
      limit: options.limit,
      offset: options.offset
    };
    
    const uiSessions = await this.uiSessionService.filterSessions(uiOptions);
    return uiSessions.map(mapUISessionToFrontend);
  }
  
  /**
   * Helper to get MIME type for export formats
   */
  private getMimeTypeForFormat(format: ExportFormat): string {
    switch (format) {
      case 'json': return 'application/json';
      case 'text': return 'text/plain';
      case 'markdown': return 'text/markdown';
      case 'pdf': return 'application/pdf';
      case 'html': return 'text/html';
      default: return 'application/octet-stream';
    }
  }
} 