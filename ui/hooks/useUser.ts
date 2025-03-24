import { useState, useCallback, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { userService, UserProfile, UserPreferences } from '@/services/UserService';

/**
 * Custom hook for user operations
 */
export function useUser() {
  const { data: session, status } = useSession();
  const [isLoading, setIsLoading] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [preferences, setPreferences] = useState<UserPreferences>({});
  const [error, setError] = useState<string | null>(null);
  
  // Fetch user profile on session change
  useEffect(() => {
    if (status === 'authenticated' && session?.user) {
      fetchUserProfile();
    } else if (status === 'unauthenticated') {
      setUserProfile(null);
    }
  }, [status, session]);
  
  // Fetch user profile
  const fetchUserProfile = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const profile = await userService.getCurrentUser();
      setUserProfile(profile);
      
      // Also get preferences
      if (profile) {
        const userPrefs = await userService.getPreferences();
        setPreferences(userPrefs);
      }
    } catch (err) {
      console.error('Error fetching user profile:', err);
      setError('Failed to load user profile');
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  // Update user profile
  const updateProfile = useCallback(async (profileData: Partial<UserProfile>): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const updatedProfile = await userService.updateProfile(profileData);
      setUserProfile(prev => prev ? { ...prev, ...updatedProfile } : updatedProfile);
      return true;
    } catch (err) {
      console.error('Error updating profile:', err);
      setError('Failed to update profile');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  // Update user preferences
  const updatePreferences = useCallback(async (prefsData: Partial<UserPreferences>): Promise<boolean> => {
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
  }, [preferences]);
  
  // Link with another user account
  const linkAccount = useCallback(async (targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const success = await userService.linkAccounts(targetUserId, relationship);
      if (success) {
        await fetchUserProfile(); // Refresh profile data
      }
      return success;
    } catch (err) {
      console.error('Error linking accounts:', err);
      setError('Failed to link accounts');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [fetchUserProfile]);
  
  // Unlink from another user account
  const unlinkAccount = useCallback(async (targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const success = await userService.unlinkAccount(targetUserId, relationship);
      if (success) {
        await fetchUserProfile(); // Refresh profile data
      }
      return success;
    } catch (err) {
      console.error('Error unlinking accounts:', err);
      setError('Failed to unlink accounts');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [fetchUserProfile]);
  
  // Search for users
  const searchUsers = useCallback(async (query: string): Promise<UserProfile[]> => {
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
  }, []);
  
  // Get linked users
  const getLinkedUsers = useCallback(async (relationship: 'students' | 'parents' | 'partners'): Promise<UserProfile[]> => {
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
  }, []);
  
  // Change email
  const changeEmail = useCallback(async (newEmail: string, password: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const success = await userService.changeEmail(newEmail, password);
      if (success) {
        await fetchUserProfile(); // Refresh user data
      }
      return success;
    } catch (err) {
      console.error('Error changing email:', err);
      setError('Failed to change email');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [fetchUserProfile]);
  
  // Change password
  const changePassword = useCallback(async (currentPassword: string, newPassword: string): Promise<boolean> => {
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
  }, []);
  
  return {
    user: userProfile,
    preferences,
    isLoading,
    error,
    updateProfile,
    updatePreferences,
    fetchUserProfile,
    linkAccount,
    unlinkAccount,
    searchUsers,
    getLinkedUsers,
    changeEmail,
    changePassword,
    isAuthenticated: status === 'authenticated',
    isUnauthenticated: status === 'unauthenticated',
    isAuthenticating: status === 'loading',
  };
} 