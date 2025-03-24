import { ComponentType } from 'react';
import { UserProfile, UserPreferences } from '@/services/UserService';

export interface UserComponentProps {
  user: UserProfile | null;
  preferences: UserPreferences;
  isLoading: boolean;
  error: string | null;
  onUpdateProfile: (data: Partial<UserProfile>) => Promise<boolean>;
  onUpdatePreferences: (data: Partial<UserPreferences>) => Promise<boolean>;
  onRefreshProfile: () => Promise<void>;
  onLinkAccount: (targetUserId: string, relationship: 'student' | 'parent' | 'partner') => Promise<boolean>;
  onUnlinkAccount: (targetUserId: string, relationship: 'student' | 'parent' | 'partner') => Promise<boolean>;
  onSearchUsers: (query: string) => Promise<UserProfile[]>;
  onGetLinkedUsers: (relationship: 'students' | 'parents' | 'partners') => Promise<UserProfile[]>;
  onChangeEmail: (newEmail: string, password: string) => Promise<boolean>;
  onChangePassword: (currentPassword: string, newPassword: string) => Promise<boolean>;
  isAuthenticated: boolean;
}

export interface UserProfileCardProps extends UserComponentProps {}
export interface UserPreferenceFormProps extends UserComponentProps {}
export interface UserAccountFormProps extends UserComponentProps {}
export interface UserSecurityFormProps extends UserComponentProps {}
export interface UserLinkedAccountsProps extends UserComponentProps {}
export interface UserErrorDisplayProps extends UserComponentProps {}

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