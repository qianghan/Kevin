'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useRouteParams } from '@/hooks/useRouteParams';

/**
 * This is a proxy/redirect component that handles the /[lang]/login route
 * and redirects to the actual auth-protected login page.
 */
export default function LoginRedirect({
  params,
}: {
  params: { lang: string } | Promise<{ lang: string }>;
}) {
  const router = useRouter();
  const routeParams = useRouteParams(params);
  
  useEffect(() => {
    if (routeParams.lang) {
      // Redirect to the actual login page but maintain the language parameter in query
      router.push(`/login?lang=${routeParams.lang}`);
    }
  }, [routeParams.lang, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-4">Redirecting to login...</p>
      </div>
    </div>
  );
} 