'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import ChatInterface from '@/components/chat/ChatInterface';
import { ObjectId } from 'mongodb';
import { ChatMessage } from '@/models/ChatSession';

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
    const sessionIdParam = searchParams.get('id');
    if (sessionIdParam) {
      setSessionId(sessionIdParam);
      loadChatSession(sessionIdParam);
    } else {
      setIsLoading(false);
    }
  }, [status, searchParams, router]);
  
  const loadChatSession = async (id: string) => {
    setIsLoading(true);
    try {
      // In a real app, this would make an API call to fetch the chat session from MongoDB
      // For now, just setting empty messages array
      setInitialMessages([]);
    } catch (error) {
      console.error('Error loading chat session:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleNewSession = (newSessionId: string) => {
    // Update URL with new session ID
    router.push(`/chat?id=${newSessionId}`);
    setSessionId(newSessionId);
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
        <h1 className="text-xl font-semibold">
          {sessionId ? 'Chat Session' : 'New Chat'}
        </h1>
      </header>
      
      <main className="flex-1 overflow-hidden">
        <ChatInterface 
          sessionId={sessionId}
          onNewSession={handleNewSession}
          initialMessages={initialMessages}
        />
      </main>
    </div>
  );
} 