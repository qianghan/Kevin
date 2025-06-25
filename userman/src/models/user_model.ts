import mongoose, { Document, Schema, Model, HydratedDocument } from 'mongoose';

/**
 * User preferences interface with customizable settings
 */
export interface UserPreferences {
  theme?: 'light' | 'dark' | 'system';
  emailNotifications?: boolean;
  language?: string;
  [key: string]: any; // Allow for extensibility
}

/**
 * Profile completeness tracking interface
 */
export interface ProfileCompleteness {
  score: number; // Overall completeness score (0-100)
  missingFields: string[]; // Array of field names that are missing
  lastUpdated: Date; // When the score was last calculated
}

/**
 * Base user properties shared across the system
 */
export interface BaseUser {
  email: string;
  name: string;
  image?: string;
  password?: string;
  emailVerified?: Date;
  preferences?: UserPreferences;
  testMode?: boolean; // Flag to indicate if user is in test mode
  profileCompleteness?: ProfileCompleteness; // Profile completeness tracking
  lastLoginAt?: Date; // When the user last logged in
  failedLoginAttempts?: number; // Number of consecutive failed login attempts
  lockedUntil?: Date; // Timestamp until which the account is locked
  createdAt: Date;
  updatedAt: Date;
}

export enum UserRole {
  ADMIN = 'admin',
  STUDENT = 'student',
  PARENT = 'parent',
  SUPPORT = 'support'
}

/**
 * User document interface
 */
export interface UserDocument extends Document {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  name: string; // Full name (computed from firstName and lastName)
  role: UserRole;
  image?: string;
  emailVerified: boolean;
  preferences?: UserPreferences;
  testMode?: boolean;
  profileCompleteness?: ProfileCompleteness;
  createdAt: Date;
  updatedAt: Date;
  failedLoginAttempts?: number;
  lockedUntil?: Date;
  lastLogin?: Date;
  services?: string[];
  studentIds?: string[];
  parentIds?: string[];
  partnerIds?: string[];
}

/**
 * Interface for the User model with static methods
 */
export interface UserModel extends Model<UserDocument, {}, {}, {}, any> {
  findOne(filter: any): Promise<UserDocument | null>;
  findByEmail(email: string): Promise<UserDocument | null>;
  findByIds(ids: string[]): Promise<UserDocument[]>;
  findStudents(userId: string): Promise<UserDocument[]>;
  findParents(userId: string): Promise<UserDocument[]>;
  findByRole(role: UserRole): Promise<UserDocument[]>;
  findByRoles(roles: UserRole[]): Promise<UserDocument[]>;
  findByService(serviceName: string): Promise<UserDocument[]>;
  findByServiceAndRole(serviceName: string, role: UserRole): Promise<UserDocument[]>;
  findByServiceAndRoles(serviceName: string, roles: UserRole[]): Promise<UserDocument[]>;
}

/**
 * Create the user schema
 */
const userSchema = new Schema<UserDocument, UserModel>({
  email: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    lowercase: true
  },
  password: {
    type: String,
    required: true
  },
  firstName: {
    type: String,
    required: true,
    trim: true
  },
  lastName: {
    type: String,
    required: true,
    trim: true
  },
  name: {
    type: String,
    required: true,
    trim: true
  },
  role: {
    type: String,
    enum: Object.values(UserRole),
    required: true
  },
  image: {
    type: String
  },
  emailVerified: {
    type: Boolean,
    default: false
  },
  preferences: {
    type: Schema.Types.Mixed,
    default: {}
  },
  testMode: {
    type: Boolean,
    default: false
  },
  profileCompleteness: {
    score: {
      type: Number,
      default: 0
    },
    missingFields: [{
      type: String
    }],
    lastUpdated: {
      type: Date
    }
  },
  failedLoginAttempts: {
    type: Number,
    default: 0
  },
  lockedUntil: {
    type: Date
  },
  lastLogin: {
    type: Date
  },
  services: [{
    type: String
  }],
  studentIds: [{
    type: Schema.Types.ObjectId,
    ref: 'User'
  }],
  parentIds: [{
    type: Schema.Types.ObjectId,
    ref: 'User'
  }],
  partnerIds: [{
    type: Schema.Types.ObjectId,
    ref: 'User'
  }]
}, {
  timestamps: true
});

// Add indexes for commonly queried fields
userSchema.index({ email: 1 });
userSchema.index({ role: 1 });

// Add static methods
userSchema.statics.findByEmail = function(email: string): Promise<UserDocument | null> {
  return this.findOne({ email });
};

// Create and export the model
export const User = mongoose.model<UserDocument, UserModel>('User', userSchema);
export default User; 