/**
 * Chat Service Interface
 * 
 * Defines the contract for chat-related operations in the frontend.
 * This is compatible with the existing UI implementation while allowing
 * for frontend-specific extensions.
 */

// Models
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant' | 'system';
  timestamp: string;
  attachments?: Attachment[];
  metadata?: Record<string, any>;
}

export interface Attachment {
  id: string;
  type: 'image' | 'document' | 'link';
  url: string;
  name: string;
  size?: number;
  mimeType?: string;
}

export interface ThinkingStep {
  id: string;
  content: string;
  timestamp: string;
}

export interface ChatSession {
  id: string;
  name: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, any>;
}

export interface NewChatSessionOptions {
  name?: string;
  initialMessage?: string;
  metadata?: Record<string, any>;
}

export interface ChatOptions {
  enableThinkingSteps?: boolean;
  streamResponse?: boolean;
  agentId?: string;
}

/**
 * Core Chat Service Interface
 * Defines the contract that all chat service implementations must follow.
 * This ensures compatibility with the UI implementation while allowing for
 * frontend-specific optimizations.
 */
export interface IChatService {
  /**
   * Get all chat sessions for the current user
   * @returns Promise resolving to array of chat sessions
   */
  getSessions(): Promise<ChatSession[]>;
  
  /**
   * Get a specific chat session by ID
   * @param sessionId Chat session ID
   * @returns Promise resolving to the chat session
   */
  getSession(sessionId: string): Promise<ChatSession>;
  
  /**
   * Create a new chat session
   * @param options Options for the new chat session
   * @returns Promise resolving to the new chat session
   */
  createSession(options?: NewChatSessionOptions): Promise<ChatSession>;
  
  /**
   * Update a chat session's metadata
   * @param sessionId Chat session ID
   * @param updates Updates to apply to the session
   * @returns Promise resolving to the updated chat session
   */
  updateSession(sessionId: string, updates: Partial<Omit<ChatSession, 'id' | 'messages'>>): Promise<ChatSession>;
  
  /**
   * Delete a chat session
   * @param sessionId Chat session ID
   * @returns Promise that resolves when the session is deleted
   */
  deleteSession(sessionId: string): Promise<void>;
  
  /**
   * Send a message in a chat session
   * @param sessionId Chat session ID
   * @param content Message content
   * @param options Chat options
   * @returns Promise resolving to the updated chat session
   */
  sendMessage(sessionId: string, content: string, options?: ChatOptions): Promise<ChatSession>;
  
  /**
   * Send a message with attachments in a chat session
   * @param sessionId Chat session ID
   * @param content Message content
   * @param attachments Array of attachments
   * @param options Chat options
   * @returns Promise resolving to the updated chat session
   */
  sendMessageWithAttachments(
    sessionId: string, 
    content: string, 
    attachments: Attachment[], 
    options?: ChatOptions
  ): Promise<ChatSession>;
  
  /**
   * Get thinking steps for a specific message
   * @param sessionId Chat session ID
   * @param messageId Message ID
   * @returns Promise resolving to array of thinking steps
   */
  getThinkingSteps(sessionId: string, messageId: string): Promise<ThinkingStep[]>;
  
  /**
   * Export a chat session to a specified format
   * @param sessionId Chat session ID
   * @param format Export format
   * @returns Promise resolving to the export data
   */
  exportSession(sessionId: string, format: 'json' | 'text' | 'markdown' | 'pdf'): Promise<Blob>;
  
  /**
   * Search for messages across all chat sessions
   * @param query Search query
   * @returns Promise resolving to matching messages with session context
   */
  searchMessages(query: string): Promise<Array<{message: ChatMessage, session: ChatSession}>>;
} 