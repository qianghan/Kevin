import mongoose, { Document, Schema } from 'mongoose';
import { AuditEventType } from '../services/interfaces';

/**
 * Audit log document interface
 */
export interface AuditLogDocument extends Document {
  timestamp: Date;
  userId?: mongoose.Types.ObjectId;
  targetUserId?: mongoose.Types.ObjectId;
  eventType: AuditEventType;
  ipAddress?: string;
  userAgent?: string;
  details?: Record<string, any>;
  success: boolean;
}

/**
 * Audit log schema
 */
const AuditLogSchema = new Schema<AuditLogDocument>(
  {
    timestamp: {
      type: Date,
      default: Date.now,
      index: true
    },
    userId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      index: true
    },
    targetUserId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      index: true
    },
    eventType: {
      type: String,
      required: true,
      enum: Object.values(AuditEventType),
      index: true
    },
    ipAddress: {
      type: String,
      index: true
    },
    userAgent: {
      type: String
    },
    details: {
      type: Schema.Types.Mixed
    },
    success: {
      type: Boolean,
      required: true,
      default: true,
      index: true
    }
  },
  {
    timestamps: false // We're using our own timestamp field
  }
);

// Create combined indexes for common query patterns
AuditLogSchema.index({ userId: 1, eventType: 1, timestamp: -1 });
AuditLogSchema.index({ eventType: 1, timestamp: -1 });
AuditLogSchema.index({ ipAddress: 1, timestamp: -1 });
AuditLogSchema.index({ success: 1, eventType: 1, timestamp: -1 });

// Create the model
export const AuditLogModel = mongoose.models.AuditLog ||
  mongoose.model<AuditLogDocument>('AuditLog', AuditLogSchema); 