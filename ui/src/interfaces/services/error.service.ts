/**
 * Error Service Interface
 * 
 * Defines the contract for error handling operations.
 * This follows the Interface Segregation Principle by including
 * only methods related to error handling.
 */

export type ErrorSeverity = 'low' | 'medium' | 'high' | 'critical';

export type ErrorCategory = 
  | 'network'       // Connection issues, API failures
  | 'authentication' // Auth errors, token issues
  | 'validation'    // Input validation errors
  | 'business'      // Business logic errors
  | 'permission'    // Authorization errors
  | 'unknown';      // Uncategorized errors

export interface ErrorContext {
  userId?: string;
  sessionId?: string;
  url?: string;
  action?: string;
  component?: string;
  additionalData?: Record<string, any>;
}

export interface ErrorRecord {
  id: string;
  message: string;
  stack?: string;
  timestamp: string;
  category: ErrorCategory;
  severity: ErrorSeverity;
  context: ErrorContext;
  isHandled: boolean;
  isReported: boolean;
}

export interface ErrorReportOptions {
  includeContext?: boolean;
  includeStack?: boolean;
  silent?: boolean;
}

export interface IErrorService {
  /**
   * Handle an error with standardized processing
   * @param error Error object or message
   * @param category Error category
   * @param context Additional context data
   * @returns Error record created
   */
  handleError(error: Error | string, category?: ErrorCategory, context?: Partial<ErrorContext>): ErrorRecord;
  
  /**
   * Report an error to external monitoring services
   * @param errorRecord Error record to report
   * @param options Reporting options
   * @returns Promise resolving when reporting is complete
   */
  reportError(errorRecord: ErrorRecord, options?: ErrorReportOptions): Promise<void>;
  
  /**
   * Get all recorded errors
   * @returns Array of error records
   */
  getErrors(): ErrorRecord[];
  
  /**
   * Clear all recorded errors
   * @returns Promise resolving when errors are cleared
   */
  clearErrors(): Promise<void>;
  
  /**
   * Set global error context that will be included with all errors
   * @param context Error context to set globally
   */
  setGlobalContext(context: Partial<ErrorContext>): void;
  
  /**
   * Get user-friendly message for an error
   * @param error Error object or error record
   * @returns User-friendly error message
   */
  getUserFriendlyMessage(error: Error | ErrorRecord): string;
  
  /**
   * Register a custom error handler for specific error categories
   * @param category Error category to handle
   * @param handler Custom handler function
   */
  registerCategoryHandler(category: ErrorCategory, handler: (error: ErrorRecord) => void): void;
} 