import { Request, Response, NextFunction } from 'express';
import { ServiceManagementService } from '../services/service_management_service';
import { ServiceStatus, ServiceAccessLevel } from '../models/service_model';
import { SubscriptionType } from '../models/service_entitlement_model';
import { NotFoundError, ValidationError, AuthorizationError } from '../utils/errors';
import { UserDocument, UserRole } from '../models/user_model';

// Create service management service instance
const serviceManager = new ServiceManagementService();

/**
 * Controller for service management
 */
export class ServiceController {
  /**
   * Register a new service
   */
  async registerService(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const {
        name,
        displayName,
        description,
        baseUrl,
        callbackUrl,
        accessLevel,
        allowedRoles,
        features,
        isSystem,
        icon
      } = req.body;

      // Validate required fields
      if (!name || !displayName || !description || !baseUrl) {
        throw new ValidationError('Name, displayName, description, and baseUrl are required');
      }

      // Register the service
      const service = await serviceManager.registerService({
        name,
        displayName,
        description,
        baseUrl,
        callbackUrl,
        status: ServiceStatus.Active,
        accessLevel: accessLevel || ServiceAccessLevel.RoleBased,
        allowedRoles: allowedRoles || [UserRole.ADMIN],
        features: features || [],
        isSystem: isSystem || false,
        icon
      });

      res.status(201).json(service);
    } catch (error) {
      next(error);
    }
  }

  /**
   * Get all services
   */
  async getServices(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { status, accessLevel, isSystem } = req.query;
      
      const filter: any = {};
      
      if (status) {
        filter.status = status;
      }
      
      if (accessLevel) {
        filter.accessLevel = accessLevel;
      }
      
      if (isSystem !== undefined) {
        filter.isSystem = isSystem === 'true';
      }

      const services = await serviceManager.getServices(filter);
      
      res.status(200).json({ services });
    } catch (error) {
      next(error);
    }
  }

  /**
   * Get a service by ID
   */
  async getServiceById(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const service = await serviceManager.getServiceById(id);
      
      res.status(200).json(service);
    } catch (error) {
      next(error);
    }
  }

  /**
   * Update a service
   */
  async updateService(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      
      // Extract updates from request body
      const {
        displayName,
        description,
        baseUrl,
        callbackUrl,
        status,
        accessLevel,
        allowedRoles,
        features,
        icon
      } = req.body;
      
      const updates: any = {};
      
      if (displayName) updates.displayName = displayName;
      if (description) updates.description = description;
      if (baseUrl) updates.baseUrl = baseUrl;
      if (callbackUrl !== undefined) updates.callbackUrl = callbackUrl;
      if (status) updates.status = status;
      if (accessLevel) updates.accessLevel = accessLevel;
      if (allowedRoles) updates.allowedRoles = allowedRoles;
      if (features) updates.features = features;
      if (icon !== undefined) updates.icon = icon;
      
      const updatedService = await serviceManager.updateService(id, updates);
      
      res.status(200).json(updatedService);
    } catch (error) {
      next(error);
    }
  }

  /**
   * Delete a service
   */
  async deleteService(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      
      await serviceManager.deleteService(id);
      
      res.status(200).json({
        success: true,
        message: 'Service deleted successfully'
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Grant service access to a user
   */
  async grantServiceAccess(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const {
        userId,
        serviceId,
        subscriptionType,
        features,
        quotaLimits,
        expiryDate,
        metadata
      } = req.body;
      
      if (!userId || !serviceId) {
        throw new ValidationError('User ID and service ID are required');
      }
      
      const options: any = {};
      
      if (subscriptionType) options.subscriptionType = subscriptionType;
      if (features) options.features = features;
      if (quotaLimits) options.quotaLimits = quotaLimits;
      if (expiryDate) options.expiryDate = new Date(expiryDate);
      if (metadata) options.metadata = metadata;
      
      // Use the current admin user ID as the grantor
      if (req.user?.id) {
        options.grantedBy = req.user.id;
      }
      
      const entitlement = await serviceManager.grantServiceAccess(
        userId,
        serviceId,
        options
      );
      
      res.status(200).json(entitlement);
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Revoke service access from a user
   */
  async revokeServiceAccess(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { userId, serviceId } = req.body;
      
      if (!userId || !serviceId) {
        throw new ValidationError('User ID and service ID are required');
      }
      
      const revoked = await serviceManager.revokeServiceAccess(userId, serviceId);
      
      res.status(200).json({
        success: revoked,
        message: revoked ? 'Service access revoked successfully' : 'No entitlement found to revoke'
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Get a user's service entitlements
   */
  async getUserEntitlements(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { userId } = req.params;
      
      const entitlements = await serviceManager.getUserEntitlements(userId);
      
      res.status(200).json({ entitlements });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Check if the authenticated user has access to a specific service
   */
  async checkServiceAccess(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const user = req.user as UserDocument;
      const { serviceName } = req.params;
      
      if (!serviceName) {
        res.status(400).json({ success: false, message: 'Service name is required' });
        return;
      }
      
      const result = await serviceManager.checkServiceAccess(user._id.toString(), serviceName);
      
      res.status(200).json({
        success: true,
        hasAccess: result.hasAccess,
        entitlement: result.entitlement
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Get all services the authenticated user has access to
   */
  async getUserServices(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const user = req.user as UserDocument;
      
      const services = await serviceManager.getUserServices(user._id.toString());
      
      res.status(200).json({
        success: true,
        services
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Check if a parent has access to a student's service
   * Used for validating parent-student relationship for service access
   */
  async checkParentStudentServiceAccess(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { studentId, serviceId } = req.params;
      const user = req.user as UserDocument;

      if (!user) {
        throw new AuthorizationError('User not authenticated');
      }

      if (user.role !== UserRole.PARENT) {
        throw new AuthorizationError('Only parents can check student service access');
      }

      if (!studentId || !serviceId) {
        res.status(400).json({ 
          success: false, 
          message: 'Student ID and service ID are required' 
        });
        return;
      }
      
      // Check if the user is linked to the student
      const studentIds = user.studentIds?.map(id => id.toString()) || [];
      if (!studentIds.includes(studentId)) {
        throw new AuthorizationError('You do not have access to this student\'s services');
      }
      
      // Check if the student has access to the service
      const result = await serviceManager.checkServiceAccess(studentId, serviceId);
      
      res.status(200).json({
        success: true,
        hasAccess: result.hasAccess,
        entitlement: result.entitlement
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Get all available services with their details
   * Only accessible by admins
   */
  async getAllServices(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const user = req.user as UserDocument;

      if (!user) {
        throw new AuthorizationError('User not authenticated');
      }

      if (user.role !== UserRole.ADMIN) {
        throw new AuthorizationError('Only admins can view all services');
      }
      
      const services = await serviceManager.getServices();
      
      res.status(200).json({
        success: true,
        services
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Get service usage statistics for a user
   */
  async getServiceUsage(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { userId, serviceNameOrId } = req.params;
      let { startDate, endDate } = req.query;
      
      if (!startDate) {
        // Default to 30 days ago
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        startDate = thirtyDaysAgo.toISOString();
      }
      
      if (!endDate) {
        // Default to now
        endDate = new Date().toISOString();
      }
      
      const usage = await serviceManager.getServiceUsage(
        userId,
        serviceNameOrId,
        new Date(startDate as string),
        new Date(endDate as string)
      );
      
      res.status(200).json({ usage });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Record service usage
   */
  async recordServiceUsage(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const {
        userId,
        serviceNameOrId,
        endpoint,
        requestCount,
        dataProcessed,
        responseTime,
        status,
        errorDetails,
        metadata
      } = req.body;
      
      if (!userId || !serviceNameOrId || !endpoint) {
        throw new ValidationError('User ID, service name/ID, and endpoint are required');
      }
      
      const metrics: any = {};
      if (requestCount) metrics.requestCount = requestCount;
      if (dataProcessed) metrics.dataProcessed = dataProcessed;
      if (responseTime) metrics.responseTime = responseTime;
      if (status) metrics.status = status;
      if (errorDetails) metrics.errorDetails = errorDetails;
      if (metadata) metrics.metadata = metadata;
      
      await serviceManager.recordServiceUsage(
        userId,
        serviceNameOrId,
        endpoint,
        metrics
      );
      
      res.status(200).json({
        success: true,
        message: 'Service usage recorded successfully'
      });
    } catch (error) {
      next(error);
    }
  }
  
  /**
   * Validate service API key (for service-to-service communication)
   */
  async validateApiKey(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { apiKey, apiSecret } = req.body;
      
      if (!apiKey || !apiSecret) {
        throw new ValidationError('API key and secret are required');
      }
      
      const service = await serviceManager.validateServiceApiKey(apiKey, apiSecret);
      
      if (!service) {
        res.status(401).json({
          success: false,
          message: 'Invalid API key or secret'
        });
        return;
      }
      
      res.status(200).json({
        success: true,
        service: {
          id: service.id,
          name: service.name,
          displayName: service.displayName
        }
      });
    } catch (error) {
      next(error);
    }
  }
} 