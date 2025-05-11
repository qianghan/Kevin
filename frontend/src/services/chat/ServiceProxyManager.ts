/**
 * Service Proxy Manager
 * 
 * This class implements the proxy pattern to manage chat service operations, providing
 * logging, caching, error handling, and other cross-cutting concerns.
 * It follows the Single Responsibility Principle (SRP) by separating these concerns
 * from the core service implementation.
 */

import { IChatService, ChatSession, ChatMessage, Attachment, ThinkingStep, NewChatSessionOptions, ChatOptions } from '../../interfaces/services/chat.service';
import { getChatService, ChatServiceStrategy } from './ChatServiceFactory';
import { logDebug, logError, logInfo } from '../logging/logger';

/**
 * Service proxy for chat operations that adds caching, logging, and error handling
 */
export class ChatServiceProxy implements IChatService {
  private service: IChatService;
  private cache: Map<string, any> = new Map();
  private cacheTtl: number = 5 * 60 * 1000; // 5 minutes
  private cacheEnabled: boolean = true;
  private enableMetrics: boolean = true;
  
  /**
   * Create a new ChatServiceProxy
   * @param serviceStrategy The service strategy to use
   */
  constructor(serviceStrategy: ChatServiceStrategy = 'auto') {
    this.service = getChatService(serviceStrategy);
    logInfo('ChatServiceProxy initialized with strategy: ' + serviceStrategy);
  }
  
  /**
   * Enable or disable caching
   */
  setEnableCache(enabled: boolean): void {
    this.cacheEnabled = enabled;
  }
  
  /**
   * Set the cache TTL in milliseconds
   */
  setCacheTtl(ttlMs: number): void {
    this.cacheTtl = ttlMs;
  }
  
  /**
   * Clear the cache
   */
  clearCache(): void {
    this.cache.clear();
    logDebug('ChatServiceProxy cache cleared');
  }
  
  /**
   * Get a value from the cache
   */
  private getCachedValue<T>(key: string): T | null {
    if (!this.cacheEnabled) return null;
    
    const cachedItem = this.cache.get(key);
    if (!cachedItem) return null;
    
    if (Date.now() - cachedItem.timestamp > this.cacheTtl) {
      this.cache.delete(key);
      return null;
    }
    
    return cachedItem.value as T;
  }
  
  /**
   * Set a value in the cache
   */
  private setCachedValue<T>(key: string, value: T): void {
    if (!this.cacheEnabled) return;
    
    this.cache.set(key, {
      value,
      timestamp: Date.now()
    });
  }
  
  /**
   * Measure the execution time of an operation
   */
  private async measureTime<T>(name: string, operation: () => Promise<T>): Promise<T> {
    if (!this.enableMetrics) return operation();
    
    const startTime = Date.now();
    try {
      const result = await operation();
      const endTime = Date.now();
      logDebug(`ChatServiceProxy: ${name} took ${endTime - startTime}ms`);
      return result;
    } catch (error) {
      const endTime = Date.now();
      logError(`ChatServiceProxy: ${name} failed after ${endTime - startTime}ms`, error);
      throw error;
    }
  }
  
  /**
   * Get all chat sessions
   */
  async getSessions(): Promise<ChatSession[]> {
    const cacheKey = 'sessions';
    const cachedSessions = this.getCachedValue<ChatSession[]>(cacheKey);
    
    if (cachedSessions) {
      logDebug('ChatServiceProxy: returning cached sessions');
      return cachedSessions;
    }
    
    return this.measureTime('getSessions', async () => {
      const sessions = await this.service.getSessions();
      this.setCachedValue(cacheKey, sessions);
      return sessions;
    });
  }
  
