import { ServiceModel, ServiceStatus, ServiceAccessLevel } from '../models/service_model';
import { EntitlementModel, EntitlementStatus, SubscriptionType } from '../models/service_entitlement_model';
import { UsageModel } from '../models/service_usage_model';
import { NotFoundError, ValidationError, AuthorizationError, DuplicateError } from '../utils/errors';
import { generateRandomToken } from '../utils/crypto';
import mongoose from 'mongoose';

/**
 * DTO for service information
 */
export interface ServiceDTO {
  id: string;
  name: string;
  displayName: string;
  description: string;
  baseUrl: string;
  callbackUrl?: string;
  status: ServiceStatus;
  accessLevel: ServiceAccessLevel;
  allowedRoles: string[];
  features: string[];
  isSystem: boolean;
  icon?: string;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * DTO for entitlement information
 */
export interface EntitlementDTO {
  id: string;
  userId: string;
  serviceId: string;
  serviceName?: string;
  status: EntitlementStatus;
  subscriptionType: SubscriptionType;
  features: string[];
  quotaLimits?: any;
  quotaUsed?: any;
  startDate: Date;
  expiryDate?: Date;
  lastUsed?: Date;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Service for managing services and entitlements
 */
export class ServiceManagementService {
  /**
   * Register a new service
   */
  async registerService(
    serviceData: Omit<ServiceDTO, 'id' | 'createdAt' | 'updatedAt'> & { apiSecret?: string }
  ): Promise<ServiceDTO> {
    // Check if service with this name already exists
    const existingService = await ServiceModel.findOne({ name: serviceData.name });
    if (existingService) {
      throw new DuplicateError(`Service with name '${serviceData.name}' already exists`);
    }

    // Generate API key and secret if not provided
    const apiKey = generateRandomToken(16);
    const apiSecret = serviceData.apiSecret || generateRandomToken(32);

    // Create the service
    const service = await ServiceModel.create({
      ...serviceData,
      apiKey,
      apiSecret
    });

    return this.mapServiceToDTO(service);
  }

  /**
   * Get a list of services with optional filtering
   */
  async getServices(filter: Partial<ServiceDTO> = {}): Promise<ServiceDTO[]> {
    const query: any = {};

    if (filter.status) {
      query.status = filter.status;
    }

    if (filter.accessLevel) {
      query.accessLevel = filter.accessLevel;
    }

    if (filter.isSystem !== undefined) {
      query.isSystem = filter.isSystem;
    }

    const services = await ServiceModel.find(query).sort({ displayName: 1 });
    return services.map(service => this.mapServiceToDTO(service));
  }

  /**
   * Get a service by ID
   */
  async getServiceById(serviceId: string): Promise<ServiceDTO> {
    const service = await ServiceModel.findById(serviceId);
    if (!service) {
      throw new NotFoundError('Service not found');
    }

    return this.mapServiceToDTO(service);
  }

  /**
   * Get a service by name
   */
  async getServiceByName(name: string): Promise<ServiceDTO> {
    const service = await ServiceModel.findOne({ name });
    if (!service) {
      throw new NotFoundError('Service not found');
    }

    return this.mapServiceToDTO(service);
  }

  /**
   * Update a service
   */
  async updateService(
    serviceId: string,
    updates: Partial<ServiceDTO>
  ): Promise<ServiceDTO> {
    const service = await ServiceModel.findById(serviceId);
    if (!service) {
      throw new NotFoundError('Service not found');
    }

    // Prevent updating critical fields
    delete (updates as any).apiKey;
    delete (updates as any).apiSecret;
    delete (updates as any).name; // Name is immutable

    // Update the service
    Object.assign(service, updates);
    await service.save();

    return this.mapServiceToDTO(service);
  }

  /**
   * Delete a service (soft delete by setting status to inactive)
   */
  async deleteService(serviceId: string): Promise<boolean> {
    const service = await ServiceModel.findById(serviceId);
    if (!service) {
      throw new NotFoundError('Service not found');
    }

    // Prevent deleting system services
    if (service.isSystem) {
      throw new ValidationError('Cannot delete a system service');
    }

    // Soft delete by setting status to inactive
    service.status = ServiceStatus.Inactive;
    await service.save();

    return true;
  }

