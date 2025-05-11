/**
 * Chat Context
 * 
 * This context provides chat state and functionality throughout the frontend application.
 * It wraps the ChatAdapterService and provides a React-friendly interface to chat functionality.
 */

import React, { createContext, useContext, useCallback, useState, useEffect, ReactNode } from 'react';
import { 
  IChatService, 
  ChatSession, 
  ChatMessage, 
  Attachment, 
  ThinkingStep,
  ChatOptions,
  NewChatSessionOptions 
} from '../interfaces/services/chat.service';
import { ChatAdapterService } from '../services/chat/chat-adapter.service';
import initializeUIChatService from '../services/chat/initialize-ui-service';

// Initialize the UI chat service at the top level
if (typeof window !== 'undefined') {
  initializeUIChatService();
}

// Define the shape of the chat context
interface ChatContextType {
  // Session state
  isLoading: boolean;
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  
  // Chat actions
  createSession: (options?: NewChatSessionOptions) => Promise<ChatSession>;
  loadSession: (sessionId: string) => Promise<void>;
  updateSession: (
    sessionId: string, 
    updates: Partial<Omit<ChatSession, 'id' | 'messages'>>
  ) => Promise<ChatSession>;
  deleteSession: (sessionId: string) => Promise<void>;
  refreshSessions: () => Promise<void>;
  
  // Message actions
  sendMessage: (content: string, options?: ChatOptions) => Promise<void>;
  sendMessageWithAttachments: (
    content: string, 
    attachments: Attachment[], 
    options?: ChatOptions
  ) => Promise<void>;
  getThinkingSteps: (messageId: string) => Promise<ThinkingStep[]>;
  
  // Export and search
  exportSession: (format: 'json' | 'text' | 'markdown' | 'pdf') => Promise<Blob>;
  searchMessages: (query: string) => Promise<Array<{message: ChatMessage, session: ChatSession}>>;
  
  // State indicators
  isSending: boolean;
  error: Error | null;
}

// Create the context with a default undefined value
const ChatContext = createContext<ChatContextType | undefined>(undefined);

// Provider props
interface ChatProviderProps {
  chatService: IChatService;
  children: ReactNode;
}

/**
 * ChatProvider component
 * 
 * This component provides chat functionality to its children through the ChatContext.
 */
