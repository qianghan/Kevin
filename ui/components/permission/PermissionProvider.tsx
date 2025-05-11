'use client';

import { ReactNode } from 'react';
import { PermissionContext, usePermissionState } from '@/hooks/usePermissions';

interface PermissionProviderProps {
  children: ReactNode;
}

export function PermissionProvider({ children }: PermissionProviderProps) {
  const permissionState = usePermissionState();
  
  return (
    <PermissionContext.Provider value={permissionState}>
      {children}
    </PermissionContext.Provider>
  );
} 