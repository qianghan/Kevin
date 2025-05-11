'use client';

import { useState, useEffect } from 'react';
import { UserRole, User } from '@/lib/interfaces/services/user.service';
import { usePermissions } from '@/hooks/usePermissions';
import { permissionServiceFactory } from '@/lib/services/permission/PermissionServiceFactory';
import { AccessDenied } from './AccessDenied';
import { Button } from '@/components/ui/button';

interface UserRoleRowProps {
  user: User;
  availableRoles: UserRole[];
  onSave: (userId: string, roles: UserRole[]) => Promise<void>;
}

/**
 * Component for editing a single user's roles
 */
function UserRoleRow({ user, availableRoles, onSave }: UserRoleRowProps) {
  const [selectedRoles, setSelectedRoles] = useState<UserRole[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // Initialize selected roles from the user
  useEffect(() => {
    // In a real app with multiple roles per user, we'd use the actual array of roles
    // Here we just use the single role as an array entry
    setSelectedRoles([user.role]);
  }, [user]);
  
  const handleRoleToggle = (role: UserRole) => {
    if (selectedRoles.includes(role)) {
      // Remove the role if it's already selected
      setSelectedRoles(prev => prev.filter(r => r !== role));
    } else {
      // Add the role if it's not selected
      setSelectedRoles(prev => [...prev, role]);
    }
  };
  
  const handleSave = async () => {
    if (selectedRoles.length === 0) {
      alert('User must have at least one role');
      return;
    }
    
    setIsSaving(true);
    try {
      await onSave(user.id, selectedRoles);
      setIsEditing(false);
    } catch (error) {
      console.error('Error saving roles:', error);
      alert('Failed to update roles');
    } finally {
      setIsSaving(false);
    }
  };
  
  const handleCancel = () => {
    // Reset to original roles
    setSelectedRoles([user.role]);
    setIsEditing(false);
  };
  
  return (
    <tr className="border-b border-gray-300 dark:border-gray-700">
      <td className="py-4 px-4 text-sm">
        <div className="font-medium">{user.firstName} {user.lastName}</div>
        <div className="text-gray-500">{user.email}</div>
      </td>
      <td className="py-4 px-4">
        {isEditing ? (
          <div className="flex flex-wrap gap-2">
            {availableRoles.map(role => (
              <label key={role} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedRoles.includes(role)}
                  onChange={() => handleRoleToggle(role)}
                  className="rounded border-gray-300 focus:ring-blue-500"
                />
                <span className="text-sm">{role}</span>
              </label>
            ))}
          </div>
        ) : (
          <div className="flex flex-wrap gap-1">
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {user.role}
            </span>
          </div>
        )}
      </td>
      <td className="py-4 px-4">
        {isEditing ? (
          <div className="flex space-x-2">
            <Button 
              size="sm" 
              onClick={handleSave}
              disabled={isSaving}
            >
              {isSaving ? 'Saving...' : 'Save'}
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={handleCancel}
              disabled={isSaving}
            >
              Cancel
            </Button>
          </div>
        ) : (
          <Button 
            size="sm" 
            variant="outline" 
            onClick={() => setIsEditing(true)}
          >
            Edit Roles
          </Button>
        )}
      </td>
    </tr>
  );
}

interface RoleManagementProps {
  initialUsers?: User[];
}

/**
 * Component for managing user roles (admin only)
 */
export function RoleManagement({ initialUsers = [] }: RoleManagementProps) {
  const { hasRole } = usePermissions();
  const [users, setUsers] = useState<User[]>(initialUsers);
  const [isLoading, setIsLoading] = useState(true);
  const [availableRoles, setAvailableRoles] = useState<UserRole[]>([]);
  
  // Only admins can access this component
  const isAdmin = hasRole(UserRole.ADMIN);
  
  const permissionService = permissionServiceFactory.getPermissionService();
  
  // Load users and roles on mount
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      try {
        // In a real app, we would fetch the users from the API
        // Here we just use the initialUsers or mock some data
        if (users.length === 0) {
          setUsers([
            {
              id: '1',
              email: 'admin@example.com',
              firstName: 'Admin',
              lastName: 'User',
              role: UserRole.ADMIN,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              isVerified: true,
              isActive: true,
              preferences: { theme: 'light', language: 'en', emailNotifications: true, timezone: 'UTC' }
            },
            {
              id: '2',
              email: 'teacher@example.com',
              firstName: 'Teacher',
              lastName: 'User',
              role: UserRole.TEACHER,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              isVerified: true,
              isActive: true,
              preferences: { theme: 'light', language: 'en', emailNotifications: true, timezone: 'UTC' }
            },
            {
              id: '3',
              email: 'student@example.com',
              firstName: 'Student',
              lastName: 'User',
              role: UserRole.STUDENT,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              isVerified: true,
              isActive: true,
              preferences: { theme: 'light', language: 'en', emailNotifications: true, timezone: 'UTC' }
            }
          ]);
        }
        
        // Load available roles
        const roles = await permissionService.getAllRoles();
        setAvailableRoles(roles);
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
  }, [users.length, permissionService]);
  
  const handleSaveUserRoles = async (userId: string, roles: UserRole[]) => {
    try {
      // Update user roles through the permission service
      const updatedUser = await permissionService.updateUserRoles(userId, roles);
      
      // Update the user in the local state
      setUsers(prev => prev.map(user => 
        user.id === userId ? { ...user, role: roles[0] } : user
      ));
    } catch (error) {
      console.error('Error updating user roles:', error);
      throw error;
    }
  };
  
  if (!isAdmin) {
    return <AccessDenied message="You must be an administrator to manage user roles." />;
  }
  
  if (isLoading) {
    return <div className="p-8 text-center">Loading user data...</div>;
  }
  
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">User Role Management</h1>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
          <thead className="bg-gray-100 dark:bg-gray-800">
            <tr>
              <th className="py-3 px-4 text-left text-sm font-medium text-gray-700 dark:text-gray-200">User</th>
              <th className="py-3 px-4 text-left text-sm font-medium text-gray-700 dark:text-gray-200">Roles</th>
              <th className="py-3 px-4 text-left text-sm font-medium text-gray-700 dark:text-gray-200">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {users.map(user => (
              <UserRoleRow 
                key={user.id} 
                user={user} 
                availableRoles={availableRoles}
                onSave={handleSaveUserRoles}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
} 