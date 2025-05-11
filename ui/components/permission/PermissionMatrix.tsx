'use client';

import { useState, useEffect } from 'react';
import { usePermissions } from '@/hooks/usePermissions';
import { UserRole } from '@/lib/interfaces/services/user.service';
import { Permission } from '@/lib/interfaces/services/permission.service';
import { permissionServiceFactory } from '@/lib/services/permission/PermissionServiceFactory';
import { AccessDenied } from './AccessDenied';

interface PermissionMatrixProps {
  showAll?: boolean;
}

/**
 * Component to visualize role-permission mappings
 */
export function PermissionMatrix({ showAll = false }: PermissionMatrixProps) {
  const { hasRole } = usePermissions();
  const [roles, setRoles] = useState<UserRole[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [rolePermissionMap, setRolePermissionMap] = useState<Record<string, string[]>>({});
  const [isLoading, setIsLoading] = useState(true);
  
  // Only admins can see all permissions unless showAll is true
  const canViewAll = showAll || hasRole(UserRole.ADMIN);
  
  const permissionService = permissionServiceFactory.getPermissionService();
  
  // Load roles and permissions on mount
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      try {
        // Get all roles
        const allRoles = await permissionService.getAllRoles();
        setRoles(allRoles);
        
        // Get all permissions
        const allPermissions = await permissionService.getAllPermissions();
        setPermissions(allPermissions);
        
        // Build the role-permission map
        const map: Record<string, string[]> = {};
        
        for (const role of allRoles) {
          const rolePermissions = await permissionService.getRolePermissions(role);
          map[role] = rolePermissions.map(p => p.id);
        }
        
        setRolePermissionMap(map);
      } catch (error) {
        console.error('Error loading role-permission data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, [permissionService]);
  
  if (!canViewAll) {
    return <AccessDenied message="You do not have permission to view the permission matrix." />;
  }
  
  if (isLoading) {
    return <div className="p-8 text-center">Loading permissions data...</div>;
  }
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">Permission Matrix</h1>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-700 border border-gray-300 dark:border-gray-700">
          <thead className="bg-gray-100 dark:bg-gray-800">
            <tr>
              <th className="py-3 px-4 text-left text-sm font-medium text-gray-700 dark:text-gray-200 border-b border-r border-gray-300 dark:border-gray-700">
                Permission
              </th>
              {roles.map(role => (
                <th 
                  key={role} 
                  className="py-3 px-4 text-center text-sm font-medium text-gray-700 dark:text-gray-200 border-b border-r border-gray-300 dark:border-gray-700"
                >
                  {role}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {permissions.map(permission => (
              <tr key={permission.id} className="hover:bg-gray-50 dark:hover:bg-gray-900">
                <td className="py-3 px-4 text-sm border-r border-gray-300 dark:border-gray-700">
                  <div className="font-medium">{permission.name}</div>
                  <div className="text-xs text-gray-500">{permission.description}</div>
                  <div className="text-xs text-gray-400">{permission.resource}.{permission.action}</div>
                </td>
                {roles.map(role => (
                  <td 
                    key={`${permission.id}-${role}`} 
                    className="py-3 px-4 text-center border-r border-gray-300 dark:border-gray-700"
                  >
                    {rolePermissionMap[role]?.includes(permission.id) ? (
                      <svg
                        className="w-5 h-5 text-green-500 mx-auto"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                    ) : (
                      <svg
                        className="w-5 h-5 text-red-500 mx-auto"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M6 18L18 6M6 6l12 12"
                        />
                      </svg>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
} 