export const ChatProvider: React.FC<ChatProviderProps> = ({ chatService, children }) => {
  // State
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);

  // Load sessions on mount
  useEffect(() => {
    refreshSessions();
  }, []);

  // Refresh the list of sessions
  const refreshSessions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const fetchedSessions = await chatService.getSessions();
      setSessions(fetchedSessions);
      
      // If there's a current session, refresh it too
      if (currentSession) {
        try {
          const refreshedSession = await chatService.getSession(currentSession.id);
          setCurrentSession(refreshedSession);
        } catch (sessionError) {
          console.error(`Error refreshing current session ${currentSession.id}:`, sessionError);
          // If the session no longer exists, clear the current session
          if (sessionError instanceof Error && sessionError.message.includes('not found')) {
            setCurrentSession(null);
          }
        }
      }
    } catch (error) {
      console.error('Error refreshing sessions:', error);
      setError(error instanceof Error ? error : new Error('Failed to refresh sessions'));
    } finally {
      setIsLoading(false);
    }
  }, [chatService, currentSession]);

  // Create a new session
  const createSession = useCallback(async (options?: NewChatSessionOptions) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const newSession = await chatService.createSession(options);
      setSessions(prevSessions => [...prevSessions, newSession]);
      setCurrentSession(newSession);
      return newSession;
    } catch (error) {
      console.error('Error creating session:', error);
      setError(error instanceof Error ? error : new Error('Failed to create session'));
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [chatService]);

  // Load a specific session
  const loadSession = useCallback(async (sessionId: string) => {
    if (currentSession?.id === sessionId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const session = await chatService.getSession(sessionId);
      setCurrentSession(session);
    } catch (error) {
      console.error(`Error loading session ${sessionId}:`, error);
      setError(error instanceof Error ? error : new Error(`Failed to load session ${sessionId}`));
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [chatService, currentSession]);

  // Update a session
  const updateSession = useCallback(async (
    sessionId: string, 
    updates: Partial<Omit<ChatSession, 'id' | 'messages'>>
  ) => {
    setError(null);
    
    try {
      const updatedSession = await chatService.updateSession(sessionId, updates);
      
      // Update sessions list
      setSessions(prevSessions => 
        prevSessions.map(s => s.id === sessionId ? updatedSession : s)
      );
      
      // Update current session if needed
      if (currentSession?.id === sessionId) {
        setCurrentSession(updatedSession);
      }
      
      return updatedSession;
    } catch (error) {
      console.error(`Error updating session ${sessionId}:`, error);
      setError(error instanceof Error ? error : new Error(`Failed to update session ${sessionId}`));
      throw error;
    }
  }, [chatService, currentSession]);

  // Delete a session
  const deleteSession = useCallback(async (sessionId: string) => {
    setError(null);
    
    try {
      await chatService.deleteSession(sessionId);
      
      // Remove from sessions list
      setSessions(prevSessions => prevSessions.filter(s => s.id !== sessionId));
      
      // Clear current session if it was deleted
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
      }
    } catch (error) {
      console.error(`Error deleting session ${sessionId}:`, error);
      setError(error instanceof Error ? error : new Error(`Failed to delete session ${sessionId}`));
      throw error;
    }
  }, [chatService, currentSession]);

  // Send a message
  const sendMessage = useCallback(async (content: string, options?: ChatOptions) => {
    if (!currentSession) {
      throw new Error('No active chat session');
    }
    
    setIsSending(true);
    setError(null);
    
    try {
      const updatedSession = await chatService.sendMessage(
        currentSession.id, 
        content, 
        options
      );
      setCurrentSession(updatedSession);
      
      // Update the session in the sessions list
      setSessions(prevSessions => 
        prevSessions.map(s => s.id === updatedSession.id ? updatedSession : s)
      );
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error instanceof Error ? error : new Error('Failed to send message'));
      throw error;
    } finally {
      setIsSending(false);
    }
  }, [chatService, currentSession]);

  // Send a message with attachments
  const sendMessageWithAttachments = useCallback(async (
    content: string, 
    attachments: Attachment[], 
    options?: ChatOptions
  ) => {
    if (!currentSession) {
      throw new Error('No active chat session');
    }
    
    setIsSending(true);
    setError(null);
    
    try {
      const updatedSession = await chatService.sendMessageWithAttachments(
        currentSession.id, 
        content, 
        attachments, 
        options
      );
      setCurrentSession(updatedSession);
      
      // Update the session in the sessions list
      setSessions(prevSessions => 
        prevSessions.map(s => s.id === updatedSession.id ? updatedSession : s)
      );
    } catch (error) {
      console.error('Error sending message with attachments:', error);
      setError(error instanceof Error ? error : new Error('Failed to send message with attachments'));
      throw error;
    } finally {
      setIsSending(false);
    }
  }, [chatService, currentSession]);

  // Get thinking steps for a message
  const getThinkingSteps = useCallback(async (messageId: string) => {
    if (!currentSession) {
      throw new Error('No active chat session');
    }
    
    setError(null);
    
    try {
      return await chatService.getThinkingSteps(currentSession.id, messageId);
    } catch (error) {
      console.error(`Error getting thinking steps for message ${messageId}:`, error);
      setError(error instanceof Error ? error : new Error(`Failed to get thinking steps for message ${messageId}`));
      throw error;
    }
  }, [chatService, currentSession]);

  // Export a session
  const exportSession = useCallback(async (format: 'json' | 'text' | 'markdown' | 'pdf') => {
    if (!currentSession) {
      throw new Error('No active chat session');
    }
    
    setError(null);
    
    try {
      return await chatService.exportSession(currentSession.id, format);
    } catch (error) {
      console.error(`Error exporting session ${currentSession.id}:`, error);
      setError(error instanceof Error ? error : new Error(`Failed to export session ${currentSession.id}`));
      throw error;
    }
  }, [chatService, currentSession]);

  // Search messages
  const searchMessages = useCallback(async (query: string) => {
    setError(null);
    
    try {
      return await chatService.searchMessages(query);
    } catch (error) {
      console.error(`Error searching messages with query "${query}":`, error);
      setError(error instanceof Error ? error : new Error(`Failed to search messages with query "${query}"`));
      throw error;
    }
  }, [chatService]);

  // Provide the context value
  const contextValue: ChatContextType = {
    isLoading,
    isSending,
    error,
    sessions,
    currentSession,
    createSession,
    loadSession,
    updateSession,
    deleteSession,
    refreshSessions,
    sendMessage,
    sendMessageWithAttachments,
    getThinkingSteps,
    exportSession,
    searchMessages
  };

  return (
    <ChatContext.Provider value={contextValue}>
      {children}
    </ChatContext.Provider>
  );
};

/**
 * Custom hook to use the chat context
 */
export const useChatContext = () => {
  const context = useContext(ChatContext);
  
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  
  return context;
};

/**
 * Factory function to create a chat context provider with a UI service
 * This is the primary way to connect the frontend chat context to the UI chat service
 */
export const createChatContextWithUIService = (uiChatService: any) => {
  // Cast the UI service to any to avoid type issues
  const chatAdapterService = new ChatAdapterService(uiChatService);
  
  return ({ children }: { children: ReactNode }) => (
    <ChatProvider chatService={chatAdapterService}>
      {children}
    </ChatProvider>
  );
}; 