'use client';

import { Suspense } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { UserProvider } from '@/features/user/context/UserContext';
import { ProfileForm } from '@/components/profile/ProfileForm';
import { ProfilePicture } from '@/components/profile/ProfilePicture';
import { ProfileCompleteness } from '@/components/profile/ProfileCompleteness';
import { EmailChangeForm } from '@/components/profile/EmailChangeForm';
import { useSession } from 'next-auth/react';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

function ProfileLoading() {
  return (
    <div className="flex justify-center items-center min-h-[400px]">
      <LoadingSpinner size="large" />
    </div>
  );
}

function ProfileError() {
  return (
    <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
      <h2 className="text-lg font-bold text-red-700 mb-2">Profile Unavailable</h2>
      <p className="text-red-600">
        Sorry, we couldn't load your profile. Please try refreshing the page or sign in again.
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

export default function ProfilePage() {
  const { status } = useSession();

  // Show loading state while checking authentication
  if (status === 'loading') {
    return <ProfileLoading />;
  }

  // Show error if not authenticated
  if (status === 'unauthenticated') {
    return <ProfileError />;
  }

  return (
    <UserProvider>
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold mb-8">Your Profile</h1>
        
        <Suspense fallback={<ProfileLoading />}>
          <Tabs defaultValue="general" className="w-full">
            <TabsList className="mb-6">
              <TabsTrigger value="general">General</TabsTrigger>
              <TabsTrigger value="picture">Profile Picture</TabsTrigger>
              <TabsTrigger value="email">Email</TabsTrigger>
            </TabsList>
            
            <TabsContent value="general" className="space-y-8">
              <ProfileCompleteness />
              <ProfileForm />
            </TabsContent>
            
            <TabsContent value="picture">
              <ProfilePicture />
            </TabsContent>
            
            <TabsContent value="email">
              <EmailChangeForm />
            </TabsContent>
          </Tabs>
        </Suspense>
      </div>
    </UserProvider>
  );
} 