'use client';

import { ReactNode } from 'react';
import { UserProfileContext, useUserProfileState } from '@/hooks/useUserProfile';

interface UserProfileProviderProps {
  children: ReactNode;
}

export function UserProfileProvider({ children }: UserProfileProviderProps) {
  const profileState = useUserProfileState();
  
  return (
    <UserProfileContext.Provider value={profileState}>
      {children}
    </UserProfileContext.Provider>
  );
} 