'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode, useEffect } from 'react';
import { useSession } from 'next-auth/react';

interface ChatSession {
  id: string;
  title: string;
  thinkingSteps?: any[];
}

interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

interface ChatContextType {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  messages: ChatMessage[];
  isLoading: boolean;
  isSending: boolean;
  error: string | null;
  createSession: () => Promise<ChatSession>;
  loadSession: (sessionId: string) => Promise<void>;
  sendMessage: (sessionId: string, content: string, options?: { useWebSearch?: boolean; enableThinkingSteps?: boolean }) => Promise<void>;
  updateSession: (sessionId: string, updates: Partial<ChatSession>) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  refreshSessions: () => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

interface ChatProviderProps {
  children: ReactNode;
  initialConversationId?: string;
  initialMessages?: ChatMessage[];
}

export function ChatProvider({ children, initialConversationId, initialMessages = [] }: ChatProviderProps) {
  const { data: session } = useSession();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load initial conversation if provided
  useEffect(() => {
    if (initialConversationId) {
      loadSession(initialConversationId);
    }
  }, [initialConversationId]);

  const createSession = useCallback(async (): Promise<ChatSession> => {
    try {
      const response = await fetch('/api/chat/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to create session');
      }

      const newSession = await response.json();
      setSessions(prev => [...prev, newSession]);
      setCurrentSession(newSession);
      return newSession;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
      throw err;
    }
  }, []);

  const loadSession = useCallback(async (sessionId: string) => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/chat/sessions/${sessionId}`);
      
      if (!response.ok) {
        throw new Error('Failed to load session');
      }

      const session = await response.json();
      setCurrentSession(session);
      
      // Load messages for the session
      const messagesResponse = await fetch(`/api/chat/sessions/${sessionId}/messages`);
      if (messagesResponse.ok) {
        const messages = await messagesResponse.json();
        setMessages(messages);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load session');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (sessionId: string, content: string, options?: { useWebSearch?: boolean; enableThinkingSteps?: boolean }) => {
    try {
      setIsSending(true);
      const response = await fetch(`/api/chat/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          ...options,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const newMessage = await response.json();
      setMessages(prev => [...prev, newMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setIsSending(false);
    }
  }, []);

  const updateSession = useCallback(async (sessionId: string, updates: Partial<ChatSession>) => {
    try {
      const response = await fetch(`/api/chat/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        throw new Error('Failed to update session');
      }

      const updatedSession = await response.json();
      setSessions(prev => prev.map(s => s.id === sessionId ? updatedSession : s));
      if (currentSession?.id === sessionId) {
        setCurrentSession(updatedSession);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update session');
    }
  }, [currentSession]);

  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      const response = await fetch(`/api/chat/sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete session');
      }

      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete session');
    }
  }, [currentSession]);

  const refreshSessions = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/chat/sessions');
      
      if (!response.ok) {
        throw new Error('Failed to load sessions');
      }

      const sessions = await response.json();
      setSessions(sessions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sessions');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const value = {
    sessions,
    currentSession,
    messages,
    isLoading,
    isSending,
    error,
    createSession,
    loadSession,
    sendMessage,
    updateSession,
    deleteSession,
    refreshSessions,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChatContext() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
} 