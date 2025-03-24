'use client';

import React from 'react';
import { UserAdapter } from './adapters/UserAdapter';
import { ComponentType } from 'react';
import {
  UserProfileCardProps,
  UserPreferenceFormProps,
  UserAccountFormProps,
  UserSecurityFormProps,
  UserLinkedAccountsProps,
  UserErrorDisplayProps,
  UserComponentProps
} from './types/user-ui.types';

interface UserInterfaceProps {
  profileCard?: ComponentType<UserProfileCardProps>;
  preferenceForm?: ComponentType<UserPreferenceFormProps>;
  accountForm?: ComponentType<UserAccountFormProps>;
  securityForm?: ComponentType<UserSecurityFormProps>;
  linkedAccounts?: ComponentType<UserLinkedAccountsProps>;
  errorDisplay?: ComponentType<UserErrorDisplayProps>;
  extraComponents?: Record<string, ComponentType<UserComponentProps>>;
}

export default function UserInterface({
  profileCard,
  preferenceForm,
  accountForm,
  securityForm,
  linkedAccounts,
  errorDisplay,
  extraComponents
}: UserInterfaceProps) {
  return (
    <UserAdapter
      components={{
        profileCard,
        preferenceForm,
        accountForm,
        securityForm,
        linkedAccounts,
        errorDisplay,
        extras: extraComponents
      }}
    />
  );
} 