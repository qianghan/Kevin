import { ComponentType } from 'react';
import { UserProfile, UserPreferences } from '@/services';

// Common properties shared by all user components
export interface UserComponentProps {
  user: UserProfile | null;
  preferences: UserPreferences;
  isLoading: boolean;
  error: string | null;
  onUpdateProfile: (data: Partial<UserProfile>) => Promise<boolean>;
  onUpdatePreferences: (data: Partial<UserPreferences>) => Promise<boolean>;
  onRefreshProfile: () => Promise<void>;
  isAuthenticated: boolean;
}

// Profile card props
export interface UserProfileCardProps extends UserComponentProps {}

// Preferences form props
export interface UserPreferenceFormProps extends UserComponentProps {}

// Account form props
export interface UserAccountFormProps extends UserComponentProps {}

// Security form props
export interface UserSecurityFormProps extends UserComponentProps {
  onChangeEmail: (newEmail: string, password: string) => Promise<boolean>;
  onChangePassword: (currentPassword: string, newPassword: string) => Promise<boolean>;
}

// Linked accounts props
export interface UserLinkedAccountsProps extends UserComponentProps {
  onLinkAccount: (targetUserId: string, relationship: 'student' | 'parent' | 'partner') => Promise<boolean>;
  onUnlinkAccount: (targetUserId: string, relationship: 'student' | 'parent' | 'partner') => Promise<boolean>;
  onSearchUsers: (query: string) => Promise<UserProfile[]>;
  onGetLinkedUsers: (relationship: 'students' | 'parents' | 'partners') => Promise<UserProfile[]>;
}

// Error display props
export interface UserErrorDisplayProps {
  error: string | null;
  onRefreshProfile?: () => Promise<void>;
}

// Adapter props for the component registry
export interface UserAdapterProps {
  components: {
    profileCard?: ComponentType<UserProfileCardProps>;
    preferenceForm?: ComponentType<UserPreferenceFormProps>;
    accountForm?: ComponentType<UserAccountFormProps>;
    securityForm?: ComponentType<UserSecurityFormProps>;
    linkedAccounts?: ComponentType<UserLinkedAccountsProps>;
    errorDisplay?: ComponentType<UserErrorDisplayProps>;
    extras?: Record<string, ComponentType<UserComponentProps>>;
  };
} 