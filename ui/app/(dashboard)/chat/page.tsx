'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import ChatInterface from '@/components/chat/ChatInterface';
import { ObjectId } from 'mongodb';
import { ChatMessage } from '@/models/ChatSession';
import { chatApi } from '@/lib/api/kevin';

export default function ChatPage() {
  const { data: session, status } = useSession();
  const [isLoading, setIsLoading] = useState(true);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [initialMessages, setInitialMessages] = useState<ChatMessage[]>([]);
  const router = useRouter();
  const searchParams = useSearchParams();
  
  useEffect(() => {
    // Check if user is authenticated
    if (status === 'unauthenticated') {
      router.push('/login');
      return;
    }
    
    // Get session ID from URL if available
    const sessionIdParam = searchParams?.get('id');
    if (sessionIdParam && sessionIdParam !== 'new') {
      setSessionId(sessionIdParam);
      loadChatSession(sessionIdParam);
    } else {
      setIsLoading(false);
    }
  }, [status, searchParams, router]);
  
  const loadChatSession = async (id: string) => {
    setIsLoading(true);
    try {
      // Load chat history for this session
      const history = await chatApi.getConversationHistory(id);
      
      if (history && history.messages && history.messages.length > 0) {
        // Convert the history format to our ChatMessage format
        const formattedMessages: ChatMessage[] = history.messages.map((msg: any) => ({
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.timestamp || Date.now())
        }));
        
        setInitialMessages(formattedMessages);
      } else {
        console.log("No messages found in history or empty history returned");
        setInitialMessages([]);
        
        // If conversation doesn't exist, reset to new chat
        if (!history || Object.keys(history).length === 0) {
          handleNewSession('new');
          return;
        }
      }
    } catch (error) {
      console.error('Error loading chat session:', error);
      setInitialMessages([]);
      
      // Show error toast or notification here if desired
      
      // Reset to new chat on error
      handleNewSession('new');
      return;
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleNewSession = (newSessionId: string) => {
    if (newSessionId === 'new') {
      // Clear the session ID and URL params for a fresh start
      setSessionId(undefined);
      router.push('/chat');
      setInitialMessages([]);
    } else {
      // Update URL with new session ID
      router.push(`/chat?id=${newSessionId}`);
      setSessionId(newSessionId);
    }
  };
  
  if (status === 'loading' || isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4">Loading...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="h-screen flex flex-col">
      <header className="bg-white shadow p-4">
        <div className="max-w-4xl mx-auto w-full px-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">
            {sessionId ? 'Chat Session' : 'New Chat'}
          </h1>
        </div>
      </header>
      
      <main className="flex-1 overflow-hidden flex justify-center">
        <div className="max-w-4xl w-full h-full flex flex-col px-4">
          <ChatInterface 
            sessionId={sessionId}
            onNewSession={handleNewSession}
            initialMessages={initialMessages}
          />
        </div>
      </main>
    </div>
  );
} 