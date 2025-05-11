import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { UserRole } from '@/lib/interfaces/services/user.service';
import { 
  Permission,
} from '@/lib/interfaces/services/permission.service';
import { permissionServiceFactory } from '@/lib/services/permission/PermissionServiceFactory';

interface PermissionContextType {
  roles: UserRole[];
  permissions: Permission[];
  isLoading: boolean;
  error: string | null;
  hasPermission: (permissionId: string) => boolean;
  hasAnyPermission: (permissionIds: string[]) => boolean;
  hasAllPermissions: (permissionIds: string[]) => boolean;
  hasRole: (role: UserRole) => boolean;
  hasAnyRole: (roles: UserRole[]) => boolean;
  hasAllRoles: (roles: UserRole[]) => boolean;
  refreshPermissions: () => Promise<void>;
}

// Default context values
const defaultPermissionContext: PermissionContextType = {
  roles: [],
  permissions: [],
  isLoading: false,
  error: null,
  hasPermission: () => false,
  hasAnyPermission: () => false,
  hasAllPermissions: () => false,
  hasRole: () => false,
  hasAnyRole: () => false,
  hasAllRoles: () => false,
  refreshPermissions: async () => {}
};

// Create the context
export const PermissionContext = createContext<PermissionContextType>(defaultPermissionContext);

// Hook to use the permission context
export function usePermissions() {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error('usePermissions must be used within a PermissionProvider');
  }
  return context;
}

// Hook to manage the permission state
export function usePermissionState() {
  const [roles, setRoles] = useState<UserRole[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Get the permission service
  const permissionService = permissionServiceFactory.getPermissionService();

  // Load permissions and roles
  const loadPermissions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Get user roles
      const userRoles = permissionService.getUserRoles();
      setRoles(userRoles);
      
      // Get user permissions
      const userPermissions = permissionService.getUserPermissions();
      setPermissions(userPermissions);
    } catch (err) {
      console.error('Error loading permissions:', err);
      setError('Failed to load permissions');
    } finally {
      setIsLoading(false);
    }
  }, [permissionService]);

  // Load permissions on initial mount
  useEffect(() => {
    loadPermissions();
  }, [loadPermissions]);

  // Permission check functions
  const hasPermission = useCallback((permissionId: string): boolean => {
    return permissionService.hasPermission(permissionId);
  }, [permissionService]);

  const hasAnyPermission = useCallback((permissionIds: string[]): boolean => {
    return permissionService.hasAnyPermission(permissionIds);
  }, [permissionService]);

  const hasAllPermissions = useCallback((permissionIds: string[]): boolean => {
    return permissionService.hasAllPermissions(permissionIds);
  }, [permissionService]);

  // Role check functions
  const hasRole = useCallback((role: UserRole): boolean => {
    return permissionService.hasRole(role);
  }, [permissionService]);

  const hasAnyRole = useCallback((roles: UserRole[]): boolean => {
    return permissionService.hasAnyRole(roles);
  }, [permissionService]);

  const hasAllRoles = useCallback((roles: UserRole[]): boolean => {
    return permissionService.hasAllRoles(roles);
  }, [permissionService]);

  return {
    roles,
    permissions,
    isLoading,
    error,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    hasAllRoles,
    refreshPermissions: loadPermissions
  };
} 