  /**
   * Grant service access to a user
   */
  async grantServiceAccess(
    userId: string,
    serviceId: string,
    options: {
      subscriptionType?: SubscriptionType;
      features?: string[];
      quotaLimits?: any;
      expiryDate?: Date;
      grantedBy?: string;
      metadata?: any;
    } = {}
  ): Promise<EntitlementDTO> {
    // Check if service exists
    const service = await ServiceModel.findById(serviceId);
    if (!service) {
      throw new NotFoundError('Service not found');
    }

    // Check if entitlement already exists
    let entitlement = await EntitlementModel.findOne({ userId, serviceId });

    if (entitlement) {
      // Update existing entitlement
      entitlement.status = EntitlementStatus.Active;
      entitlement.subscriptionType = options.subscriptionType || entitlement.subscriptionType;
      
      if (options.features) {
        entitlement.features = options.features;
      }
      
      if (options.quotaLimits) {
        entitlement.quotaLimits = options.quotaLimits;
      }
      
      if (options.expiryDate) {
        entitlement.expiryDate = options.expiryDate;
      }
      
      if (options.grantedBy) {
        entitlement.grantedBy = new mongoose.Types.ObjectId(options.grantedBy);
      }
      
      if (options.metadata) {
        entitlement.metadata = { ...entitlement.metadata, ...options.metadata };
      }
    } else {
      // Create new entitlement
      entitlement = new EntitlementModel({
        userId,
        serviceId,
        status: EntitlementStatus.Active,
        subscriptionType: options.subscriptionType || SubscriptionType.Free,
        features: options.features || [],
        quotaLimits: options.quotaLimits || null,
        expiryDate: options.expiryDate || null,
        grantedBy: options.grantedBy ? new mongoose.Types.ObjectId(options.grantedBy) : null,
        metadata: options.metadata || {}
      });
    }

    await entitlement.save();
    
    return this.mapEntitlementToDTO(entitlement, service.name);
  }

  /**
   * Revoke service access from a user
   */
  async revokeServiceAccess(userId: string, serviceId: string): Promise<boolean> {
    // Find the entitlement
    const entitlement = await EntitlementModel.findOne({ userId, serviceId });
    if (!entitlement) {
      return false; // No entitlement to revoke
    }

    // Set status to suspended
    entitlement.status = EntitlementStatus.Suspended;
    await entitlement.save();

    return true;
  }

  /**
   * Check if a user has access to a service
   */
  async checkServiceAccess(
    userId: string,
    serviceNameOrId: string
  ): Promise<{ hasAccess: boolean; entitlement?: EntitlementDTO }> {
    // Find the service by name or ID
    const service = serviceNameOrId.match(/^[0-9a-fA-F]{24}$/)
      ? await ServiceModel.findById(serviceNameOrId)
      : await ServiceModel.findOne({ name: serviceNameOrId });

    if (!service) {
      throw new NotFoundError('Service not found');
    }

    // For public services, access is always granted
    if (service.accessLevel === ServiceAccessLevel.Public) {
      return { hasAccess: true };
    }

    // Find the user's entitlement for this service
    const entitlement = await EntitlementModel.findOne({
      userId,
      serviceId: service._id,
      status: EntitlementStatus.Active
    });

    // If entitlement exists and is active, user has access
    if (entitlement) {
      // Check if entitlement has expired
      if (entitlement.expiryDate && entitlement.expiryDate < new Date()) {
        entitlement.status = EntitlementStatus.Expired;
        await entitlement.save();
        return { hasAccess: false };
      }

      // Update last used time
      entitlement.lastUsed = new Date();
      await entitlement.save();

      return {
        hasAccess: true,
        entitlement: this.mapEntitlementToDTO(entitlement, service.name)
      };
    }

    // For role-based services, check if user's role is in allowed roles
    // This would require the user object, so we'd typically get this from the request
    // For now, we'll return false as we can't check the role here
    return { hasAccess: false };
  }

  /**
   * Get a user's entitlements
   */
  async getUserEntitlements(userId: string): Promise<EntitlementDTO[]> {
    const entitlements = await EntitlementModel.find({
      userId,
      status: { $in: [EntitlementStatus.Active, EntitlementStatus.Suspended] }
    }).sort({ createdAt: -1 });

    // Fetch service names for the entitlements
    const serviceIds = entitlements.map(e => e.serviceId);
    const services = await ServiceModel.find({ _id: { $in: serviceIds } });
    
    // Create a map of service ID to name
    const serviceMap = new Map();
    services.forEach(service => {
      serviceMap.set(service._id.toString(), service.name);
    });

    return entitlements.map(entitlement => 
      this.mapEntitlementToDTO(
        entitlement, 
        serviceMap.get(entitlement.serviceId.toString())
      )
    );
  }

