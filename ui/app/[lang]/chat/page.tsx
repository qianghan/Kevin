'use client';

import React, { Suspense, useState, useEffect } from 'react';
import { useRouteParams } from '@/hooks/useRouteParams';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { ChatInterface } from '@/features/chat/ChatInterface';
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
  
  // Move all hooks before any conditional returns
  useEffect(() => {
    // Only proceed if we have the language parameter
    if (!routeParams.lang) return;
    
    if (status === 'unauthenticated') {
      // Redirect to login with the proper language
      router.push(`/${routeParams.lang}/login`);
    } else if (status !== 'loading') {
      setIsLoading(false);
    }
  }, [status, router, routeParams.lang]);
  
  // Now use state for conditionally rendering
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

  return (
    <div className="h-screen flex flex-col">
      <header className="bg-white shadow p-4">
        <div className="max-w-4xl mx-auto w-full px-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">
            Chat ({routeParams.lang})
          </h1>
        </div>
      </header>
      
      <main className="flex-1 overflow-hidden flex justify-center">
        <div className="max-w-4xl w-full h-full flex flex-col px-4">
          <ChatInterface />
        </div>
      </main>
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
  // Use React.useState to create a stable reference and avoid 
  // suspending with an uncached promise
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