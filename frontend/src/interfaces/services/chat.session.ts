/**
 * Chat Session Management Interfaces
 * 
 * This file defines interfaces for chat session-related functionality in the frontend application.
 * These interfaces are aligned with existing UI implementation to ensure compatibility.
 */

import { ChatMessage } from './chat.service';

/**
 * Chat Session interface representing a conversation session
 */
export interface ChatSession {
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

/**
 * Chat Session Service interface for managing sessions
 */
export interface ChatSessionService {
  /**
   * Get all available chat sessions
   */
  getSessions(): Promise<ChatSession[]>;
  
  /**
   * Get a specific chat session by ID
   */
  getSession(sessionId: string): Promise<ChatSession>;
  
  /**
   * Create a new chat session
   */
  createSession(name?: string, metadata?: Record<string, any>): Promise<ChatSession>;
  
  /**
   * Update an existing chat session
   */
  updateSession(sessionId: string, updates: Partial<ChatSession>): Promise<ChatSession>;
  
  /**
   * Delete a chat session
   */
  deleteSession(sessionId: string): Promise<void>;
  
  /**
   * Get all messages for a chat session
   */
  getSessionMessages(sessionId: string): Promise<ChatMessage[]>;
  
  /**
   * Search for chat sessions
   */
  searchSessions(query: string): Promise<ChatSession[]>;
  
  /**
   * Export a chat session to a specific format
   */
  exportSession(sessionId: string, format: ExportFormat): Promise<ExportResult>;
}

/**
 * Chat Session Index interface for efficient session searching
 */
export interface ChatSessionIndex {
  /**
   * Add a session to the index
   */
  addSession(session: ChatSession): void;
  
  /**
   * Update a session in the index
   */
  updateSession(sessionId: string, session: Partial<ChatSession>): void;
  
  /**
   * Remove a session from the index
   */
  removeSession(sessionId: string): void;
  
  /**
   * Search sessions by query
   */
  search(query: string): ChatSession[];
  
  /**
   * Clear the index
   */
  clear(): void;
}

/**
 * Export format options for chat sessions
 */
export type ExportFormat = 'json' | 'text' | 'markdown' | 'pdf' | 'html';

/**
 * Result of a session export operation
 */
export interface ExportResult {
  data: string | Blob;
  filename: string;
  mimeType: string;
}

/**
 * Session list filter options
 */
export interface SessionFilterOptions {
  search?: string;
  sortBy?: 'name' | 'updatedAt' | 'createdAt' | 'messageCount';
  sortDirection?: 'asc' | 'desc';
  showStarredOnly?: boolean;
  tags?: string[];
  limit?: number;
  offset?: number;
}

/**
 * Session management context interface
 */
export interface SessionContextProps {
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

/**
 * Session migration interface for transitioning between UI and frontend
 */
export interface SessionMigrationService {
  /**
   * Migrate sessions from UI to frontend
   */
  migrateFromUI(): Promise<{
    migrated: number;
    failed: number;
    errors: Error[];
  }>;
  
  /**
   * Check if migration is needed
   */
  needsMigration(): Promise<boolean>;
  
  /**
   * Get migration status
   */
  getMigrationStatus(): Promise<{
    migrated: number;
    total: number;
    inProgress: boolean;
  }>;
} 