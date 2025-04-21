import mongoose, { Document, Schema, Model } from 'mongoose';

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
 * Base user properties shared across the system
 */
export interface BaseUser {
  email: string;
  name: string;
  image?: string;
  password?: string;
  emailVerified?: Date;
  preferences?: UserPreferences;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Available user roles in the system
 */
export type UserRole = 'student' | 'parent' | 'admin';

/**
 * Mongoose document interface for User
 */
export interface UserDocument extends Document, BaseUser {
  role: UserRole;
  studentIds?: mongoose.Types.ObjectId[]; // For parent accounts
  parentIds?: mongoose.Types.ObjectId[]; // For student accounts
  partnerIds?: mongoose.Types.ObjectId[]; // For parent accounts (co-parents)
}

/**
 * User schema for MongoDB storage
 */
const UserSchema = new Schema<UserDocument>(
  {
    email: {
      type: String,
      required: true,
      unique: true,
      trim: true,
      lowercase: true,
    },
    name: {
      type: String,
      required: true,
      trim: true,
    },
    password: {
      type: String,
    },
    image: {
      type: String,
    },
    emailVerified: {
      type: Date,
    },
    role: {
      type: String,
      enum: ['student', 'parent', 'admin'],
      required: true,
      default: 'student',
    },
    studentIds: [{
      type: Schema.Types.ObjectId,
      ref: 'User',
    }],
    parentIds: [{
      type: Schema.Types.ObjectId,
      ref: 'User',
    }],
    partnerIds: [{
      type: Schema.Types.ObjectId,
      ref: 'User',
    }],
    preferences: {
      type: Schema.Types.Mixed,
      default: {
        theme: 'system',
        emailNotifications: true,
        language: 'en'
      }
    }
  },
  {
    timestamps: true,
  }
);

// Add indexes for commonly queried fields
UserSchema.index({ email: 1 });
UserSchema.index({ role: 1 });
UserSchema.index({ studentIds: 1 });
UserSchema.index({ parentIds: 1 });

/**
 * Interface for the User model with static methods
 */
export interface UserModel extends Model<UserDocument> {
  findByEmail(email: string): Promise<UserDocument | null>;
  findByIds(ids: string[]): Promise<UserDocument[]>;
  findStudents(parentId: string): Promise<UserDocument[]>;
  findParents(studentId: string): Promise<UserDocument[]>;
}

// Static method implementations
UserSchema.statics.findByEmail = async function(email: string): Promise<UserDocument | null> {
  return this.findOne({ email: email.toLowerCase() });
};

UserSchema.statics.findByIds = async function(ids: string[]): Promise<UserDocument[]> {
  return this.find({ _id: { $in: ids } });
};

UserSchema.statics.findStudents = async function(parentId: string): Promise<UserDocument[]> {
  return this.find({ parentIds: parentId });
};

UserSchema.statics.findParents = async function(studentId: string): Promise<UserDocument[]> {
  return this.find({ studentIds: studentId });
};

// Create the model
// Use a function to avoid model recompilation errors in development
export const getUserModel = (): UserModel => {
  return (mongoose.models.User as UserModel) || 
    mongoose.model<UserDocument, UserModel>('User', UserSchema);
};

export default getUserModel; 