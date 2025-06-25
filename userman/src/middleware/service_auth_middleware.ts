import { Request, Response, NextFunction } from 'express';
import { ServiceManagementService } from '../services/service_management_service';
import { AuthenticationError, AuthorizationError } from '../utils/errors';
import { UserDocument, UserRole } from '../models/user_model';

// Service management instance
const serviceManager = new ServiceManagementService();

/**
 * Middleware to validate a user's access to a service
 * This middleware checks if the authenticated user has access to the requested service
 */
export const validateServiceAccess = (serviceName: string) => {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const user = req.user as UserDocument;
      
      // If no user is authenticated, reject access
      if (!user) {
        throw new AuthenticationError('Authentication required');
      }
      
      // Check if the user has access to the service
      const accessResult = await serviceManager.checkServiceAccess(user._id.toString(), serviceName);
      
      if (!accessResult.hasAccess) {
        throw new AuthorizationError(`You don't have access to ${serviceName}`);
      }
      
      // Add entitlement info to the request for downstream use
      if (accessResult.entitlement) {
        req.serviceEntitlement = accessResult.entitlement;
      }
      
      next();
    } catch (error) {
      next(error);
    }
  };
};

/**
 * Middleware to validate a user's subscription level for a service
 * This ensures the user has the required subscription type or higher
 */
export const validateSubscriptionLevel = (serviceName: string, requiredLevel: string) => {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const user = req.user as UserDocument;
      
      // If no user is authenticated, reject access
      if (!user) {
        throw new AuthenticationError('Authentication required');
      }
      
      // Check if the user has access to the service
      const accessResult = await serviceManager.checkServiceAccess(user._id.toString(), serviceName);
      
      if (!accessResult.hasAccess) {
        throw new AuthorizationError(`You don't have access to ${serviceName}`);
      }
      
      // Get the entitlement and check subscription level
      const entitlement = accessResult.entitlement;
      if (!entitlement) {
        throw new AuthorizationError('Service entitlement information not available');
      }
      
      // Define subscription hierarchy
      const subscriptionLevels = ['FREE', 'BASIC', 'PREMIUM', 'ENTERPRISE', 'CUSTOM'];
      
      const requiredLevelIndex = subscriptionLevels.indexOf(requiredLevel.toUpperCase());
      const userLevelIndex = subscriptionLevels.indexOf(entitlement.subscriptionType);
      
      if (requiredLevelIndex === -1) {
        throw new Error(`Invalid subscription level: ${requiredLevel}`);
      }
      
      if (userLevelIndex < requiredLevelIndex) {
        throw new AuthorizationError(`This feature requires ${requiredLevel} subscription or higher`);
      }
      
      // Add entitlement info to the request for downstream use
      req.serviceEntitlement = entitlement;
      
      next();
    } catch (error) {
      next(error);
    }
  };
};

/**
 * Middleware to validate if a user has specific features enabled
 * This checks if the user's entitlement includes specific features
 */
export const validateFeatureAccess = (serviceName: string, requiredFeature: string) => {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const user = req.user as UserDocument;
      
      // If no user is authenticated, reject access
      if (!user) {
        throw new AuthenticationError('Authentication required');
      }
      
      // Check if the user has access to the service
      const accessResult = await serviceManager.checkServiceAccess(user._id.toString(), serviceName);
      
      if (!accessResult.hasAccess) {
        throw new AuthorizationError(`You don't have access to ${serviceName}`);
      }
      
      // Get the entitlement and check for the required feature
      const entitlement = accessResult.entitlement;
      if (!entitlement) {
        throw new AuthorizationError('Service entitlement information not available');
      }
      
      if (!entitlement.features.includes(requiredFeature)) {
        throw new AuthorizationError(`You don't have access to the ${requiredFeature} feature`);
      }
      
      // Add entitlement info to the request for downstream use
      req.serviceEntitlement = entitlement;
      
      next();
    } catch (error) {
      next(error);
    }
  };
};

/**
 * Middleware to validate parent-student relationship access
 * Ensures parents can only access their linked students' resources
 */
export const validateParentStudentAccess = (studentIdParam: string = 'studentId') => {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const user = req.user as UserDocument;
      
      // If no user is authenticated, reject access
      if (!user) {
        throw new AuthenticationError('Authentication required');
      }
      
      // Get student ID from request parameters
      const studentId = req.params[studentIdParam];
      
      if (!studentId) {
        throw new AuthorizationError('Student ID is required');
      }
      
      // If user is the student, allow access
      if (user._id.toString() === studentId) {
        return next();
      }
      
      // If user is admin, allow access
      if (user.role === UserRole.ADMIN) {
        return next();
      }
      
      // If user is parent, check if student is linked
      if (user.role === UserRole.PARENT) {
        const studentIds = user.studentIds?.map(id => id.toString()) || [];
        
        if (!studentIds.includes(studentId)) {
          throw new AuthorizationError('You do not have access to this student\'s resources');
        }
        
        // Parent has access to the student
        return next();
      }
      
      // If user is not the student, not an admin, and not a parent of the student, deny access
      throw new AuthorizationError('You do not have access to this resource');
    } catch (error) {
      next(error);
    }
  };
}; 