  /**
   * Record service usage
   */
  async recordServiceUsage(
    userId: string,
    serviceNameOrId: string,
    endpoint: string,
    metrics: {
      requestCount?: number;
      dataProcessed?: number;
      responseTime?: number;
      status?: string;
      errorDetails?: any;
      metadata?: any;
    } = {}
  ): Promise<void> {
    // Find the service by name or ID
    const service = serviceNameOrId.match(/^[0-9a-fA-F]{24}$/)
      ? await ServiceModel.findById(serviceNameOrId)
      : await ServiceModel.findOne({ name: serviceNameOrId });

    if (!service) {
      throw new NotFoundError('Service not found');
    }

    // Record the usage
    await UsageModel.recordUsage(userId, service._id.toString(), endpoint, metrics);

    // Update entitlement quota used if applicable
    const entitlement = await EntitlementModel.findOne({
      userId,
      serviceId: service._id,
      status: EntitlementStatus.Active
    });

    if (entitlement && entitlement.quotaLimits) {
      // Initialize quota used if not set
      if (!entitlement.quotaUsed) {
        entitlement.quotaUsed = {};
      }

      // Update request count
      const requestCount = metrics.requestCount || 1;
      entitlement.quotaUsed.requestCount = (entitlement.quotaUsed.requestCount || 0) + requestCount;

      // Update data processed
      if (metrics.dataProcessed) {
        entitlement.quotaUsed.dataProcessed = 
          (entitlement.quotaUsed.dataProcessed || 0) + metrics.dataProcessed;
      }

      // Save updated entitlement
      await entitlement.save();
    }
  }

  /**
   * Get service usage for a user
   */
  async getServiceUsage(
    userId: string,
    serviceNameOrId: string,
    startDate: Date,
    endDate: Date
  ): Promise<any> {
    // Find the service by name or ID
    const service = serviceNameOrId.match(/^[0-9a-fA-F]{24}$/)
      ? await ServiceModel.findById(serviceNameOrId)
      : await ServiceModel.findOne({ name: serviceNameOrId });

    if (!service) {
      throw new NotFoundError('Service not found');
    }

    // Get aggregated usage data
    const usageData = await UsageModel.getAggregatedUsage(
      userId,
      service._id.toString(),
      startDate,
      endDate
    );

    return usageData[0] || {
      totalRequests: 0,
      totalDataProcessed: 0,
      avgResponseTime: 0,
      successCount: 0,
      failureCount: 0,
      throttledCount: 0,
      errorCount: 0
    };
  }

  /**
   * Validate a service API key for service-to-service communication
   */
  async validateServiceApiKey(apiKey: string, apiSecret: string): Promise<ServiceDTO | null> {
    const service = await ServiceModel.findOne({ apiKey });
    
    if (!service) {
      return null;
    }

    // Validate the API secret
    if (service.apiSecret !== apiSecret) {
      return null;
    }

    // Only active services can use the API
    if (service.status !== ServiceStatus.Active) {
      return null;
    }

    return this.mapServiceToDTO(service);
  }

  /**
   * Map a service document to DTO
   */
  private mapServiceToDTO(service: any): ServiceDTO {
    return {
      id: service._id.toString(),
      name: service.name,
      displayName: service.displayName,
      description: service.description,
      baseUrl: service.baseUrl,
      callbackUrl: service.callbackUrl,
      status: service.status,
      accessLevel: service.accessLevel,
      allowedRoles: service.allowedRoles,
      features: service.features,
      isSystem: service.isSystem,
      icon: service.icon,
      createdAt: service.createdAt,
      updatedAt: service.updatedAt
    };
  }

  /**
   * Map an entitlement document to DTO
   */
  private mapEntitlementToDTO(entitlement: any, serviceName?: string): EntitlementDTO {
    return {
      id: entitlement._id.toString(),
      userId: entitlement.userId.toString(),
      serviceId: entitlement.serviceId.toString(),
      serviceName,
      status: entitlement.status,
      subscriptionType: entitlement.subscriptionType,
      features: entitlement.features,
      quotaLimits: entitlement.quotaLimits,
      quotaUsed: entitlement.quotaUsed,
      startDate: entitlement.startDate,
      expiryDate: entitlement.expiryDate,
      lastUsed: entitlement.lastUsed,
      createdAt: entitlement.createdAt,
      updatedAt: entitlement.updatedAt
    };
  }

  /**
   * Get all services available to a user
   * @param userId User ID to check
   * @returns Array of services with entitlement details
   */
  async getUserServices(userId: string): Promise<{
    serviceName: string;
    hasAccess: boolean;
    entitlement: EntitlementDTO | null;
  }[]> {
    // Verify user exists
    const userModel = mongoose.model('User');
    const user = await userModel.findById(userId);
    if (!user) {
      throw new NotFoundError('User not found');
    }

    // Get all services
    const services = await ServiceModel.find({});
    
    // Get all entitlements for this user
    const entitlements = await EntitlementModel.find({ userId });
    
    // Map services to include access information
    return Promise.all(
      services.map(async (service: any) => {
        const entitlement = entitlements.find(
          (e: any) => e.serviceId.toString() === service._id.toString()
        );
        
        return {
          serviceName: service.name,
          hasAccess: !!entitlement,
          entitlement: entitlement ? this.mapEntitlementToDTO(entitlement, service.name) : null
        };
      })
    );
  }
} 