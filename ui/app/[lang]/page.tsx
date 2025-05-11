'use client';

import React, { Suspense } from 'react';
import { useRouteParams } from '@/hooks/useRouteParams';
import ServerLangPage from './ServerPage';

function ClientLangPage({
  params,
}: {
  params: { lang: string } | Promise<{ lang: string }>;
}) {
  // Use our custom hook to safely access params
  const routeParams = useRouteParams(params);
  
  // Show loading state until params are resolved
  if (!routeParams.lang) {
    return <div>Loading...</div>;
  }
  
  return (
    <main>
      <h1>Welcome to KAI ({routeParams.lang})</h1>
      <p>This is the {routeParams.lang} landing page.</p>
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