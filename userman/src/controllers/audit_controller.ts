import { Request, Response } from 'express';
import { IAuditLogService, AuditEventType } from '../services/interfaces';

/**
 * Controller for audit log API endpoints
 */
export class AuditController {
  private auditLogService: IAuditLogService;
  
  /**
   * Constructor
   */
  constructor(auditLogService: IAuditLogService) {
    this.auditLogService = auditLogService;
  }
  
  /**
   * Get audit logs with optional filtering
   */
  async getAuditLogs(req: Request, res: Response): Promise<void> {
    try {
      const { 
        eventTypes, 
        startDate, 
        endDate, 
        userId, 
        success,
        limit = 100,
        offset = 0
      } = req.query;
      
      // Parse event types from comma-separated string
      const parsedEventTypes = eventTypes 
        ? (eventTypes as string).split(',').map(type => type.trim()) as AuditEventType[] 
        : undefined;
      
      // Parse dates
      const parsedStartDate = startDate ? new Date(startDate as string) : undefined;
      const parsedEndDate = endDate ? new Date(endDate as string) : undefined;
      
      // Parse success flag
      const parsedSuccess = success !== undefined 
        ? success === 'true' 
        : undefined;
      
      // Get logs
      const logs = await this.auditLogService.getAuditLog(
        {
          eventTypes: parsedEventTypes,
          startDate: parsedStartDate,
          endDate: parsedEndDate,
          userId: userId as string,
          success: parsedSuccess
        },
        Number(limit),
        Number(offset)
      );
      
      res.status(200).json({
        success: true,
        count: logs.length,
        data: logs
      });
    } catch (error) {
      console.error('Error getting audit logs:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to retrieve audit logs',
        error: (error as Error).message
      });
    }
  }
  
  /**
   * Get audit logs for a specific user
   */
  async getUserAuditLogs(req: Request, res: Response): Promise<void> {
    try {
      const { userId } = req.params;
      const { limit = 50, offset = 0 } = req.query;
      
      if (!userId) {
        res.status(400).json({
          success: false,
          message: 'User ID is required'
        });
        return;
      }
      
      const logs = await this.auditLogService.getUserAuditLog(
        userId,
        Number(limit),
        Number(offset)
      );
      
      res.status(200).json({
        success: true,
        count: logs.length,
        data: logs
      });
    } catch (error) {
      console.error('Error getting user audit logs:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to retrieve user audit logs',
        error: (error as Error).message
      });
    }
  }
  
  /**
   * Get security events for a specific IP address
   */
  async getIPSecurityEvents(req: Request, res: Response): Promise<void> {
    try {
      const { ipAddress } = req.params;
      const { limit = 50 } = req.query;
      
      if (!ipAddress) {
        res.status(400).json({
          success: false,
          message: 'IP address is required'
        });
        return;
      }
      
      const events = await this.auditLogService.getIPSecurityEvents(
        ipAddress,
        Number(limit)
      );
      
      res.status(200).json({
        success: true,
        count: events.length,
        data: events
      });
    } catch (error) {
      console.error('Error getting IP security events:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to retrieve IP security events',
        error: (error as Error).message
      });
    }
  }
} 