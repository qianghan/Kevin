/**
 * Mock Chat Service
 * 
 * This file provides a mock implementation of the IChatService interface for testing
 * and development purposes. It simulates the behavior of a real chat service with
 * in-memory data storage.
 */

import { v4 as uuidv4 } from 'uuid';
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
 * Mock implementation of IChatService for testing and development
 */
export class MockChatService implements IChatService {
  private sessions: Map<string, ChatSession> = new Map();
  
  /**
   * Get all chat sessions
   */
  async getSessions(): Promise<ChatSession[]> {
    return Array.from(this.sessions.values());
  }
  
  /**
   * Get a specific chat session by ID
   */
  async getSession(sessionId: string): Promise<ChatSession> {
    const session = this.sessions.get(sessionId);
    
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    
    return { ...session };
  }
  
  /**
   * Create a new chat session
   */
  async createSession(options?: NewChatSessionOptions): Promise<ChatSession> {
    const sessionId = uuidv4();
    const now = new Date().toISOString();
    
    const session: ChatSession = {
      id: sessionId,
      name: options?.name || 'New Chat',
      messages: [],
      createdAt: now,
      updatedAt: now,
      metadata: options?.metadata || {}
    };
    
    // Add initial message if provided
    if (options?.initialMessage) {
      const initialMessageId = uuidv4();
      const initialMessage: ChatMessage = {
        id: initialMessageId,
        content: options.initialMessage,
        role: 'user',
        timestamp: now
      };
      
      session.messages.push(initialMessage);
    }
    
    this.sessions.set(sessionId, session);
    return { ...session };
  }
  
  /**
   * Update a chat session
   */
  async updateSession(
    sessionId: string, 
    updates: Partial<Omit<ChatSession, 'id' | 'messages'>>
  ): Promise<ChatSession> {
    const session = this.sessions.get(sessionId);
    
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    
    const updatedSession = {
      ...session,
      ...updates,
      updatedAt: new Date().toISOString()
    };
    
    this.sessions.set(sessionId, updatedSession);
    return { ...updatedSession };
  }
  
  /**
   * Delete a chat session
   */
  async deleteSession(sessionId: string): Promise<void> {
    if (!this.sessions.has(sessionId)) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    
    this.sessions.delete(sessionId);
  }
  
  /**
   * Send a message in a chat session
   */
  async sendMessage(
    sessionId: string, 
    content: string, 
    options?: ChatOptions
  ): Promise<ChatSession> {
    const session = this.sessions.get(sessionId);
    
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    
    const now = new Date().toISOString();
    const messageId = uuidv4();
    
    // Add user message
    const userMessage: ChatMessage = {
      id: messageId,
      content,
      role: 'user',
      timestamp: now
    };
    
    // Create AI response with a slight delay to simulate processing
    await new Promise((resolve) => setTimeout(resolve, 500));
    
    const aiMessageId = uuidv4();
    const aiMessage: ChatMessage = {
      id: aiMessageId,
      content: `Mock AI response to: ${content}`,
      role: 'assistant',
      timestamp: new Date().toISOString(),
      metadata: {
        model: 'mock-model-1',
        thinking_steps: options?.enableThinkingSteps ? [
          { step: 1, content: 'Thinking about the query...' },
          { step: 2, content: 'Generating a response...' }
        ] : undefined
      }
    };
    
    // Update session with new messages
    const updatedSession = {
      ...session,
      messages: [...session.messages, userMessage, aiMessage],
      updatedAt: new Date().toISOString()
    };
    
    this.sessions.set(sessionId, updatedSession);
    return { ...updatedSession };
  }
  
  /**
   * Send a message with attachments in a chat session
   */
  async sendMessageWithAttachments(
    sessionId: string, 
    content: string, 
    attachments: Attachment[], 
    options?: ChatOptions
  ): Promise<ChatSession> {
    const session = this.sessions.get(sessionId);
    
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    
    const now = new Date().toISOString();
    const messageId = uuidv4();
    
    // Add user message with attachments
    const userMessage: ChatMessage = {
      id: messageId,
      content,
      role: 'user',
      timestamp: now,
      attachments: attachments.map(attachment => ({
        ...attachment,
        id: attachment.id || uuidv4()
      }))
    };
    
    // Create AI response with a slight delay to simulate processing
    await new Promise((resolve) => setTimeout(resolve, 1000));
    
    const aiMessageId = uuidv4();
    const aiMessage: ChatMessage = {
      id: aiMessageId,
      content: `Mock AI response to message with ${attachments.length} attachment(s): ${content}`,
      role: 'assistant',
      timestamp: new Date().toISOString(),
      metadata: {
        model: 'mock-model-1',
        thinking_steps: options?.enableThinkingSteps ? [
          { step: 1, content: 'Processing attachments...' },
          { step: 2, content: 'Analyzing content...' },
          { step: 3, content: 'Generating a response...' }
        ] : undefined
      }
    };
    
    // Update session with new messages
    const updatedSession = {
      ...session,
      messages: [...session.messages, userMessage, aiMessage],
      updatedAt: new Date().toISOString()
    };
    
    this.sessions.set(sessionId, updatedSession);
    return { ...updatedSession };
  }
  
  /**
   * Get thinking steps for a message
   */
  async getThinkingSteps(sessionId: string, messageId: string): Promise<ThinkingStep[]> {
    const session = this.sessions.get(sessionId);
    
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    
    const message = session.messages.find((m: ChatMessage) => m.id === messageId);
    
    if (message?.metadata?.thinking_steps) {
      return message.metadata.thinking_steps;
    }
    
    return [];
  }
  
  /**
   * Search messages across all sessions
   */
  async searchMessages(query: string): Promise<Array<{message: ChatMessage, session: ChatSession}>> {
    const results: Array<{message: ChatMessage, session: ChatSession}> = [];
    const allSessions = Array.from(this.sessions.values());
    
    // Simple case-insensitive search
    const lowerQuery = query.toLowerCase();
    
    for (const session of allSessions) {
      const matchingMessages = session.messages.filter((message: ChatMessage) => 
        typeof message.content === 'string' && 
        message.content.toLowerCase().includes(lowerQuery)
      );
      
      // Add each matching message with its session context
      matchingMessages.forEach(message => {
        results.push({
          message,
          session: { ...session }
        });
      });
    }
    
    return results;
  }
  
  /**
   * Export a chat session to a specific format
   */
  async exportSession(
    sessionId: string, 
    format: 'json' | 'text' | 'markdown' | 'pdf'
  ): Promise<Blob> {
    const session = this.sessions.get(sessionId);
    
    if (!session) {
      throw new Error(`Session not found: ${sessionId}`);
    }
    
    // Simple export implementation that just stringifies the session
    const content = JSON.stringify(session, null, 2);
    return new Blob([content], { type: 'application/json' });
  }
} 