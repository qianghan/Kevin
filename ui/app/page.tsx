'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import Image from "next/image";

export default function Home() {
  const router = useRouter();
  const { status } = useSession();

  useEffect(() => {
    // If authenticated, redirect to chat page
    if (status === 'authenticated') {
      router.push('/chat');
    } else if (status === 'unauthenticated') {
      // If not authenticated, redirect to login page with language
      const lang = window.navigator.language.split('-')[0] || 'en';
      router.push(`/${lang}/login`);
    }
    // If status is 'loading', we'll wait for the status to change
  }, [status, router]);

  // Show a loading state while checking authentication
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-4 text-lg text-gray-600">Loading Kevin...</p>
      </div>
    </div>
  );
}
