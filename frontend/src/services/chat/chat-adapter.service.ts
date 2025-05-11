/**
 * Chat Adapter Service
 * 
 * This service adapts the UI chat service implementation for use in the frontend.
 * It serves as a bridge between the frontend and the UI codebase, allowing for
 * smooth transition while maintaining compatibility.
 */

import { 
  IChatService, 
  ChatSession, 
  ChatMessage, 
  Attachment, 
  ThinkingStep, 
  NewChatSessionOptions, 
  ChatOptions 
} from '../../interfaces/services/chat.service';

/**
 * UI Chat Service Interface (for reference)
 * This represents what we expect from the UI chat service.
 * It's used for typing only and isn't exported.
 */
interface UIIChatService {
  getSessions(): Promise<any[]>;
  getSession(sessionId: string): Promise<any>;
  createSession(options?: any): Promise<any>;
  updateSession(sessionId: string, updates: any): Promise<any>;
  deleteSession(sessionId: string): Promise<void>;
  sendMessage(sessionId: string, content: string, options?: any): Promise<any>;
  sendMessageWithAttachments(
    sessionId: string, 
    content: string, 
    attachments: any[], 
    options?: any
  ): Promise<any>;
  getThinkingSteps(sessionId: string, messageId: string): Promise<any[]>;
  exportSession(sessionId: string, format: string): Promise<Blob>;
  searchMessages(query: string): Promise<any[]>;
}

/**
 * Chat Adapter Service
 * 
 * This implements the frontend IChatService interface by delegating to the UI chat service.
 * It handles any necessary data transformations between the two systems.
 */
export class ChatAdapterService implements IChatService {
  private uiChatService: UIIChatService;

  /**
   * Create a new ChatAdapterService
   * @param uiChatService The UI chat service to adapt
   */
  constructor(uiChatService: UIIChatService) {
    this.uiChatService = uiChatService;
  }

  /**
   * Map UI chat session to frontend format
   * @param uiSession UI chat session
   * @returns Frontend-formatted chat session
   */
  private mapSession(uiSession: any): ChatSession {
    return {
      id: uiSession.id,
      name: uiSession.name,
      messages: Array.isArray(uiSession.messages) 
        ? uiSession.messages.map(this.mapMessage.bind(this))
        : [],
      createdAt: uiSession.createdAt,
      updatedAt: uiSession.updatedAt,
      metadata: uiSession.metadata || {}
    };
  }

  /**
   * Map UI chat message to frontend format
   * @param uiMessage UI chat message
   * @returns Frontend-formatted chat message
   */
  private mapMessage(uiMessage: any): ChatMessage {
    return {
      id: uiMessage.id,
      content: uiMessage.content,
      role: uiMessage.role,
      timestamp: uiMessage.timestamp,
      attachments: Array.isArray(uiMessage.attachments)
        ? uiMessage.attachments.map(this.mapAttachment.bind(this))
        : undefined,
      metadata: uiMessage.metadata
    };
  }

  /**
   * Map UI attachment to frontend format
   * @param uiAttachment UI attachment
   * @returns Frontend-formatted attachment
   */
  private mapAttachment(uiAttachment: any): Attachment {
    return {
      id: uiAttachment.id,
      type: uiAttachment.type,
      url: uiAttachment.url,
      name: uiAttachment.name,
      size: uiAttachment.size,
      mimeType: uiAttachment.mimeType
    };
  }

  /**
   * Map UI thinking step to frontend format
   * @param uiThinkingStep UI thinking step
   * @returns Frontend-formatted thinking step
   */
  private mapThinkingStep(uiThinkingStep: any): ThinkingStep {
    return {
      id: uiThinkingStep.id,
      content: uiThinkingStep.content,
      timestamp: uiThinkingStep.timestamp
    };
  }

  /**
   * Get all chat sessions for the current user
   * @returns Promise resolving to array of chat sessions
   */
  async getSessions(): Promise<ChatSession[]> {
    try {
      const uiSessions = await this.uiChatService.getSessions();
      return uiSessions.map(this.mapSession.bind(this));
    } catch (error) {
      console.error('Error in ChatAdapterService.getSessions:', error);
      throw error;
    }
  }

  /**
   * Get a specific chat session by ID
   * @param sessionId Chat session ID
   * @returns Promise resolving to the chat session
   */
  async getSession(sessionId: string): Promise<ChatSession> {
    try {
      const uiSession = await this.uiChatService.getSession(sessionId);
      return this.mapSession(uiSession);
    } catch (error) {
      console.error(`Error in ChatAdapterService.getSession for ID ${sessionId}:`, error);
      throw error;
    }
  }

