import mongoose, { Document, Schema, Model } from 'mongoose';

/**
 * Session document interface
 */
export interface SessionDocument extends Document {
  userId: mongoose.Types.ObjectId;
  token: string;
  device?: string;
  ipAddress?: string;
  lastActive: Date;
  expiresAt: Date;
  isValid: boolean;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * User session schema for MongoDB storage
 */
const SessionSchema = new Schema<SessionDocument>(
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
      unique: true
    },
    device: {
      type: String
    },
    ipAddress: {
      type: String
    },
    lastActive: {
      type: Date,
      default: Date.now
    },
    expiresAt: {
      type: Date,
      required: true,
      index: true
    },
    isValid: {
      type: Boolean,
      default: true,
      index: true
    }
  },
  {
    timestamps: true
  }
);

// Index for finding active user sessions
SessionSchema.index({ userId: 1, isValid: 1 });

// Index for token validation
SessionSchema.index({ token: 1, isValid: 1 });

/**
 * Interface for the Session model with static methods
 */
export interface SessionModel extends Model<SessionDocument> {
  findActiveSessionsByUser(userId: string): Promise<SessionDocument[]>;
  findByToken(token: string): Promise<SessionDocument | null>;
  invalidateSession(sessionId: string): Promise<boolean>;
  invalidateUserSessions(userId: string): Promise<boolean>;
  updateLastActive(sessionId: string): Promise<boolean>;
}

// Static methods implementation
SessionSchema.statics.findActiveSessionsByUser = async function(userId: string): Promise<SessionDocument[]> {
  return this.find({
    userId,
    isValid: true,
    expiresAt: { $gt: new Date() }
  });
};

SessionSchema.statics.findByToken = async function(token: string): Promise<SessionDocument | null> {
  return this.findOne({
    token,
    isValid: true,
    expiresAt: { $gt: new Date() }
  });
};

SessionSchema.statics.invalidateSession = async function(sessionId: string): Promise<boolean> {
  const result = await this.updateOne(
    { _id: sessionId },
    { isValid: false }
  );
  return result.modifiedCount > 0;
};

SessionSchema.statics.invalidateUserSessions = async function(userId: string): Promise<boolean> {
  const result = await this.updateMany(
    { userId },
    { isValid: false }
  );
  return result.modifiedCount > 0;
};

SessionSchema.statics.updateLastActive = async function(sessionId: string): Promise<boolean> {
  const result = await this.updateOne(
    { _id: sessionId },
    { lastActive: new Date() }
  );
  return result.modifiedCount > 0;
};

// Create the model
export const getSessionModel = (): SessionModel => {
  return (mongoose.models.Session as SessionModel) ||
    mongoose.model<SessionDocument, SessionModel>('Session', SessionSchema);
};

export default getSessionModel; 