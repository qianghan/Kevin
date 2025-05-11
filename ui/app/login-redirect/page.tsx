'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

/**
 * Special redirect handler to manage root /login path
 * This ensures compatibility with the i18n middleware routing
 */
export default function LoginRedirectRoot() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  useEffect(() => {
    // Extract any language from the query params (if it was redirected from a locale path)
    const lang = searchParams?.get('lang') || 'en';
    
    // Redirect to the actual auth login page with language as a query param
    router.push(`/login?lang=${lang}`);
  }, [router, searchParams]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-4">Redirecting to login page...</p>
      </div>
    </div>
  );
} 