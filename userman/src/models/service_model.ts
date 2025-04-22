import mongoose, { Schema } from 'mongoose';

/**
 * Service status options
 */
export enum ServiceStatus {
  Active = 'ACTIVE',
  Inactive = 'INACTIVE',
  Beta = 'BETA',
  Deprecated = 'DEPRECATED'
}

/**
 * Service access levels
 */
export enum ServiceAccessLevel {
  Public = 'PUBLIC',       // Available to all users
  RoleBased = 'ROLE_BASED', // Available based on roles
  Restricted = 'RESTRICTED' // Requires explicit permission
}

// Create the service schema
const serviceSchema = new Schema(
  {
    name: {
      type: String,
      required: true,
      unique: true,
      trim: true
    },
    displayName: {
      type: String,
      required: true
    },
    description: {
      type: String,
      required: true
    },
    apiKey: {
      type: String,
      required: true,
      unique: true
    },
    apiSecret: {
      type: String,
      required: true
    },
    baseUrl: {
      type: String,
      required: true
    },
    callbackUrl: {
      type: String
    },
    status: {
      type: String,
      enum: Object.values(ServiceStatus),
      default: ServiceStatus.Active
    },
    accessLevel: {
      type: String,
      enum: Object.values(ServiceAccessLevel),
      default: ServiceAccessLevel.RoleBased
    },
    allowedRoles: {
      type: [String],
      default: ['admin'] // Default to admin-only access
    },
    features: {
      type: [String],
      default: []
    },
    config: {
      type: Schema.Types.Mixed,
      default: {}
    },
    usageLimits: {
      // Optional usage limits or quotas
      type: Schema.Types.Mixed,
      default: null
    },
    isSystem: {
      // Whether this is a core system service
      type: Boolean,
      default: false
    },
    icon: {
      type: String,
      default: null
    }
  },
  { timestamps: true }
);

// Create indexes for efficient lookups
serviceSchema.index({ name: 1 }, { unique: true });
serviceSchema.index({ apiKey: 1 }, { unique: true });
serviceSchema.index({ status: 1 });

// Create and export the model
const ServiceModel = mongoose.model('Service', serviceSchema);
export { ServiceModel }; 