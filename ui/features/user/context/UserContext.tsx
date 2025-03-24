'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useSession } from 'next-auth/react';
import { userService, UserProfile, UserPreferences } from '@/services';

interface UserContextType {
  profile: UserProfile | null;
  preferences: UserPreferences;
  isLoading: boolean;
  error: string | null;
  updateProfile: (data: Partial<UserProfile>) => Promise<boolean>;
  updatePreferences: (data: Partial<UserPreferences>) => Promise<boolean>;
  refreshProfile: () => Promise<void>;
  linkAccount: (targetUserId: string, relationship: 'student' | 'parent' | 'partner') => Promise<boolean>;
  unlinkAccount: (targetUserId: string, relationship: 'student' | 'parent' | 'partner') => Promise<boolean>;
  searchUsers: (query: string) => Promise<UserProfile[]>;
  getLinkedUsers: (relationship: 'students' | 'parents' | 'partners') => Promise<UserProfile[]>;
  changeEmail: (newEmail: string, password: string) => Promise<boolean>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<boolean>;
  isAuthenticated: boolean;
}

// Create the context with default values
const UserContext = createContext<UserContextType>({
  profile: null,
  preferences: {},
  isLoading: false,
  error: null,
  updateProfile: async () => false,
  updatePreferences: async () => false,
  refreshProfile: async () => {},
  linkAccount: async () => false,
  unlinkAccount: async () => false,
  searchUsers: async () => [],
  getLinkedUsers: async () => [],
  changeEmail: async () => false,
  changePassword: async () => false,
  isAuthenticated: false,
});

// Hook for using the user context
export const useUserContext = () => useContext(UserContext);

interface UserProviderProps {
  children: ReactNode;
}

export function UserProvider({ children }: UserProviderProps) {
  const { data: session, status } = useSession();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences>({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Determine if user is authenticated
  const isAuthenticated = status === 'authenticated';
  
  // Fetch user profile on session change
  useEffect(() => {
    if (isAuthenticated && session?.user) {
      refreshProfile();
    } else if (status === 'unauthenticated') {
      setProfile(null);
      setPreferences({});
    }
  }, [isAuthenticated, session, status]);
  
  // Refresh user profile data
  const refreshProfile = useCallback(async () => {
    if (!isAuthenticated) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Try to get the current user profile
      const userProfile = await userService.getCurrentUser();
      console.log("UserContext: User profile fetched:", userProfile ? 'Success' : 'Not found');
      setProfile(userProfile);
      
      // Also get preferences if profile exists
      if (userProfile) {
        try {
          const userPrefs = await userService.getPreferences();
          console.log("UserContext: User preferences fetched");
          setPreferences(userPrefs);
        } catch (prefsError) {
          console.error('Error fetching user preferences:', prefsError);
          // Don't set an error - preferences are less critical than the profile
        }
      }
    } catch (err) {
      console.error('Error fetching user profile:', err);
      setError('Failed to load user profile');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);
  
  // Update user profile
  const updateProfile = useCallback(async (profileData: Partial<UserProfile>): Promise<boolean> => {
    if (!isAuthenticated || !profile) return false;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const updatedProfile = await userService.updateProfile(profileData);
      setProfile(prev => prev ? { ...prev, ...updatedProfile } : updatedProfile);
      return true;
    } catch (err) {
      console.error('Error updating profile:', err);
      setError('Failed to update profile');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, profile]);
  
  // Update user preferences
  const updatePreferences = useCallback(async (prefsData: Partial<UserPreferences>): Promise<boolean> => {
    if (!isAuthenticated) return false;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const updatedPrefs = await userService.updatePreferences({
        ...preferences,
        ...prefsData
      });
      setPreferences(updatedPrefs);
      return true;
    } catch (err) {
      console.error('Error updating preferences:', err);
      setError('Failed to update preferences');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, preferences]);
  
  // Link with another user account
  const linkAccount = useCallback(async (
    targetUserId: string, 
    relationship: 'student' | 'parent' | 'partner'
  ): Promise<boolean> => {
    if (!isAuthenticated) return false;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const success = await userService.linkAccounts(targetUserId, relationship);
      if (success) {
        await refreshProfile(); // Refresh profile data
      }
      return success;
    } catch (err) {
      console.error('Error linking accounts:', err);
      setError('Failed to link accounts');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, refreshProfile]);
  
  // Unlink from another user account
  const unlinkAccount = useCallback(async (
    targetUserId: string, 
    relationship: 'student' | 'parent' | 'partner'
  ): Promise<boolean> => {
    if (!isAuthenticated) return false;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const success = await userService.unlinkAccount(targetUserId, relationship);
      if (success) {
        await refreshProfile(); // Refresh profile data
      }
      return success;
    } catch (err) {
      console.error('Error unlinking accounts:', err);
      setError('Failed to unlink accounts');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, refreshProfile]);
  
  // Search for users
  const searchUsers = useCallback(async (query: string): Promise<UserProfile[]> => {
    if (!isAuthenticated) return [];
    
    setIsLoading(true);
    setError(null);
    
    try {
      return await userService.searchUsers(query);
    } catch (err) {
      console.error('Error searching users:', err);
      setError('Failed to search users');
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);
  
  // Get linked users
  const getLinkedUsers = useCallback(async (
    relationship: 'students' | 'parents' | 'partners'
  ): Promise<UserProfile[]> => {
    if (!isAuthenticated) return [];
    
    setIsLoading(true);
    setError(null);
    
    try {
      return await userService.getLinkedUsers(relationship);
    } catch (err) {
      console.error(`Error getting ${relationship}:`, err);
      setError(`Failed to get ${relationship}`);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);
  
  // Change email
  const changeEmail = useCallback(async (newEmail: string, password: string): Promise<boolean> => {
    if (!isAuthenticated) return false;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const success = await userService.changeEmail(newEmail, password);
      if (success) {
        await refreshProfile(); // Refresh user data
      }
      return success;
    } catch (err) {
      console.error('Error changing email:', err);
      setError('Failed to change email');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, refreshProfile]);
  
  // Change password
  const changePassword = useCallback(async (
    currentPassword: string, 
    newPassword: string
  ): Promise<boolean> => {
    if (!isAuthenticated) return false;
    
    setIsLoading(true);
    setError(null);
    
    try {
      return await userService.changePassword(currentPassword, newPassword);
    } catch (err) {
      console.error('Error changing password:', err);
      setError('Failed to change password');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);
  
  // Create the context value
  const contextValue: UserContextType = {
    profile,
    preferences,
    isLoading,
    error,
    updateProfile,
    updatePreferences,
    refreshProfile,
    linkAccount,
    unlinkAccount,
    searchUsers,
    getLinkedUsers,
    changeEmail,
    changePassword,
    isAuthenticated,
  };
  
  return (
    <UserContext.Provider value={contextValue}>
      {children}
    </UserContext.Provider>
  );
} 