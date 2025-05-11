'use client';

import { ReactNode } from 'react';
import { usePermissions } from '@/hooks/usePermissions';
import { UserRole } from '@/lib/interfaces/services/user.service';

interface PermissionGuardProps {
  children: ReactNode;
  fallback?: ReactNode;
  permissions?: string[];
  anyPermission?: boolean;
  roles?: UserRole[];
  anyRole?: boolean;
}

/**
 * Component that conditionally renders its children based on user permissions
 */
export function PermissionGuard({
  children,
  fallback = null,
  permissions = [],
  anyPermission = false,
  roles = [],
  anyRole = false
}: PermissionGuardProps) {
  const { 
    hasAllPermissions, 
    hasAnyPermission, 
    hasAllRoles, 
    hasAnyRole 
  } = usePermissions();
  
  // Permission check
  let hasPermission = true;
  if (permissions.length > 0) {
    hasPermission = anyPermission 
      ? hasAnyPermission(permissions)
      : hasAllPermissions(permissions);
  }
  
  // Role check
  let hasRequiredRole = true;
  if (roles.length > 0) {
    hasRequiredRole = anyRole
      ? hasAnyRole(roles)
      : hasAllRoles(roles);
  }
  
  // User must pass both permission and role checks
  const isAuthorized = hasPermission && hasRequiredRole;
  
  if (!isAuthorized) {
    return <>{fallback}</>;
  }
  
  return <>{children}</>;
} 