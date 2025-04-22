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

/**
 * Available user roles in the system
 */
export type UserRole = 'student' | 'parent' | 'admin' | 'support';

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
    lastLoginAt: {
      type: Date
    },
    failedLoginAttempts: {
      type: Number,
      default: 0
    },
    lockedUntil: {
      type: Date
    },
    role: {
      type: String,
      enum: ['student', 'parent', 'admin', 'support'],
      required: true,
      default: 'student',
    },
    testMode: {
      type: Boolean,
      default: false,
    },
    profileCompleteness: {
      score: {
        type: Number,
        default: 0
      },
      missingFields: {
        type: [String],
        default: []
      },
      lastUpdated: {
        type: Date,
        default: Date.now
      }
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
UserSchema.index({ testMode: 1 }); // Add index for testMode
UserSchema.index({ "profileCompleteness.score": 1 }); // Index for profile completeness score

/**
 * Calculate profile completeness score based on filled fields
 * @param user User document
 * @returns Profile completeness score (0-100)
 */
export const calculateProfileCompleteness = (user: UserDocument): ProfileCompleteness => {
  const requiredFields = ['name', 'email', 'image'];
  const preferenceFields = ['preferences.theme', 'preferences.language'];
  
  // Fields that should be filled based on user role
  const roleBasedFields: Record<UserRole, string[]> = {
    student: [],
    parent: ['studentIds'],
    admin: [],
    support: []
  };
  
  // All fields that should be checked for this user
  const fieldsToCheck = [...requiredFields, ...preferenceFields, ...(roleBasedFields[user.role] || [])];
  const missingFields: string[] = [];
  
  // Check each field
  fieldsToCheck.forEach(field => {
    if (field.includes('.')) {
      // Handle nested fields
      const [parent, child] = field.split('.');
      if (!user[parent] || !user[parent][child]) {
        missingFields.push(field);
      }
    } else if (!user[field] || (Array.isArray(user[field]) && user[field].length === 0)) {
      missingFields.push(field);
    }
  });
  
  // Calculate score as percentage of completed fields
  const filledFields = fieldsToCheck.length - missingFields.length;
  const score = Math.round((filledFields / fieldsToCheck.length) * 100);
  
  return {
    score,
    missingFields,
    lastUpdated: new Date()
  };
};

// Pre-save middleware to calculate profile completeness
UserSchema.pre('save', function(next) {
  // Only recalculate if relevant fields have changed
  if (this.isModified('name') || this.isModified('email') || this.isModified('image') ||
      this.isModified('preferences') || this.isModified('studentIds') || this.isModified('parentIds')) {
    this.profileCompleteness = calculateProfileCompleteness(this);
  }
  next();
});

/**
 * Interface for the User model with static methods
 */
export interface UserModel extends Model<UserDocument> {
  findByEmail(email: string): Promise<UserDocument | null>;
  findByIds(ids: string[]): Promise<UserDocument[]>;
  findStudents(parentId: string): Promise<UserDocument[]>;
  findParents(studentId: string): Promise<UserDocument[]>;
  updateLoginTimestamp(userId: string): Promise<boolean>;
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

// Update the user's last login timestamp
UserSchema.statics.updateLoginTimestamp = async function(userId: string): Promise<boolean> {
  const result = await this.updateOne(
    { _id: userId },
    { lastLoginAt: new Date() }
  );
  return result.modifiedCount > 0;
};

// Create the model
// Use a function to avoid model recompilation errors in development
export const getUserModel = (): UserModel => {
  return (mongoose.models.User as UserModel) || 
    mongoose.model<UserDocument, UserModel>('User', UserSchema);
};

export default getUserModel; 