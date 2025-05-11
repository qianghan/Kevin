import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { userServiceFactory } from '@/lib/services/user/UserServiceFactory';
import { 
  ProfileUpdateData, 
  UserPreferences,
  EmailChangeRequest,
  ExtendedUser
} from '@/lib/interfaces/services/userProfile.service';

interface UserProfileContextType {
  user: ExtendedUser | null;
  isLoading: boolean;
  error: string | null;
  completeness: number;
  updateProfile: (data: ProfileUpdateData) => Promise<boolean>;
  uploadProfilePicture: (file: File) => Promise<boolean>;
  updatePreferences: (preferences: Partial<UserPreferences>) => Promise<boolean>;
  requestEmailChange: (data: EmailChangeRequest) => Promise<boolean>;
  verifyEmailChange: (token: string) => Promise<boolean>;
  exportProfile: (format: 'json' | 'csv') => Promise<any>;
  refreshProfile: () => Promise<void>;
}

// Default context values
const defaultProfileContext: UserProfileContextType = {
  user: null,
  isLoading: false,
  error: null,
  completeness: 0,
  updateProfile: async () => false,
  uploadProfilePicture: async () => false,
  updatePreferences: async () => false,
  requestEmailChange: async () => false,
  verifyEmailChange: async () => false,
  exportProfile: async () => null,
  refreshProfile: async () => {}
};

// Create the context
export const UserProfileContext = createContext<UserProfileContextType>(defaultProfileContext);

// Hook to use the profile context
export function useUserProfile() {
  const context = useContext(UserProfileContext);
  if (!context) {
    throw new Error('useUserProfile must be used within a UserProfileProvider');
  }
  return context;
}

// Hook to manage the user profile state
export function useUserProfileState() {
  const [user, setUser] = useState<ExtendedUser | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [completeness, setCompleteness] = useState<number>(0);

  // Get the user profile service
  const profileService = userServiceFactory.createUserProfileService();

  // Initial loading of profile and completeness
  const loadProfile = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const profile = await profileService.getCurrentProfile();
      setUser(profile);
      
      if (profile) {
        const profileCompleteness = await profileService.getProfileCompleteness();
        setCompleteness(profileCompleteness);
      }
    } catch (err) {
      console.error('Error loading profile:', err);
      setError('Failed to load profile');
    } finally {
      setIsLoading(false);
    }
  }, [profileService]);

  // Load the profile on initial mount
  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  // Update profile
  const updateProfile = useCallback(async (data: ProfileUpdateData): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const updatedUser = await profileService.updateProfile(data);
      setUser(updatedUser);
      
      // Refresh completeness
      const profileCompleteness = await profileService.getProfileCompleteness();
      setCompleteness(profileCompleteness);
      
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update profile';
      setError(errorMessage);
      console.error('Error updating profile:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [profileService]);

  // Upload profile picture
  const uploadProfilePicture = useCallback(async (file: File): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const updatedUser = await profileService.uploadProfilePicture(file);
      setUser(updatedUser);
      
      // Refresh completeness
      const profileCompleteness = await profileService.getProfileCompleteness();
      setCompleteness(profileCompleteness);
      
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload profile picture';
      setError(errorMessage);
      console.error('Error uploading profile picture:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [profileService]);

  // Update preferences
  const updatePreferences = useCallback(async (preferences: Partial<UserPreferences>): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const updatedUser = await profileService.updatePreferences(preferences);
      setUser(updatedUser);
      
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update preferences';
      setError(errorMessage);
      console.error('Error updating preferences:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [profileService]);

  // Request email change
  const requestEmailChange = useCallback(async (data: EmailChangeRequest): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const result = await profileService.requestEmailChange(data);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to request email change';
      setError(errorMessage);
      console.error('Error requesting email change:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [profileService]);

  // Verify email change
  const verifyEmailChange = useCallback(async (token: string): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const result = await profileService.verifyEmailChange(token);
      
      if (result) {
        // Refresh the profile to get updated email
        await loadProfile();
      }
      
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to verify email change';
      setError(errorMessage);
      console.error('Error verifying email change:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [profileService, loadProfile]);

  // Export profile
  const exportProfile = useCallback(async (format: 'json' | 'csv' = 'json'): Promise<any> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const data = await profileService.exportProfileData(format);
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to export profile';
      setError(errorMessage);
      console.error('Error exporting profile:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [profileService]);

  return {
    user,
    isLoading,
    error,
    completeness,
    updateProfile,
    uploadProfilePicture,
    updatePreferences,
    requestEmailChange,
    verifyEmailChange,
    exportProfile,
    refreshProfile: loadProfile
  };
} 