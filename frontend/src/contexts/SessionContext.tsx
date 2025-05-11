/**
 * SessionContext
 * 
 * This context provides chat session management functionality to the application,
 * with compatibility across both UI and frontend implementations.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { 
  ChatSession, 
  ChatSessionService, 
  ExportFormat, 
  ExportResult,
  SessionContextProps 
} from '../interfaces/services/chat.session';
import { SessionAdapter } from '../services/adapters/SessionAdapter';

// Create context with default values
const SessionContext = createContext<SessionContextProps>({
  sessions: [],
  currentSession: null,
  isLoading: false,
  error: null,
  createSession: async () => { throw new Error('SessionContext not initialized'); },
  selectSession: async () => { throw new Error('SessionContext not initialized'); },
  updateSession: async () => { throw new Error('SessionContext not initialized'); },
  deleteSession: async () => { throw new Error('SessionContext not initialized'); },
  exportSession: async () => { throw new Error('SessionContext not initialized'); },
  searchSessions: async () => { throw new Error('SessionContext not initialized'); },
  refreshSessions: async () => { throw new Error('SessionContext not initialized'); }
});

interface SessionProviderProps {
  children: ReactNode;
  sessionService: ChatSessionService;
}

/**
 * SessionProvider component that provides session management functionality
 */
export const SessionProvider: React.FC<SessionProviderProps> = ({ 
  children, 
  sessionService 
}) => {
  // State
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);

  // Load sessions on initialization
  useEffect(() => {
    refreshSessions();
  }, []);

  /**
   * Refresh the list of sessions
   */
  const refreshSessions = async (): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const sessionsList = await sessionService.getSessions();
      setSessions(sessionsList);
      
      // If we have a current session, update it with the latest data
      if (currentSession) {
        const updatedSession = sessionsList.find(s => s.id === currentSession.id);
        if (updatedSession) {
          setCurrentSession(updatedSession);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to load sessions'));
      console.error('Error loading sessions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Create a new chat session
   */
  const createSession = async (name?: string): Promise<ChatSession> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const newSession = await sessionService.createSession(name);
      setSessions(prevSessions => [newSession, ...prevSessions]);
      setCurrentSession(newSession);
      return newSession;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to create session'));
      console.error('Error creating session:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Select a session by ID
   */
  const selectSession = async (sessionId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Check if already in state
      let session = sessions.find(s => s.id === sessionId);
      
      // If not found, fetch it
      if (!session) {
        session = await sessionService.getSession(sessionId);
      }
      
      setCurrentSession(session);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to select session'));
      console.error('Error selecting session:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Update a session
   */
  const updateSession = async (sessionId: string, updates: Partial<ChatSession>): Promise<ChatSession> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const updatedSession = await sessionService.updateSession(sessionId, updates);
      
      // Update sessions list
      setSessions(prevSessions => 
        prevSessions.map(s => s.id === sessionId ? updatedSession : s)
      );
      
      // Update current session if it matches
      if (currentSession?.id === sessionId) {
        setCurrentSession(updatedSession);
      }
      
      return updatedSession;
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to update session'));
      console.error('Error updating session:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Delete a session
   */
  const deleteSession = async (sessionId: string): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      await sessionService.deleteSession(sessionId);
      
      // Remove from sessions list
      setSessions(prevSessions => prevSessions.filter(s => s.id !== sessionId));
      
      // If deleted current session, set current to null
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to delete session'));
      console.error('Error deleting session:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Export a session
   */
  const exportSession = async (sessionId: string, format: ExportFormat): Promise<ExportResult> => {
    setIsLoading(true);
    setError(null);
    
    try {
      return await sessionService.exportSession(sessionId, format);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to export session'));
      console.error('Error exporting session:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Search sessions
   */
  const searchSessions = async (query: string): Promise<ChatSession[]> => {
    setIsLoading(true);
    setError(null);
    
    try {
      return await sessionService.searchSessions(query);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to search sessions'));
      console.error('Error searching sessions:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const contextValue: SessionContextProps = {
    sessions,
    currentSession,
    isLoading,
    error,
    createSession,
    selectSession,
    updateSession,
    deleteSession,
    exportSession,
    searchSessions,
    refreshSessions
  };

  return (
    <SessionContext.Provider value={contextValue}>
      {children}
    </SessionContext.Provider>
  );
};

/**
 * Hook to use the session context
 */
export const useSessionContext = (): SessionContextProps => {
  const context = useContext(SessionContext);
  
  if (context === undefined) {
    throw new Error('useSessionContext must be used within a SessionProvider');
  }
  
  return context;
};

/**
 * Create an adapter that wraps UI session service and provides it to the context
 */
export const createSessionAdapter = (uiSessionService: any): ChatSessionService => {
  return new SessionAdapter(uiSessionService);
}; 