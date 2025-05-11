import { ChatMessage } from '../components/chat.components';

/**
 * Represents the export format options for chat sessions
 */
export enum ExportFormat {
  JSON = 'json',
  TEXT = 'text',
  MARKDOWN = 'md',
  HTML = 'html',
  PDF = 'pdf'
}

/**
 * Result of an export operation containing the data, filename, and MIME type
 */
export interface ExportResult {
  data: string;
  filename: string;
  mimeType: string;
}

/**
 * Interface for a chat session
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
 * Interface for a chat session service that handles CRUD operations
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
   * Get all messages for a specific chat session
   */
  getSessionMessages(sessionId: string): Promise<ChatMessage[]>;
  
  /**
   * Search for chat sessions based on a query string
   */
  searchSessions(query: string): Promise<ChatSession[]>;
  
  /**
   * Export a chat session in the specified format
   */
  exportSession(sessionId: string, format: ExportFormat): Promise<ExportResult>;
}

/**
 * Interface for a search index of chat sessions
 */
export interface ChatSessionIndex {
  /**
   * Build or rebuild the search index
   */
  buildIndex(sessions: ChatSession[]): void;
  
  /**
   * Add a session to the search index
   */
  addSession(session: ChatSession): void;
  
  /**
   * Update a session in the search index
   */
  updateSession(session: ChatSession): void;
  
  /**
   * Remove a session from the search index
   */
  removeSession(sessionId: string): void;
  
  /**
   * Search for sessions matching the query
   */
  search(query: string): ChatSession[];
  
  /**
   * Clear the search index
   */
  clear(): void;
}

/**
 * Properties for the SessionBrowser component
 */
export interface SessionBrowserProps {
  /**
   * Array of chat sessions to display
   */
  sessions?: ChatSession[];
  
  /**
   * Currently selected session ID
   */
  selectedSessionId?: string;
  
  /**
   * Function called when a session is selected
   */
  onSessionSelect?: (sessionId: string) => void;
  
  /**
   * Function called when a new session is created
   */
  onSessionCreate?: () => void;
  
  /**
   * Function called when a session is renamed
   */
  onSessionRename?: (sessionId: string, newName: string) => void;
  
  /**
   * Function called when a session is deleted
   */
  onSessionDelete?: (sessionId: string) => void;
  
  /**
   * Function called when a session is exported
   */
  onSessionExport?: (sessionId: string, format: ExportFormat) => void;
  
  /**
   * Function called when a session is starred/unstarred
   */
  onSessionStar?: (sessionId: string, starred: boolean) => void;
  
  /**
   * Whether the component is in a loading state
   */
  isLoading?: boolean;
  
  /**
   * Error message to display if there was a problem loading sessions
   */
  error?: Error | null;
}

/**
 * Context props for the Session Context
 */
export interface SessionContextProps {
  /**
   * Array of all chat sessions
   */
  sessions: ChatSession[];
  
  /**
   * Currently selected chat session
   */
  currentSession: ChatSession | null;
  
  /**
   * Whether the sessions are currently loading
   */
  isLoading: boolean;
  
  /**
   * Error that occurred during session operations
   */
  error: Error | null;
  
  /**
   * Function to create a new chat session
   */
  createSession: (name?: string) => Promise<ChatSession>;
  
  /**
   * Function to select a chat session
   */
  selectSession: (sessionId: string) => Promise<void>;
  
  /**
   * Function to update a chat session
   */
  updateSession: (sessionId: string, updates: Partial<ChatSession>) => Promise<ChatSession>;
  
  /**
   * Function to delete a chat session
   */
  deleteSession: (sessionId: string) => Promise<void>;
  
  /**
   * Function to export a chat session
   */
  exportSession: (sessionId: string, format: ExportFormat) => Promise<ExportResult>;
  
  /**
   * Function to search for chat sessions
   */
  searchSessions: (query: string) => Promise<ChatSession[]>;
  
  /**
   * Function to refresh the list of chat sessions
   */
  refreshSessions: () => Promise<void>;
} 