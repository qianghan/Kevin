import { Request, Response, NextFunction } from 'express';
import mongoose from 'mongoose';
import { PermissionService } from '../services/permission_service';
import { ResourceType, ActionType } from '../models/permission_model';
import { NotFoundError, ValidationError, AuthorizationError } from '../utils/errors';

// Get User model
const UserModel = mongoose.model('User');

// Create permission service
const permissionService = new PermissionService();

/**
 * Admin controller for user and service management
 */
export class AdminController {
  /**
   * Get a list of all users with optional filtering
   */
  async getAllUsers(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { role, search, testMode, page = 1, limit = 20 } = req.query;
      
      // Build query
      const query: any = {};
      
      if (role) {
        query.role = role;
      }
      
      if (testMode !== undefined) {
        query.testMode = testMode === 'true';
      }
      
      if (search) {
        query.$or = [
          { email: { $regex: search, $options: 'i' } },
          { firstName: { $regex: search, $options: 'i' } },
          { lastName: { $regex: search, $options: 'i' } }
        ];
      }
      
      // Calculate pagination
      const skip = (Number(page) - 1) * Number(limit);
      
      // Get users and total count
      const [users, total] = await Promise.all([
        UserModel.find(query)
          .sort({ createdAt: -1 })
          .skip(skip)
          .limit(Number(limit)),
        UserModel.countDocuments(query)
      ]);
      
      // Map users to DTOs
      const userDTOs = users.map(user => ({
        id: user._id.toString(),
        email: user.email,
        name: user.fullName || `${user.firstName} ${user.lastName}`,
        role: user.role,
        testMode: user.testMode,
        createdAt: user.createdAt,
        updatedAt: user.updatedAt,
        // Only include IDs, not the full relationship details
        studentIds: user.studentIds || [],
        parentIds: user.parentIds || [],
        partnerIds: user.partnerIds || []
      }));
      
      // Return paginated results
      res.status(200).json({
        users: userDTOs,
        pagination: {
          total,
          page: Number(page),
          limit: Number(limit),
          pages: Math.ceil(total / Number(limit))
        }
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Get detailed information about a specific user
   */
  async getUserDetails(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      
      const user = await UserModel.findById(id);
      
      if (!user) {
        throw new NotFoundError('User not found');
      }
      
      // Get user's permissions
      const permissions = await permissionService.getRolePermissions(user.role);
      
      // Return complete user details
      res.status(200).json({
        id: user._id.toString(),
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        fullName: user.fullName,
        role: user.role,
        testMode: user.testMode,
        createdAt: user.createdAt,
        updatedAt: user.updatedAt,
        studentIds: user.studentIds || [],
        parentIds: user.parentIds || [],
        partnerIds: user.partnerIds || [],
        preferences: user.preferences || {},
        permissions
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Update a user's role
   */
  async updateUserRole(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const { role } = req.body;
      
      if (!role) {
        throw new ValidationError('Role is required');
      }
      
      // Validate the role
      const validRoles = ['admin', 'support', 'parent', 'student'];
      if (!validRoles.includes(role)) {
        throw new ValidationError(`Invalid role. Must be one of: ${validRoles.join(', ')}`);
      }
      
      const user = await UserModel.findById(id);
      
      if (!user) {
        throw new NotFoundError('User not found');
      }
      
      // Prevent changing own role for admins
      if (req.user?.id === id && req.user?.role === 'admin' && role !== 'admin') {
        throw new ValidationError('Admins cannot change their own role');
      }
      
      // Update the user's role
      user.role = role;
      await user.save();
      
      res.status(200).json({
        id: user._id.toString(),
        email: user.email,
        role: user.role,
        message: 'User role updated successfully'
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Toggle test mode for a user
   */
  async toggleTestMode(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const { enabled } = req.body;
      
      if (enabled === undefined) {
        throw new ValidationError('Test mode enabled flag is required');
      }
      
      const user = await UserModel.findById(id);
      
      if (!user) {
        throw new NotFoundError('User not found');
      }
      
      // Update test mode
      user.testMode = !!enabled;
      await user.save();
      
      res.status(200).json({
        id: user._id.toString(),
        email: user.email,
        testMode: user.testMode,
        message: `Test mode ${user.testMode ? 'enabled' : 'disabled'} successfully`
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Get users in test mode
   */
  async getTestModeUsers(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const users = await UserModel.find({ testMode: true });
      
      const userDTOs = users.map(user => ({
        id: user._id.toString(),
        email: user.email,
        name: user.fullName || `${user.firstName} ${user.lastName}`,
        role: user.role,
        createdAt: user.createdAt
      }));
      
      res.status(200).json({ users: userDTOs });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Manage service access for users
   */
  async manageServiceAccess(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { userId, serviceName, hasAccess } = req.body;
      
      if (!userId || !serviceName || hasAccess === undefined) {
        throw new ValidationError('User ID, service name, and access flag are required');
      }
      
      const user = await UserModel.findById(userId);
      
      if (!user) {
        throw new NotFoundError('User not found');
      }
      
      // Initialize services array if it doesn't exist
      if (!user.services) {
        user.services = [];
      }
      
      if (hasAccess) {
        // Grant access if user doesn't already have it
        if (!user.services.includes(serviceName)) {
          user.services.push(serviceName);
        }
      } else {
        // Remove access if user has it
        user.services = user.services.filter(service => service !== serviceName);
      }
      
      await user.save();
      
      // Update permissions for the user's role to include this service
      if (hasAccess) {
        await permissionService.addPermission(
          user.role,
          ResourceType.Service,
          ActionType.Read,
          { services: [serviceName] }
        );
      }
      
      res.status(200).json({
        id: user._id.toString(),
        email: user.email,
        services: user.services,
        message: `Service access ${hasAccess ? 'granted' : 'revoked'} successfully`
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Get all permissions in the system
   */
  async getAllPermissions(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const rolePermissions: Record<string, any> = {};
      
      // Get permissions for each role
      const roles = ['admin', 'support', 'parent', 'student'];
      
      for (const role of roles) {
        rolePermissions[role] = await permissionService.getRolePermissions(role);
      }
      
      res.status(200).json({ permissions: rolePermissions });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Update permissions for a role
   */
  async updateRolePermissions(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { role } = req.params;
      const { permissions } = req.body;
      
      if (!role || !permissions || !Array.isArray(permissions)) {
        throw new ValidationError('Role and permissions array are required');
      }
      
      // Validate the role
      const validRoles = ['admin', 'support', 'parent', 'student'];
      if (!validRoles.includes(role)) {
        throw new ValidationError(`Invalid role. Must be one of: ${validRoles.join(', ')}`);
      }
      
      // Delete existing permissions for this role
      await mongoose.model('Permission').deleteMany({ role });
      
      // Add new permissions
      for (const perm of permissions) {
        if (!perm.resource || !perm.action) {
          throw new ValidationError('Each permission must have resource and action properties');
        }
        
        await permissionService.addPermission(
          role,
          perm.resource,
          perm.action,
          perm.conditions || {}
        );
      }
      
      // Get updated permissions
      const updatedPermissions = await permissionService.getRolePermissions(role);
      
      res.status(200).json({
        role,
        permissions: updatedPermissions,
        message: 'Role permissions updated successfully'
      });
    } catch (error) {
      next(error);
    }
  }
} 