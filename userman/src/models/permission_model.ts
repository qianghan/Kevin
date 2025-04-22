import mongoose, { Schema } from 'mongoose';

/**
 * Permission resource types that can be controlled
 */
export enum ResourceType {
  User = 'USER',
  Service = 'SERVICE',
  Invitation = 'INVITATION',
  Relationship = 'RELATIONSHIP',
  Dashboard = 'DASHBOARD',
  Report = 'REPORT',
  System = 'SYSTEM'
}

/**
 * Permission action types
 */
export enum ActionType {
  Create = 'CREATE',
  Read = 'READ',
  Update = 'UPDATE',
  Delete = 'DELETE',
  Manage = 'MANAGE', // Combines multiple actions
  Execute = 'EXECUTE' // For running operations
}

/**
 * Predefined permissions for different roles
 */
export const RolePermissions = {
  // Admin has full access to everything
  admin: [
    { resource: ResourceType.User, action: ActionType.Manage },
    { resource: ResourceType.Service, action: ActionType.Manage },
    { resource: ResourceType.Invitation, action: ActionType.Manage },
    { resource: ResourceType.Relationship, action: ActionType.Manage },
    { resource: ResourceType.Dashboard, action: ActionType.Manage },
    { resource: ResourceType.Report, action: ActionType.Manage },
    { resource: ResourceType.System, action: ActionType.Manage }
  ],
  
  // Support has read access to most things, plus ability to help users
  support: [
    { resource: ResourceType.User, action: ActionType.Read },
    { resource: ResourceType.Service, action: ActionType.Read },
    { resource: ResourceType.Invitation, action: ActionType.Read },
    { resource: ResourceType.Relationship, action: ActionType.Read },
    { resource: ResourceType.Dashboard, action: ActionType.Read },
    { resource: ResourceType.Report, action: ActionType.Read },
    { resource: ResourceType.User, action: ActionType.Execute } // For support actions
  ],
  
  // Parent can manage their own students and relationships
  parent: [
    { resource: ResourceType.User, action: ActionType.Read },
    { resource: ResourceType.Invitation, action: ActionType.Create },
    { resource: ResourceType.Invitation, action: ActionType.Read },
    { resource: ResourceType.Invitation, action: ActionType.Update },
    { resource: ResourceType.Relationship, action: ActionType.Manage }
  ],
  
  // Student has basic access and can manage own data
  student: [
    { resource: ResourceType.User, action: ActionType.Read },
    { resource: ResourceType.Invitation, action: ActionType.Read },
    { resource: ResourceType.Invitation, action: ActionType.Update }
  ]
};

// Create the permission schema
const permissionSchema = new Schema(
  {
    role: {
      type: String,
      required: true,
      index: true
    },
    resource: {
      type: String,
      enum: Object.values(ResourceType),
      required: true
    },
    action: {
      type: String,
      enum: Object.values(ActionType),
      required: true
    },
    conditions: {
      // Optional JSON conditions for fine-grained permissions
      // e.g., { ownResourceOnly: true } or { serviceName: "chatService" }
      type: Schema.Types.Mixed,
      default: {}
    }
  },
  { timestamps: true }
);

// Create a compound index for efficient permission lookups
permissionSchema.index({ role: 1, resource: 1, action: 1 }, { unique: true });

// Create and export the model
const PermissionModel = mongoose.model('Permission', permissionSchema);
export { PermissionModel }; 