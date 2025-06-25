'use client';

import { ReactNode } from 'react';
import { UserProvider } from '@/features/user/context/UserContext';

interface UserProfileProviderProps {
  children: ReactNode;
}

export function UserProfileProvider({ children }: UserProfileProviderProps) {
  return (
    <UserProvider>
      {children}
    </UserProvider>
  );
} 