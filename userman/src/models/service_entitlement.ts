import mongoose, { Document, Schema } from 'mongoose';
import { ServiceStatus } from '../services/service_registry';

/**
 * Status for the entitlement
 */
export enum EntitlementStatus {
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
  EXPIRED = 'expired',
  REVOKED = 'revoked'
}

/**
 * Service entitlement interface
 */
export interface ServiceEntitlement {
  userId: string;
  serviceId: string;
  status: EntitlementStatus;
  grantedBy?: string; // ID of admin who granted access
  grantedAt: Date;
  expiresAt?: Date;
  lastAccessed?: Date;
  suspendedAt?: Date;
  suspendedReason?: string;
  usageCount: number;
  additionalPermissions?: string[]; // Special permissions beyond the default for service
  metadata?: Record<string, any>; // Additional service-specific data
}

/**
 * Service entitlement document for MongoDB
 */
export interface ServiceEntitlementDocument extends Document, Omit<ServiceEntitlement, 'userId'> {
  userId: mongoose.Types.ObjectId;
}

/**
 * Service entitlement schema
 */
const ServiceEntitlementSchema = new Schema<ServiceEntitlementDocument>(
  {
    userId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true
    },
    serviceId: {
      type: String,
      required: true,
      index: true
    },
    status: {
      type: String,
      enum: Object.values(EntitlementStatus),
      default: EntitlementStatus.ACTIVE,
      index: true
    },
    grantedBy: {
      type: Schema.Types.ObjectId,
      ref: 'User'
    },
    grantedAt: {
      type: Date,
      default: Date.now
    },
    expiresAt: {
      type: Date
    },
    lastAccessed: {
      type: Date
    },
    suspendedAt: {
      type: Date
    },
    suspendedReason: {
      type: String
    },
    usageCount: {
      type: Number,
      default: 0
    },
    additionalPermissions: {
      type: [String]
    },
    metadata: {
      type: Schema.Types.Mixed
    }
  },
  {
    timestamps: true
  }
);

// Create compound index for userId + serviceId for efficient lookups
ServiceEntitlementSchema.index({ userId: 1, serviceId: 1 }, { unique: true });
ServiceEntitlementSchema.index({ expiresAt: 1 }, { sparse: true });

/**
 * Service entitlement model for tracking user access to services
 */
export const ServiceEntitlementModel = mongoose.models.ServiceEntitlement ||
  mongoose.model<ServiceEntitlementDocument>('ServiceEntitlement', ServiceEntitlementSchema);

/**
 * Helper function to track service usage
 */
export const trackServiceUsage = async (userId: string, serviceId: string): Promise<boolean> => {
  try {
    const result = await ServiceEntitlementModel.updateOne(
      { 
        userId: new mongoose.Types.ObjectId(userId), 
        serviceId,
        status: EntitlementStatus.ACTIVE
      },
      { 
        $inc: { usageCount: 1 },
        $set: { lastAccessed: new Date() }
      }
    );
    
    return result.modifiedCount > 0;
  } catch (error) {
    console.error(`Error tracking service usage for ${userId}/${serviceId}:`, error);
    return false;
  }
}; 