  /**
   * Create a new chat session
   * @param options Options for the new chat session
   * @returns Promise resolving to the new chat session
   */
  async createSession(options?: NewChatSessionOptions): Promise<ChatSession> {
    try {
      const uiSession = await this.uiChatService.createSession(options);
      return this.mapSession(uiSession);
    } catch (error) {
      console.error('Error in ChatAdapterService.createSession:', error);
      throw error;
    }
  }

  /**
   * Update a chat session's metadata
   * @param sessionId Chat session ID
   * @param updates Updates to apply to the session
   * @returns Promise resolving to the updated chat session
   */
  async updateSession(
    sessionId: string, 
    updates: Partial<Omit<ChatSession, 'id' | 'messages'>>
  ): Promise<ChatSession> {
    try {
      const uiSession = await this.uiChatService.updateSession(sessionId, updates);
      return this.mapSession(uiSession);
    } catch (error) {
      console.error(`Error in ChatAdapterService.updateSession for ID ${sessionId}:`, error);
      throw error;
    }
  }

  /**
   * Delete a chat session
   * @param sessionId Chat session ID
   * @returns Promise that resolves when the session is deleted
   */
  async deleteSession(sessionId: string): Promise<void> {
    try {
      await this.uiChatService.deleteSession(sessionId);
    } catch (error) {
      console.error(`Error in ChatAdapterService.deleteSession for ID ${sessionId}:`, error);
      throw error;
    }
  }

  /**
   * Send a message in a chat session
   * @param sessionId Chat session ID
   * @param content Message content
   * @param options Chat options
   * @returns Promise resolving to the updated chat session
   */
  async sendMessage(
    sessionId: string, 
    content: string, 
    options?: ChatOptions
  ): Promise<ChatSession> {
    try {
      const uiSession = await this.uiChatService.sendMessage(sessionId, content, options);
      return this.mapSession(uiSession);
    } catch (error) {
      console.error(`Error in ChatAdapterService.sendMessage for session ${sessionId}:`, error);
      throw error;
    }
  }

  /**
   * Send a message with attachments in a chat session
   * @param sessionId Chat session ID
   * @param content Message content
   * @param attachments Array of attachments
   * @param options Chat options
   * @returns Promise resolving to the updated chat session
   */
  async sendMessageWithAttachments(
    sessionId: string, 
    content: string, 
    attachments: Attachment[], 
    options?: ChatOptions
  ): Promise<ChatSession> {
    try {
      const uiSession = await this.uiChatService.sendMessageWithAttachments(
        sessionId, 
        content, 
        attachments, 
        options
      );
      return this.mapSession(uiSession);
    } catch (error) {
      console.error(`Error in ChatAdapterService.sendMessageWithAttachments for session ${sessionId}:`, error);
      throw error;
    }
  }

  /**
   * Get thinking steps for a specific message
   * @param sessionId Chat session ID
   * @param messageId Message ID
   * @returns Promise resolving to array of thinking steps
   */
  async getThinkingSteps(sessionId: string, messageId: string): Promise<ThinkingStep[]> {
    try {
      const uiThinkingSteps = await this.uiChatService.getThinkingSteps(sessionId, messageId);
      return uiThinkingSteps.map(this.mapThinkingStep.bind(this));
    } catch (error) {
      console.error(`Error in ChatAdapterService.getThinkingSteps for message ${messageId}:`, error);
      throw error;
    }
  }

  /**
   * Export a chat session to a specified format
   * @param sessionId Chat session ID
   * @param format Export format
   * @returns Promise resolving to the export data
   */
  async exportSession(
    sessionId: string, 
    format: 'json' | 'text' | 'markdown' | 'pdf'
  ): Promise<Blob> {
    try {
      return await this.uiChatService.exportSession(sessionId, format);
    } catch (error) {
      console.error(`Error in ChatAdapterService.exportSession for session ${sessionId}:`, error);
      throw error;
    }
  }

  /**
   * Search for messages across all chat sessions
   * @param query Search query
   * @returns Promise resolving to matching messages with session context
   */
  async searchMessages(query: string): Promise<Array<{message: ChatMessage, session: ChatSession}>> {
    try {
      const uiResults = await this.uiChatService.searchMessages(query);
      return uiResults.map(result => ({
        message: this.mapMessage(result.message),
        session: this.mapSession(result.session)
      }));
    } catch (error) {
      console.error(`Error in ChatAdapterService.searchMessages for query "${query}":`, error);
      throw error;
    }
  }
} 