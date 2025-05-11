# Role-Based Access Control

This document outlines the architecture and implementation of the role-based access control (RBAC) system in the Kevin application.

## Architecture Overview

The RBAC system follows SOLID principles and is built around the following key components:

1. **IPermissionService Interface**: Defines the contract for permission operations
2. **PermissionAdapter**: Adapter implementation connecting to backend /userman API
3. **MockPermissionService**: Mock implementation for testing and development
4. **PermissionContext & usePermissions Hook**: React context and hooks for component access
5. **Permission UI Components**: Reusable UI components for RBAC

## Components

### IPermissionService Interface

Located in `ui/lib/interfaces/services/permission.service.ts`, this interface follows the Interface Segregation Principle (ISP) to define specific permission-related operations:

- `hasPermission()`: Checks if a user has a specific permission
- `hasRole()`: Checks if a user has a specific role
- `getUserRoles()`: Gets all roles assigned to the current user
- `getUserPermissions()`: Gets all permissions granted to the current user
- `updateUserRoles()`: Updates the roles assigned to a user (admin only)

### PermissionAdapter

Located in `ui/lib/services/permission/PermissionAdapter.service.ts`, this adapter connects to the backend /userman API, implementing the IPermissionService interface. It follows the Adapter pattern to translate between the application and the backend service.

### MockPermissionService

Located in `ui/lib/services/permission/mock/MockPermission.service.ts`, this provides a fully functional in-memory implementation for testing and development without requiring the backend service.

### Factory Integration

The PermissionServiceFactory follows the Factory and Strategy patterns:

```typescript
// In PermissionServiceFactory.ts
public createPermissionService(strategy: PermissionServiceStrategy = this.defaultStrategy): IPermissionService {
  // Determine which permission service implementation to create based on strategy
}
```

### PermissionContext & Hook

Located in `ui/hooks/usePermissions.ts`, the context and hook provide React components with access to permission operations:

```typescript
// Example usage in components
const { 
  hasRole, 
  hasPermission, 
  roles,
  permissions
} = usePermissions();
```

This follows the React Context pattern for global state management and implements the Dependency Inversion Principle (DIP) by depending on abstractions rather than concrete implementations.

### Permission UI Components

Located in `ui/components/permission/`, these components provide a user-friendly interface for role-based rendering:

- `PermissionGuard.tsx`: Component for conditional rendering based on permissions
- `AccessDenied.tsx`: Component shown when access is denied
- `RoleManagement.tsx`: Interface for managing user roles (admin only)
- `PermissionMatrix.tsx`: Visualization of role-permission mappings
- `RoleBasedNavigation.tsx`: Navigation with role-based visibility

## Data Flow

1. User authenticates and the PermissionService loads their roles and permissions
2. PermissionContext makes role/permission data available throughout the application
3. Components use the usePermissions hook to check permissions
4. UI conditionally renders based on the user's permissions
5. Admins can update user roles through the permission management interface

## Security Considerations

1. Permission checks are duplicated on the backend to prevent client-side bypassing
2. The permission service caches permissions to reduce API calls
3. User interface elements are conditionally rendered based on permissions
4. Role management requires admin permissions

## Development and Testing

During development, the MockPermissionService provides realistic data and behavior without requiring the backend service. This implementation can be selected using the PermissionServiceFactory:

```typescript
// Force mock implementation during development/testing
permissionServiceFactory.setDefaultStrategy('mock');
```

For production, the adapter implementation is used by default, connecting to the actual backend services.

## Role Hierarchy

The system supports the following user roles, in order of increasing privilege:

1. **GUEST**: Limited access to public information
2. **STUDENT**: Access to learning resources and their own data
3. **TEACHER**: Access to teaching resources, courses, and student data
4. **PARENT**: Access to linked students' data
5. **ADMIN**: Full system access

## Permission Matrix

The application includes a visual permission matrix that shows which roles have which permissions, making it easy to understand and audit the security model.

## Future Enhancements

1. Support for custom roles and permissions
2. Granular permission management at the resource level
3. Role inheritance for more complex permission hierarchies
4. Audit logging for security-related operations 