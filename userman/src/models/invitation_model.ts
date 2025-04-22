import mongoose, { Document, Schema } from 'mongoose';

/**
 * Available relationship types for invitations
 */
export enum RelationshipType {
  PARENT_STUDENT = 'parent_student',
  STUDENT_PARENT = 'student_parent',
  PARTNER = 'partner'
}

/**
 * Invitation status types
 */
export enum InvitationStatus {
  PENDING = 'pending',
  ACCEPTED = 'accepted',
  REJECTED = 'rejected',
  EXPIRED = 'expired',
  CANCELLED = 'cancelled'
}

/**
 * Invitation document interface
 */
export interface InvitationDocument extends Document {
  email: string;
  inviterId: mongoose.Types.ObjectId;
  relationship: RelationshipType;
  status: InvitationStatus;
  token: string;
  message?: string;
  expiresAt: Date;
  acceptedById?: mongoose.Types.ObjectId;
  acceptedAt?: Date;
  rejectedAt?: Date;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Invitation schema
 */
const InvitationSchema = new Schema<InvitationDocument>(
  {
    email: {
      type: String,
      required: true,
      trim: true,
      lowercase: true,
      index: true
    },
    inviterId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true
    },
    relationship: {
      type: String,
      enum: Object.values(RelationshipType),
      required: true
    },
    status: {
      type: String,
      enum: Object.values(InvitationStatus),
      default: InvitationStatus.PENDING,
      index: true
    },
    token: {
      type: String,
      required: true,
      unique: true
    },
    message: {
      type: String
    },
    expiresAt: {
      type: Date,
      required: true,
      index: true
    },
    acceptedById: {
      type: Schema.Types.ObjectId,
      ref: 'User'
    },
    acceptedAt: {
      type: Date
    },
    rejectedAt: {
      type: Date
    }
  },
  {
    timestamps: true
  }
);

// Create indexes
InvitationSchema.index({ email: 1, status: 1 });
InvitationSchema.index({ inviterId: 1, status: 1 });
InvitationSchema.index({ expiresAt: 1, status: 1 });

// Create model
export const InvitationModel = mongoose.models.Invitation || 
  mongoose.model<InvitationDocument>('Invitation', InvitationSchema); 