  /**
   * Get a specific chat session
   */
  async getSession(sessionId: string): Promise<ChatSession> {
    const cacheKey = `session:${sessionId}`;
    const cachedSession = this.getCachedValue<ChatSession>(cacheKey);
    
    if (cachedSession) {
      logDebug(`ChatServiceProxy: returning cached session ${sessionId}`);
      return cachedSession;
    }
    
    return this.measureTime(`getSession:${sessionId}`, async () => {
      const session = await this.service.getSession(sessionId);
      this.setCachedValue(cacheKey, session);
      return session;
    });
  }
  
  /**
   * Create a new chat session
   */
  async createSession(options?: NewChatSessionOptions): Promise<ChatSession> {
    return this.measureTime('createSession', async () => {
      const session = await this.service.createSession(options);
      // Invalidate sessions cache
      this.cache.delete('sessions');
      return session;
    });
  }
  
  /**
   * Update a chat session
   */
  async updateSession(
    sessionId: string, 
    updates: Partial<Omit<ChatSession, 'id' | 'messages'>>
  ): Promise<ChatSession> {
    return this.measureTime(`updateSession:${sessionId}`, async () => {
      const session = await this.service.updateSession(sessionId, updates);
      // Invalidate caches
      this.cache.delete(`session:${sessionId}`);
      this.cache.delete('sessions');
      return session;
    });
  }
  
  /**
   * Delete a chat session
   */
  async deleteSession(sessionId: string): Promise<void> {
    return this.measureTime(`deleteSession:${sessionId}`, async () => {
      await this.service.deleteSession(sessionId);
      // Invalidate caches
      this.cache.delete(`session:${sessionId}`);
      this.cache.delete('sessions');
    });
  }
  
  /**
   * Send a message in a chat session
   */
  async sendMessage(
    sessionId: string, 
    content: string, 
    options?: ChatOptions
  ): Promise<ChatSession> {
    return this.measureTime(`sendMessage:${sessionId}`, async () => {
      const session = await this.service.sendMessage(sessionId, content, options);
      // Invalidate caches
      this.cache.delete(`session:${sessionId}`);
      this.cache.delete('sessions');
      return session;
    });
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
    return this.measureTime(`sendMessageWithAttachments:${sessionId}`, async () => {
      const session = await this.service.sendMessageWithAttachments(
        sessionId, 
        content, 
        attachments, 
        options
      );
      // Invalidate caches
      this.cache.delete(`session:${sessionId}`);
      this.cache.delete('sessions');
      return session;
    });
  }
  
  /**
   * Get thinking steps for a message
   */
  async getThinkingSteps(sessionId: string, messageId: string): Promise<ThinkingStep[]> {
    const cacheKey = `thinkingSteps:${sessionId}:${messageId}`;
    const cachedSteps = this.getCachedValue<ThinkingStep[]>(cacheKey);
    
    if (cachedSteps) {
      logDebug(`ChatServiceProxy: returning cached thinking steps for message ${messageId}`);
      return cachedSteps;
    }
    
    return this.measureTime(`getThinkingSteps:${messageId}`, async () => {
      const steps = await this.service.getThinkingSteps(sessionId, messageId);
      this.setCachedValue(cacheKey, steps);
      return steps;
    });
  }
  
  /**
   * Export a chat session
   */
  async exportSession(
    sessionId: string, 
    format: 'json' | 'text' | 'markdown' | 'pdf'
  ): Promise<Blob> {
    return this.measureTime(`exportSession:${sessionId}:${format}`, async () => {
      return await this.service.exportSession(sessionId, format);
    });
  }
  
  /**
   * Search messages across all sessions
   */
  async searchMessages(query: string): Promise<Array<{message: ChatMessage, session: ChatSession}>> {
    return this.measureTime(`searchMessages:${query}`, async () => {
      return await this.service.searchMessages(query);
    });
  }
}

/**
 * Create a singleton instance of the chat service proxy
 */
export const chatServiceProxy = new ChatServiceProxy();

/**
 * Get the global chat service proxy instance
 */
export function getChatServiceProxy(): ChatServiceProxy {
  return chatServiceProxy;
} 