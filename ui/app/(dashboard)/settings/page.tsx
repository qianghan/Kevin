'use client';

import React, { Suspense } from 'react';
import UserInterface from '@/features/user/UserInterface';
import { PreferenceForm } from '@/features/user/components/PreferenceForm';
import { AccountForm } from '@/features/user/components/AccountForm';
import { SecurityForm } from '@/features/user/components/SecurityForm';
import { ErrorDisplay } from '@/features/user/components/ErrorDisplay';
import { useSession } from 'next-auth/react';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

// Loading component for Suspense
function SettingsLoading() {
  return (
    <div className="flex justify-center items-center min-h-[400px]">
      <LoadingSpinner size="large" />
    </div>
  );
}

// Error boundary fallback
function SettingsError() {
  return (
    <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
      <h2 className="text-lg font-bold text-red-700 mb-2">Settings Unavailable</h2>
      <p className="text-red-600">
        Sorry, we couldn't load your settings. Please try refreshing the page or sign in again.
      </p>
      <button 
        onClick={() => window.location.reload()}
        className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
      >
        Refresh Page
      </button>
    </div>
  );
}

export default function SettingsPage() {
  const { status } = useSession();
  
  // Show loading state while checking authentication
  if (status === 'loading') {
    return <SettingsLoading />;
  }
  
  // Show error if not authenticated 
  if (status === 'unauthenticated') {
    return <SettingsError />;
  }
  
  return (
    <div className="container mx-auto px-4 py-6">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Account Settings</h1>
        <p className="text-gray-800 mt-2">
          Manage your profile and preferences.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <Suspense fallback={<SettingsLoading />}>
            <UserInterface 
              accountForm={AccountForm}
              preferenceForm={PreferenceForm}
              securityForm={SecurityForm}
              errorDisplay={ErrorDisplay}
            />
          </Suspense>
        </div>
        
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Help & Support</h2>
          <p className="text-gray-600 mb-4">
            Having trouble with your account settings? Contact our support team for assistance.
          </p>
          <a 
            href="mailto:support@kevin.ai" 
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Contact Support
          </a>
        </div>
      </div>
    </div>
  );
} 