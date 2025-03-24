'use client';

import { UserProvider } from '@/features/user/context/UserContext';
import Image from 'next/image';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <UserProvider>
      <div className="min-h-screen bg-gray-50 flex flex-col">
        <header className="bg-white shadow-sm py-4">
          <div className="container mx-auto px-4 flex justify-between items-center">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center mr-3 shadow-md">
                <span className="text-xl font-bold" style={{ textShadow: '0px 1px 2px rgba(0, 0, 0, 0.2)' }}>K</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">Kevin.AI</h1>
            </div>
          </div>
        </header>
        
        <main className="flex-grow flex items-center justify-center">
          {children}
        </main>
        
        <footer className="bg-white py-4 border-t">
          <div className="container mx-auto px-4 text-center text-gray-500 text-sm">
            &copy; {new Date().getFullYear()} Kevin.AI. All rights reserved.
          </div>
        </footer>
      </div>
    </UserProvider>
  );
} 