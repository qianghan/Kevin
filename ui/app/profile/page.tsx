'use client';

import { Suspense } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { UserProfileProvider } from '@/components/profile/UserProfileProvider';
import { ProfileForm } from '@/components/profile/ProfileForm';
import { ProfilePicture } from '@/components/profile/ProfilePicture';
import { ProfileCompleteness } from '@/components/profile/ProfileCompleteness';
import { EmailChangeForm } from '@/components/profile/EmailChangeForm';

export default function ProfilePage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Your Profile</h1>
      
      <UserProfileProvider>
        <Suspense fallback={<div>Loading...</div>}>
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
      </UserProfileProvider>
    </div>
  );
} 