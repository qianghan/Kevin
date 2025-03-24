'use client';

import React, { ReactNode } from 'react';
import { UserProvider, useUserContext } from '../context/UserContext';
import { UserAdapterProps } from '../types/user-ui.types';

// UserAdapter component that connects UI components to the user context
export function UserAdapter({
  components
}: UserAdapterProps) {
  // Return the provider with the inner component
  return (
    <UserProvider>
      <UserAdapterInner components={components} />
    </UserProvider>
  );
}

// Inner component to access context
function UserAdapterInner({ 
  components
}: { 
  components: UserAdapterProps['components']
}) {
  const {
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
    isAuthenticated
  } = useUserContext();
  
  // Map components with props
  const renderComponent = (Component: React.ComponentType<any>, key: string) => {
    if (!Component) return null;
    
    return (
      <Component
        key={key}
        user={profile}
        preferences={preferences}
        isLoading={isLoading}
        error={error}
        onUpdateProfile={updateProfile}
        onUpdatePreferences={updatePreferences}
        onRefreshProfile={refreshProfile}
        onLinkAccount={linkAccount}
        onUnlinkAccount={unlinkAccount}
        onSearchUsers={searchUsers}
        onGetLinkedUsers={getLinkedUsers}
        onChangeEmail={changeEmail}
        onChangePassword={changePassword}
        isAuthenticated={isAuthenticated}
      />
    );
  };
  
  return (
    <div className="user-adapter">
      {/* Main profile section */}
      {components.profileCard && renderComponent(components.profileCard, 'profile-card')}
      
      {/* Settings forms */}
      {components.preferenceForm && renderComponent(components.preferenceForm, 'preference-form')}
      {components.accountForm && renderComponent(components.accountForm, 'account-form')}
      {components.securityForm && renderComponent(components.securityForm, 'security-form')}
      
      {/* Linked accounts management */}
      {components.linkedAccounts && renderComponent(components.linkedAccounts, 'linked-accounts')}
      
      {/* Error display */}
      {error && components.errorDisplay && renderComponent(components.errorDisplay, 'error-display')}
      
      {/* Other components */}
      {components.extras && Object.entries(components.extras).map(([key, Component]) => 
        renderComponent(Component, `extra-${key}`)
      )}
    </div>
  );
} 