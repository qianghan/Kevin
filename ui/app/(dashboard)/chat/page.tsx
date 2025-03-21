'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ChatInterface } from '@/features/chat/ChatInterface';
import { ObjectId } from 'mongodb';
import { ChatMessage } from '@/models/ChatSession';
import { useChat } from '@/hooks/useChat';

export default function ChatPage() {
  const { data: session, status } = useSession();
  const [isLoading, setIsLoading] = useState(true);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [initialMessages, setInitialMessages] = useState<ChatMessage[]>([]);
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Use the Chat service through our custom hook
  const { getConversation } = useChat();
  
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
      console.log(`Loading chat session with ID: ${id}`);
      // Load chat history using the ChatService
      const conversation = await getConversation(id);
      
      if (!conversation) {
        console.error(`No conversation found for ID: ${id}`);
        // If conversation doesn't exist, reset to new chat
        handleNewSession('new');
        return;
      }
      
      console.log(`Retrieved conversation with title: ${conversation.title}`, {
        messageCount: conversation.messages?.length || 0,
        hasContextSummary: !!conversation.contextSummary
      });
      
      if (conversation.messages && conversation.messages.length > 0) {
        // Ensure messages are in the correct format
        const formattedMessages = conversation.messages.map(msg => ({
          role: msg.role || 'assistant',
          content: msg.content || '',
          timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp || Date.now()),
          thinkingSteps: msg.thinkingSteps || [],
          documents: msg.documents || []
        }));
        
        setInitialMessages(formattedMessages);
        console.log(`Loaded ${formattedMessages.length} messages for conversation ${id}`);
      } else {
        console.log("No messages found in history or empty history returned");
        setInitialMessages([]);
      }
    } catch (error) {
      console.error('Error loading chat session:', error instanceof Error ? error.message : String(error));
      setInitialMessages([]);
      
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
            initialConversationId={sessionId}
            initialMessages={initialMessages}
          />
        </div>
      </main>
    </div>
  );
} 