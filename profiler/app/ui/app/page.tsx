'use client';

import { ProfileProvider } from '../lib/contexts/ProfileContext';
import { DocumentProvider } from '../lib/contexts/DocumentContext';
import ProfileBuilder from '../components/ProfileBuilder';

export default function Home() {
  // In a real app, you would get the user ID from authentication
  const userId = 'test-user-1';

  return (
    <main className="min-h-screen bg-gray-100">
      <DocumentProvider>
        <ProfileProvider userId={userId}>
          <ProfileBuilder />
        </ProfileProvider>
      </DocumentProvider>
    </main>
  );
} 