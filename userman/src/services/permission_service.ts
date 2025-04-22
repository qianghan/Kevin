import mongoose from 'mongoose';
import { PermissionModel, ResourceType, ActionType, RolePermissions } from '../models/permission_model';
import { NotFoundError, AuthorizationError } from '../utils/errors';

/**
 * Service for handling role-based permissions
 */
export class PermissionService {
  /**
   * Initialize the permission system by loading default permissions if none exist
   */
  async initializePermissions(): Promise<void> {
    const count = await PermissionModel.countDocuments();
    
    // If we already have permissions in the database, don't recreate them
    if (count > 0) return;
    
    // Create default permissions for each role
    const permissionsToCreate = [];
    
    for (const [role, permissions] of Object.entries(RolePermissions)) {
      for (const permission of permissions) {
        permissionsToCreate.push({
          role,
          resource: permission.resource,
          action: permission.action,
          conditions: {}
        });
      }
    }
    
    // Insert all permissions
    await PermissionModel.insertMany(permissionsToCreate);
  }
  
  /**
   * Check if a user has permission to perform an action on a resource
   */
  async hasPermission(
    userId: string,
    userRole: string,
    resource: ResourceType,
    action: ActionType,
    resourceId?: string
  ): Promise<boolean> {
    // First, check if the user has the specific permission
    const permission = await PermissionModel.findOne({
      role: userRole,
      resource,
      $or: [
        { action },
        { action: ActionType.Manage } // Manage includes all actions
      ]
    });
    
    if (!permission) return false;
    
    // If the permission has conditions, evaluate them
    if (permission.conditions && Object.keys(permission.conditions).length > 0) {
      // Check if permission is limited to own resources
      if (permission.conditions.ownResourceOnly && resourceId) {
        // For user resources, check if the resourceId is the userId
        if (resource === ResourceType.User && resourceId !== userId) {
          return false;
        }
        
        // For relationship resources, check if the user is related to the resource
        if (resource === ResourceType.Relationship) {
          // Logic to check if the user is part of the relationship
          // This would depend on your relationship model structure
          const UserModel = mongoose.model('User');
          const user = await UserModel.findById(userId);
          
          if (!user) return false;
          
          // Check if the resource is in the user's relationships
          return (
            user.studentIds?.includes(resourceId) ||
            user.parentIds?.includes(resourceId) ||
            user.partnerIds?.includes(resourceId)
          );
        }
      }
      
      // Service-specific permissions
      if (permission.conditions.services && resource === ResourceType.Service) {
        // Check if the service is in the allowed services list
        return permission.conditions.services.includes(resourceId);
      }
    }
    
    // If we got here, the user has permission
    return true;
  }
  
  /**
   * Add a custom permission for a role
   */
  async addPermission(
    role: string,
    resource: ResourceType,
    action: ActionType,
    conditions: Record<string, any> = {}
  ): Promise<void> {
    // Check if permission already exists
    const existingPermission = await PermissionModel.findOne({
      role,
      resource,
      action
    });
    
    if (existingPermission) {
      // Update the conditions
      existingPermission.conditions = conditions;
      await existingPermission.save();
    } else {
      // Create a new permission
      await PermissionModel.create({
        role,
        resource,
        action,
        conditions
      });
    }
  }
  
  /**
   * Remove a permission from a role
   */
  async removePermission(
    role: string,
    resource: ResourceType,
    action: ActionType
  ): Promise<void> {
    await PermissionModel.deleteOne({
      role,
      resource,
      action
    });
  }
  
  /**
   * Get all permissions for a role
   */
  async getRolePermissions(role: string): Promise<any[]> {
    const permissions = await PermissionModel.find({ role });
    return permissions.map(permission => ({
      resource: permission.resource,
      action: permission.action,
      conditions: permission.conditions
    }));
  }
  
  /**
   * Authorization middleware factory
   * Creates a middleware function that checks permissions for a specific resource and action
   */
  createAuthorizationMiddleware(resource: ResourceType, action: ActionType) {
    return async (req: any, res: any, next: any) => {
      try {
        const userId = req.user?.id;
        const userRole = req.user?.role;
        
        if (!userId || !userRole) {
          throw new AuthorizationError('Authentication required');
        }
        
        // Get the resource ID from the request params or body
        const resourceId = req.params.id || req.body.id;
        
        // Check permission
        const hasPermission = await this.hasPermission(
          userId,
          userRole,
          resource,
          action,
          resourceId
        );
        
        if (!hasPermission) {
          throw new AuthorizationError(`You don't have permission to ${action} this ${resource}`);
        }
        
        next();
      } catch (error) {
        next(error);
      }
    };
  }
} 