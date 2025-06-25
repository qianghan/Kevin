'use client';

import React, { Suspense, useState, useEffect } from 'react';
import { useRouteParams } from '@/hooks/useRouteParams';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import ChatInterface from '@/components/chat/ChatInterface';
import { useChat } from '@/hooks/useChat';
import ServerChatPage from './ServerPage';

function ClientChatPage({
  params,
}: {
  params: { lang: string } | Promise<{ lang: string }>;
}) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const routeParams = useRouteParams(params);
  const [isLoading, setIsLoading] = useState(true);
  const { getConversation } = useChat();
  const [initialMessages, setInitialMessages] = useState([]);
  const [conversationId, setConversationId] = useState<string | undefined>();
  
  useEffect(() => {
    if (!routeParams.lang) return;
    
    if (status === 'unauthenticated') {
      router.push(`/${routeParams.lang}/login`);
    } else if (status !== 'loading') {
      setIsLoading(false);
    }
  }, [status, router, routeParams.lang]);

  // Load conversation if ID is provided in URL
  useEffect(() => {
    const loadConversation = async () => {
      const searchParams = new URLSearchParams(window.location.search);
      const id = searchParams.get('id');
      
      if (id && id !== 'new') {
        try {
          const conversation = await getConversation(id);
          if (conversation) {
            setInitialMessages(conversation.messages || []);
            setConversationId(id);
          }
        } catch (error) {
          console.error('Failed to load conversation:', error);
        }
      }
    };

    if (!isLoading && status === 'authenticated') {
      loadConversation();
    }
  }, [isLoading, getConversation, status]);
  
  if (!routeParams.lang) {
    return <div>Loading language settings...</div>;
  }
  
  if (status === 'loading' || isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4">Loading chat...</p>
        </div>
      </div>
    );
  }

  if (status === 'unauthenticated') {
    return null; // Will be redirected by the useEffect
  }

  return (
    <div className="h-screen w-screen overflow-hidden bg-white">
      <ChatInterface
        sessionId={conversationId}
        initialMessages={initialMessages}
      />
    </div>
  );
}

// Safe param unwrapper for server components
function ParamUnwrapper({
  params,
  children,
}: {
  params: { lang: string };
  children: (lang: string) => React.ReactNode;
}) {
  const [lang] = React.useState(params.lang);
  return <>{children(lang)}</>;
}

// Error boundary wrapper component
class ParamsErrorBoundary extends React.Component<
  { 
    children: React.ReactNode; 
    fallback: React.ReactNode;
  }, 
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode; fallback: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

export default function ChatPage({
  params,
}: {
  params: { lang: string } | Promise<{ lang: string }>;
}) {
  return (
    <ParamsErrorBoundary 
      fallback={
        <ParamUnwrapper params={params as any}>
          {(lang) => <ServerChatPage lang={lang} />}
        </ParamUnwrapper>
      }
    >
      <Suspense fallback={<div>Loading...</div>}>
        <ClientChatPage params={params} />
      </Suspense>
    </ParamsErrorBoundary>
  );
} 