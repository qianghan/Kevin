import mongoose, { Document, Model, Schema } from 'mongoose';
import { UserRole } from '../models/user_model';

/**
 * Status for services in the platform
 */
export enum ServiceStatus {
  ACTIVE = 'active',
  MAINTENANCE = 'maintenance',
  DEPRECATED = 'deprecated',
  DISABLED = 'disabled'
}

/**
 * Type for service access roles
 */
export type ServiceAccessRole = UserRole | 'any' | 'premium';

/**
 * Service definition interface
 */
export interface ServiceDefinition {
  id: string;
  name: string;
  description: string;
  baseUrl: string;
  apiKey?: string;
  status: ServiceStatus;
  allowedRoles: ServiceAccessRole[];
  webhookUrl?: string;
  webhookSecret?: string;
  configOptions?: Record<string, any>;
  createdAt?: Date;
  updatedAt?: Date;
}

/**
 * Service definition document for MongoDB
 */
export interface ServiceDefinitionDocument extends Omit<Document, 'id'>, Omit<ServiceDefinition, 'id'> {
  id: string;
}

/**
 * Service definition schema
 */
const ServiceDefinitionSchema = new Schema<ServiceDefinitionDocument>(
  {
    id: {
      type: String,
      required: true,
      unique: true,
      index: true
    },
    name: {
      type: String,
      required: true
    },
    description: {
      type: String,
      required: true
    },
    baseUrl: {
      type: String,
      required: true
    },
    apiKey: {
      type: String
    },
    status: {
      type: String,
      enum: Object.values(ServiceStatus),
      default: ServiceStatus.ACTIVE,
      index: true
    },
    allowedRoles: {
      type: [String],
      required: true,
      validate: {
        validator: function(roles: string[]) {
          const validRoles = ['admin', 'teacher', 'student', 'parent', 'any', 'premium'];
          return roles.every(role => validRoles.includes(role));
        },
        message: 'Invalid role provided for service access'
      }
    },
    webhookUrl: {
      type: String
    },
    webhookSecret: {
      type: String
    },
    configOptions: {
      type: Schema.Types.Mixed
    }
  },
  {
    timestamps: true
  }
);

/**
 * Service definition model
 */
export const ServiceDefinitionModel: Model<
  ServiceDefinitionDocument, 
  {}, 
  {}, 
  {}, 
  Document<unknown, {}, ServiceDefinitionDocument> & ServiceDefinitionDocument,
  Schema<ServiceDefinitionDocument, Model<ServiceDefinitionDocument, {}, {}, {}, any, any, {}>>,
  {}
> = mongoose.models.ServiceDefinition || 
  mongoose.model<ServiceDefinitionDocument>('ServiceDefinition', ServiceDefinitionSchema);

/**
 * Service registry for managing service integrations
 */
export class ServiceRegistry {
  /**
   * Register a new service
   * @param service The service definition to register
   */
  async registerService(service: ServiceDefinition): Promise<ServiceDefinition> {
    try {
      const existingService = await ServiceDefinitionModel.findOne({ id: service.id });
      
      if (existingService) {
        // Update existing service
        Object.assign(existingService, service);
        await existingService.save();
        return this.mapServiceDocument(existingService);
      }
      
      // Create new service
      const newService = new ServiceDefinitionModel(service);
      await newService.save();
      return this.mapServiceDocument(newService);
    } catch (error) {
      console.error(`Error registering service ${service.id}:`, error);
      throw new Error(`Failed to register service: ${(error as Error).message}`);
    }
  }

  /**
   * Get a service by ID
   * @param serviceId Service ID to retrieve
   */
  async getServiceById(serviceId: string): Promise<ServiceDefinition | null> {
    try {
      const service = await ServiceDefinitionModel.findOne({ id: serviceId });
      return service ? this.mapServiceDocument(service) : null;
    } catch (error) {
      console.error(`Error getting service ${serviceId}:`, error);
      throw new Error(`Failed to get service: ${(error as Error).message}`);
    }
  }

  /**
   * Get all registered services
   * @param status Optional status filter
   */
  async getAllServices(status?: ServiceStatus): Promise<ServiceDefinition[]> {
    try {
      const query = status ? { status } : {};
      const services = await ServiceDefinitionModel.find(query);
      return services.map(service => this.mapServiceDocument(service));
    } catch (error) {
      console.error('Error getting all services:', error);
      throw new Error(`Failed to get services: ${(error as Error).message}`);
    }
  }

  /**
   * Update service status
   * @param serviceId Service ID to update
   * @param status New status
   */
  async updateServiceStatus(serviceId: string, status: ServiceStatus): Promise<boolean> {
    try {
      const result = await ServiceDefinitionModel.updateOne(
        { id: serviceId },
        { status }
      );
      return result.modifiedCount > 0;
    } catch (error) {
      console.error(`Error updating service status for ${serviceId}:`, error);
      throw new Error(`Failed to update service status: ${(error as Error).message}`);
    }
  }

  /**
   * Check if a user can access a service based on their role
   * @param serviceId Service ID to check
   * @param userRole User's role
   */
  async canAccessService(serviceId: string, userRole: UserRole | string): Promise<boolean> {
    try {
      const service = await this.getServiceById(serviceId);
      
      if (!service) {
        return false;
      }
      
      // If service is not active, only admins can access
      if (service.status !== ServiceStatus.ACTIVE && userRole !== 'admin') {
        return false;
      }
      
      // Check role access
      return service.allowedRoles.includes('any') || 
             service.allowedRoles.includes(userRole as ServiceAccessRole);
    } catch (error) {
      console.error(`Error checking service access for ${serviceId}:`, error);
      return false;
    }
  }

  /**
   * Map service document to service definition
   */
  private mapServiceDocument(doc: ServiceDefinitionDocument): ServiceDefinition {
    return {
      id: doc.id,
      name: doc.name,
      description: doc.description,
      baseUrl: doc.baseUrl,
      apiKey: doc.apiKey,
      status: doc.status as ServiceStatus,
      allowedRoles: doc.allowedRoles as ServiceAccessRole[],
      webhookUrl: doc.webhookUrl,
      webhookSecret: doc.webhookSecret,
      configOptions: doc.configOptions,
      createdAt: doc.createdAt,
      updatedAt: doc.updatedAt
    };
  }
} 