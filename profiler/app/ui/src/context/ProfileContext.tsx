import React, { createContext, useContext, useEffect, useState } from 'react';
import { ProfileState, ProfileService } from '../services/profile';
import { 
  ProfileStore, 
  ProfileStoreState, 
  setProfile, 
  setLoading, 
  setError, 
  clearError
} from '../store/profileStore';

export interface ProfileContextType {
  profileState: ProfileState | null;
  loading: boolean;
  error: string | null;
  sendMessage: (type: string, data: any) => void;
  fetchProfile: () => Promise<ProfileState>;
}

// Create the context with a default undefined value
const ProfileContext = createContext<ProfileContextType | undefined>(undefined);

interface ProfileProviderProps {
  userId: string;
  children: React.ReactNode;
}

export const ProfileProvider: React.FC<ProfileProviderProps> = ({ userId, children }) => {
  // Create a store instance
  const [store] = useState(() => new ProfileStore());
  const [state, setState] = useState<ProfileStoreState>(store.getState());
  const [profileService, setProfileService] = useState<ProfileService | null>(null);

  // Subscribe to store changes
  useEffect(() => {
    const unsubscribe = store.subscribe(newState => {
      setState(newState);
    });
    
    return unsubscribe;
  }, [store]);

  // Setup profile service
  useEffect(() => {
    const service = new ProfileService(userId);
    
    // Set up state change handler
    service.onStateChange((profileState) => {
      store.dispatch(setProfile(profileState));
    });
    
    // Connect to WebSocket
    service.connect();
    
    // Set service in state
    setProfileService(service);
    
    // Cleanup on unmount
    return () => {
      service.disconnect();
    };
  }, [userId, store]);

  const sendMessage = (type: string, data: any) => {
    if (profileService) {
      profileService.sendMessage(type, data);
    } else {
      store.dispatch(setError('Profile service not initialized'));
    }
  };

  const fetchProfile = async (): Promise<ProfileState> => {
    if (profileService) {
      try {
        store.dispatch(setLoading(true));
        const profileState = await profileService.fetchProfile();
        store.dispatch(setProfile(profileState));
        return profileState;
      } catch (e) {
        const errorMessage = e instanceof Error ? e.message : 'Unknown error';
        store.dispatch(setError(errorMessage));
        throw e;
      }
    } else {
      const errorMessage = 'Profile service not initialized';
      store.dispatch(setError(errorMessage));
      throw new Error(errorMessage);
    }
  };

  const value = {
    profileState: state.profile,
    loading: state.loading,
    error: state.error,
    sendMessage,
    fetchProfile
  };

  return (
    <ProfileContext.Provider value={value}>
      {children}
    </ProfileContext.Provider>
  );
};

export const useProfile = (): ProfileContextType => {
  const context = useContext(ProfileContext);
  if (context === undefined) {
    throw new Error('useProfile must be used within a ProfileProvider');
  }
  return context;
};

// Export the context for testing purposes
export { ProfileContext }; 