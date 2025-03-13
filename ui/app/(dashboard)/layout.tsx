'use client';

import { useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login');
    }
  }, [status, router]);

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-md">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">Kevin AI</h2>
        </div>
        <nav className="p-4">
          <ul className="space-y-2">
            <li>
              <Link 
                href="/chat" 
                className="block px-4 py-2 rounded hover:bg-gray-100"
              >
                Chat
              </Link>
            </li>
            <li>
              <Link 
                href="/sessions" 
                className="block px-4 py-2 rounded hover:bg-gray-100"
              >
                Sessions
              </Link>
            </li>
            {session?.user?.role === 'parent' && (
              <li>
                <Link 
                  href="/family" 
                  className="block px-4 py-2 rounded hover:bg-gray-100"
                >
                  Family
                </Link>
              </li>
            )}
            <li>
              <Link 
                href="/settings" 
                className="block px-4 py-2 rounded hover:bg-gray-100"
              >
                Settings
              </Link>
            </li>
          </ul>
        </nav>
        <div className="absolute bottom-0 w-64 p-4 border-t">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-gray-300 rounded-full mr-3">
              {session?.user?.image ? (
                <img 
                  src={session.user.image} 
                  alt={session.user.name || 'User'} 
                  className="w-10 h-10 rounded-full"
                />
              ) : (
                <div className="w-10 h-10 rounded-full flex items-center justify-center bg-blue-500 text-white">
                  {session?.user?.name?.charAt(0) || 'U'}
                </div>
              )}
            </div>
            <div>
              <p className="font-medium">{session?.user?.name}</p>
              <p className="text-xs text-gray-500">{session?.user?.role}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden">
        {children}
      </div>
    </div>
  );
} 