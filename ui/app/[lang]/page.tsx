'use client';

import React, { Suspense, useEffect } from 'react';
import { useRouteParams } from '@/hooks/useRouteParams';
import ServerLangPage from './ServerPage';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

function ClientLangPage({
  params,
}: {
  params: { lang: string } | Promise<{ lang: string }>;
}) {
  const routeParams = useRouteParams(params);
  const { status } = useSession();
  const router = useRouter();

  // Redirect unauthenticated users to /[lang]/login
  useEffect(() => {
    if (routeParams.lang && status === "unauthenticated") {
      router.replace(`/${routeParams.lang}/login`);
    }
  }, [routeParams.lang, status, router]);
  
  // Show loading state until params are resolved or session is checked
  if (!routeParams.lang || status === "loading") {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }
  
  // If authenticated, redirect to chat
  if (status === "authenticated") {
    router.replace(`/${routeParams.lang}/chat`);
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Redirecting to chat...</p>
        </div>
      </div>
    );
  }
  
  return (
    <main className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Welcome to KAI ({routeParams.lang})</h1>
        <p className="text-lg text-gray-600">Please log in to continue.</p>
      </div>
    </main>
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

export default function LangPage({
  params,
}: {
  params: { lang: string } | Promise<{ lang: string }>;
}) {
  return (
    <ParamsErrorBoundary 
      fallback={
        <ParamUnwrapper params={params as any}>
          {(lang) => <ServerLangPage lang={lang} />}
        </ParamUnwrapper>
      }
    >
      <Suspense fallback={<div>Loading...</div>}>
        <ClientLangPage params={params} />
      </Suspense>
    </ParamsErrorBoundary>
  );
} 