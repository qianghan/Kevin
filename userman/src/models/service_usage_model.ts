import mongoose, { Schema } from 'mongoose';

// Create the service usage schema
const usageSchema = new Schema(
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
    endpoint: {
      // API endpoint or feature that was used
      type: String,
      required: true
    },
    requestCount: {
      // Number of API calls in this record
      type: Number,
      default: 1
    },
    dataProcessed: {
      // Amount of data processed (bytes)
      type: Number,
      default: 0
    },
    responseTime: {
      // Average response time (ms)
      type: Number,
      default: 0
    },
    status: {
      // Success, failure, etc.
      type: String,
      enum: ['SUCCESS', 'FAILURE', 'THROTTLED', 'ERROR'],
      default: 'SUCCESS'
    },
    errorDetails: {
      // Details if there was an error
      type: Schema.Types.Mixed,
      default: null
    },
    metadata: {
      // Additional data specific to the service
      type: Schema.Types.Mixed,
      default: {}
    },
    // Using date fields to allow for daily/monthly aggregation
    date: {
      type: Date,
      required: true
    },
    year: {
      type: Number,
      required: true
    },
    month: {
      type: Number,
      required: true
    },
    day: {
      type: Number,
      required: true
    }
  },
  { timestamps: true }
);

// Create indexes for efficient querying and aggregation
usageSchema.index({ userId: 1, serviceId: 1, date: 1 });
usageSchema.index({ serviceId: 1, date: 1 });
usageSchema.index({ userId: 1, date: 1 });
usageSchema.index({ year: 1, month: 1, day: 1 });

/**
 * Static method to record usage
 */
usageSchema.statics.recordUsage = async function(
  userId: string,
  serviceId: string,
  endpoint: string,
  metrics: {
    requestCount?: number,
    dataProcessed?: number,
    responseTime?: number,
    status?: string,
    errorDetails?: any,
    metadata?: any
  } = {}
) {
  const now = new Date();
  
  // Create new usage record
  return this.create({
    userId,
    serviceId,
    endpoint,
    requestCount: metrics.requestCount || 1,
    dataProcessed: metrics.dataProcessed || 0,
    responseTime: metrics.responseTime || 0,
    status: metrics.status || 'SUCCESS',
    errorDetails: metrics.errorDetails || null,
    metadata: metrics.metadata || {},
    date: now,
    year: now.getFullYear(),
    month: now.getMonth() + 1, // 1-12 instead of 0-11
    day: now.getDate()
  });
};

/**
 * Static method to get aggregated usage for a user and service
 */
usageSchema.statics.getAggregatedUsage = async function(
  userId: string,
  serviceId: string,
  startDate: Date,
  endDate: Date
) {
  return this.aggregate([
    {
      $match: {
        userId: new mongoose.Types.ObjectId(userId),
        serviceId: new mongoose.Types.ObjectId(serviceId),
        date: { $gte: startDate, $lte: endDate }
      }
    },
    {
      $group: {
        _id: null,
        totalRequests: { $sum: '$requestCount' },
        totalDataProcessed: { $sum: '$dataProcessed' },
        avgResponseTime: { $avg: '$responseTime' },
        successCount: {
          $sum: { $cond: [{ $eq: ['$status', 'SUCCESS'] }, '$requestCount', 0] }
        },
        failureCount: {
          $sum: { $cond: [{ $eq: ['$status', 'FAILURE'] }, '$requestCount', 0] }
        },
        throttledCount: {
          $sum: { $cond: [{ $eq: ['$status', 'THROTTLED'] }, '$requestCount', 0] }
        },
        errorCount: {
          $sum: { $cond: [{ $eq: ['$status', 'ERROR'] }, '$requestCount', 0] }
        }
      }
    }
  ]);
};

// Create and export the model
const UsageModel = mongoose.model('Usage', usageSchema);
export { UsageModel }; 