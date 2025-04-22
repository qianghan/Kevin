import mongoose, { Schema } from 'mongoose';

/**
 * Entitlement status enum
 */
export enum EntitlementStatus {
  Active = 'ACTIVE',
  Suspended = 'SUSPENDED',
  Expired = 'EXPIRED'
}

/**
 * Subscription types
 */
export enum SubscriptionType {
  Free = 'FREE',
  Basic = 'BASIC',
  Premium = 'PREMIUM',
  Enterprise = 'ENTERPRISE',
  Custom = 'CUSTOM'
}

// Create the service entitlement schema
const entitlementSchema = new Schema(
  {
    userId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true
    },
    serviceId: {
      type: Schema.Types.ObjectId,
      ref: 'Service',
      required: true
    },
    status: {
      type: String,
      enum: Object.values(EntitlementStatus),
      default: EntitlementStatus.Active
    },
    subscriptionType: {
      type: String,
      enum: Object.values(SubscriptionType),
      default: SubscriptionType.Free
    },
    features: {
      // Optional additional features enabled for this user
      type: [String],
      default: []
    },
    quotaLimits: {
      // Custom quota limits for this entitlement
      type: Schema.Types.Mixed,
      default: null
    },
    quotaUsed: {
      // Tracking quota usage
      type: Schema.Types.Mixed,
      default: {}
    },
    startDate: {
      type: Date,
      default: Date.now
    },
    expiryDate: {
      // Optional expiry date for the entitlement
      type: Date,
      default: null
    },
    lastUsed: {
      // Track when the service was last used
      type: Date,
      default: null
    },
    grantedBy: {
      // User ID of admin who granted access
      type: Schema.Types.ObjectId,
      ref: 'User',
      default: null
    },
    metadata: {
      // Additional metadata specific to the service
      type: Schema.Types.Mixed,
      default: {}
    }
  },
  { timestamps: true }
);

// Create compound index for user-service uniqueness
entitlementSchema.index({ userId: 1, serviceId: 1 }, { unique: true });
// Additional indexes for querying
entitlementSchema.index({ userId: 1, status: 1 });
entitlementSchema.index({ serviceId: 1, status: 1 });
entitlementSchema.index({ expiryDate: 1 });

// Create and export the model
const EntitlementModel = mongoose.model('Entitlement', entitlementSchema);
export { EntitlementModel }; 