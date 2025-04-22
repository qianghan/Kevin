import { IAuditLogService, AuditEventType, AuditLogEntryDTO } from './interfaces';
import { AuditLogModel, AuditLogDocument } from '../models/audit_log_model';
import mongoose from 'mongoose';

/**
 * Configuration for audit log service
 */
export interface AuditLogServiceConfig {
  enableConsoleLogging?: boolean;
  logLevel?: 'debug' | 'info' | 'warn' | 'error';
  maxRetention?: number; // days to retain logs
}

/**
 * Default configuration
 */
const DEFAULT_CONFIG: AuditLogServiceConfig = {
  enableConsoleLogging: true,
  logLevel: 'info',
  maxRetention: 90 // 90 days default retention
};

/**
 * Implementation of the audit log service
 */
export class AuditLogService implements IAuditLogService {
  private config: AuditLogServiceConfig;
  
  /**
   * Constructor with optional configuration
   */
  constructor(config: Partial<AuditLogServiceConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    
    // Set up auto-cleanup if retention is enabled
    if (this.config.maxRetention && this.config.maxRetention > 0) {
      this.setupRetentionCleanup();
    }
  }
  
  /**
   * Log an audit event
   */
  async logEvent(
    eventType: AuditEventType,
    userId?: string,
    success: boolean = true,
    metadata?: {
      targetUserId?: string;
      ipAddress?: string;
      userAgent?: string;
      details?: Record<string, any>;
    }
  ): Promise<void> {
    try {
      // Create the audit log entry
      const logEntry = {
        timestamp: new Date(),
        userId: userId ? new mongoose.Types.ObjectId(userId) : undefined,
        targetUserId: metadata?.targetUserId ? new mongoose.Types.ObjectId(metadata.targetUserId) : undefined,
        eventType,
        ipAddress: metadata?.ipAddress,
        userAgent: metadata?.userAgent,
        details: metadata?.details,
        success
      };
      
      // Save to database
      await AuditLogModel.create(logEntry);
      
      // Optionally log to console
      if (this.config.enableConsoleLogging) {
        this.logToConsole(eventType, userId, success, metadata);
      }
    } catch (error) {
      console.error('Error saving audit log:', error);
      // Still log to console if database logging fails
      if (this.config.enableConsoleLogging) {
        this.logToConsole(eventType, userId, success, metadata);
      }
    }
  }
  
  /**
   * Get audit log entries for a specific user
   */
  async getUserAuditLog(userId: string, limit: number = 50, offset: number = 0): Promise<AuditLogEntryDTO[]> {
    try {
      const entries = await AuditLogModel
        .find({ userId: new mongoose.Types.ObjectId(userId) })
        .sort({ timestamp: -1 })
        .skip(offset)
        .limit(limit);
      
      return entries.map(entry => this.mapToDTO(entry));
    } catch (error) {
      console.error('Error retrieving user audit log:', error);
      return [];
    }
  }
  
  /**
   * Get all audit log entries
   */
  async getAuditLog(
    filter?: {
      eventTypes?: AuditEventType[];
      startDate?: Date;
      endDate?: Date;
      userId?: string;
      success?: boolean;
    },
    limit: number = 100,
    offset: number = 0
  ): Promise<AuditLogEntryDTO[]> {
    try {
      // Build query based on filter
      const query: any = {};
      
      if (filter) {
        if (filter.eventTypes && filter.eventTypes.length > 0) {
          query.eventType = { $in: filter.eventTypes };
        }
        
        if (filter.startDate || filter.endDate) {
          query.timestamp = {};
          if (filter.startDate) {
            query.timestamp.$gte = filter.startDate;
          }
          if (filter.endDate) {
            query.timestamp.$lte = filter.endDate;
          }
        }
        
        if (filter.userId) {
          query.userId = new mongoose.Types.ObjectId(filter.userId);
        }
        
        if (filter.success !== undefined) {
          query.success = filter.success;
        }
      }
      
      const entries = await AuditLogModel
        .find(query)
        .sort({ timestamp: -1 })
        .skip(offset)
        .limit(limit);
      
      return entries.map(entry => this.mapToDTO(entry));
    } catch (error) {
      console.error('Error retrieving audit log:', error);
      return [];
    }
  }
  
  /**
   * Get security events for a specific IP address
   */
  async getIPSecurityEvents(ipAddress: string, limit: number = 50): Promise<AuditLogEntryDTO[]> {
    try {
      const entries = await AuditLogModel
        .find({ ipAddress })
        .sort({ timestamp: -1 })
        .limit(limit);
      
      return entries.map(entry => this.mapToDTO(entry));
    } catch (error) {
      console.error('Error retrieving IP security events:', error);
      return [];
    }
  }
  
  /**
   * Set up automatic cleanup of old audit logs based on retention policy
   */
  private setupRetentionCleanup(): void {
    // Run cleanup daily at midnight
    const runCleanup = async () => {
      try {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - this.config.maxRetention!);
        
        const result = await AuditLogModel.deleteMany({
          timestamp: { $lt: cutoffDate }
        });
        
        console.log(`Audit log cleanup: Removed ${result.deletedCount} entries older than ${this.config.maxRetention} days`);
      } catch (error) {
        console.error('Error during audit log cleanup:', error);
      }
    };
    
    // Calculate time until midnight
    const now = new Date();
    const midnight = new Date(now);
    midnight.setHours(24, 0, 0, 0);
    const timeUntilMidnight = midnight.getTime() - now.getTime();
    
    // Schedule first run at midnight
    setTimeout(() => {
      runCleanup();
      // Then run every 24 hours
      setInterval(runCleanup, 24 * 60 * 60 * 1000);
    }, timeUntilMidnight);
  }
  
  /**
   * Log event to console for debugging or as backup if DB logging fails
   */
  private logToConsole(
    eventType: AuditEventType,
    userId?: string,
    success: boolean = true,
    metadata?: {
      targetUserId?: string;
      ipAddress?: string;
      userAgent?: string;
      details?: Record<string, any>;
    }
  ): void {
    const logLevel = success ? 'info' : 'warn';
    if (this.shouldLog(logLevel)) {
      const timestamp = new Date().toISOString();
      const userInfo = userId ? `User: ${userId}` : 'Anonymous';
      const targetInfo = metadata?.targetUserId ? `, Target: ${metadata.targetUserId}` : '';
      const ipInfo = metadata?.ipAddress ? `, IP: ${metadata.ipAddress}` : '';
      const statusInfo = success ? 'SUCCESS' : 'FAILURE';
      
      console[logLevel](`AUDIT [${timestamp}] ${statusInfo} ${eventType} | ${userInfo}${targetInfo}${ipInfo}${metadata?.details ? ' | ' + JSON.stringify(metadata.details) : ''}`);
    }
  }
  
  /**
   * Check if a log level should be displayed based on current config
   */
  private shouldLog(level: string): boolean {
    const logLevels = {
      'debug': 0,
      'info': 1,
      'warn': 2,
      'error': 3
    };
    
    return logLevels[level as keyof typeof logLevels] >= logLevels[this.config.logLevel as keyof typeof logLevels];
  }
  
  /**
   * Map a database document to a DTO
   */
  private mapToDTO(document: AuditLogDocument): AuditLogEntryDTO {
    return {
      id: document._id.toString(),
      timestamp: document.timestamp,
      userId: document.userId?.toString(),
      targetUserId: document.targetUserId?.toString(),
      eventType: document.eventType,
      ipAddress: document.ipAddress,
      userAgent: document.userAgent,
      details: document.details,
      success: document.success
    };
  }
} 