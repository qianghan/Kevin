import mongoose, { Document, Schema, Model } from 'mongoose';
import crypto from 'crypto';

/**
 * Token types for different verification purposes
 */
export enum TokenType {
  EMAIL_VERIFICATION = 'email_verification',
  PASSWORD_RESET = 'password_reset',
  EMAIL_CHANGE = 'email_change'
}

/**
 * Verification token document interface
 */
export interface VerificationTokenDocument extends Document {
  userId: mongoose.Types.ObjectId;
  token: string;
  type: TokenType;
  email?: string; // For email verification or change
  expiresAt: Date;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Verification token schema for MongoDB storage
 */
const VerificationTokenSchema = new Schema<VerificationTokenDocument>(
  {
    userId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true
    },
    token: {
      type: String,
      required: true,
      unique: true,
      index: true
    },
    type: {
      type: String,
      enum: Object.values(TokenType),
      required: true
    },
    email: {
      type: String,
      lowercase: true
    },
    expiresAt: {
      type: Date,
      required: true,
      index: true
    }
  },
  {
    timestamps: true
  }
);

// Add compound index for looking up tokens by userId and type
VerificationTokenSchema.index({ userId: 1, type: 1 });

/**
 * Interface for the VerificationToken model with static methods
 */
export interface VerificationTokenModel extends Model<VerificationTokenDocument> {
  createToken(userId: string, type: TokenType, email?: string, expiresInHours?: number): Promise<VerificationTokenDocument>;
  findValidToken(token: string, type: TokenType): Promise<VerificationTokenDocument | null>;
  invalidateUserTokens(userId: string, type: TokenType): Promise<boolean>;
}

// Static methods implementation
VerificationTokenSchema.statics.createToken = async function(
  userId: string,
  type: TokenType,
  email?: string,
  expiresInHours: number = 24
): Promise<VerificationTokenDocument> {
  // Generate a random token
  const token = crypto.randomBytes(32).toString('hex');
  
  // Calculate expiration date
  const expiresAt = new Date();
  expiresAt.setHours(expiresAt.getHours() + expiresInHours);
  
  // Invalidate any existing tokens of the same type for this user
  await this.deleteMany({
    userId,
    type
  });
  
  // Create and return the new token
  return await this.create({
    userId,
    token,
    type,
    email,
    expiresAt
  });
};

VerificationTokenSchema.statics.findValidToken = async function(
  token: string,
  type: TokenType
): Promise<VerificationTokenDocument | null> {
  return this.findOne({
    token,
    type,
    expiresAt: { $gt: new Date() }
  });
};

VerificationTokenSchema.statics.invalidateUserTokens = async function(
  userId: string,
  type: TokenType
): Promise<boolean> {
  const result = await this.deleteMany({
    userId,
    type
  });
  return result.deletedCount > 0;
};

// Create the model
export const getVerificationTokenModel = (): VerificationTokenModel => {
  return (mongoose.models.VerificationToken as VerificationTokenModel) ||
    mongoose.model<VerificationTokenDocument, VerificationTokenModel>('VerificationToken', VerificationTokenSchema);
};

export default getVerificationTokenModel; 