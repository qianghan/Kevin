'use client';

import React from 'react';
import UserInterface from '@/features/user/UserInterface';
import { ProfileCard } from '@/features/user/components/ProfileCard';

export default function ProfilePage() {
  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Your Profile</h1>
      
      {/* Using the user service with the adapter pattern */}
      <UserInterface
        profileCard={ProfileCard}
      />
    </div>
  );
} 