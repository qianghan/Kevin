/**
 * Error Service Implementation
 * 
 * This is a concrete implementation of the IErrorService interface.
 * It provides centralized error handling functionality for the application.
 */

import { v4 as uuidv4 } from 'uuid';
import { 
  IErrorService, 
  ErrorRecord, 
  ErrorCategory, 
  ErrorContext, 
  ErrorReportOptions 
} from '../../interfaces/services/error.service';
import { AppError } from '../../models/error.model';

/**
 * Maximum number of errors to keep in memory
 */
const MAX_ERROR_HISTORY = 50;

/**
 * Error Service implementation
 */
export class ErrorService implements IErrorService {
  private errorHistory: ErrorRecord[] = [];
  private globalContext: Partial<ErrorContext> = {};
  private categoryHandlers: Map<ErrorCategory, (error: ErrorRecord) => void> = new Map();
  
  /**
   * Handle an error with standardized processing
   */
  public handleError(error: Error | string, category: ErrorCategory = 'unknown', context: Partial<ErrorContext> = {}): ErrorRecord {
    // Create error message from input
    const errorMessage = typeof error === 'string' ? error : error.message;
    
    // Get stack trace if available
    const stack = typeof error === 'object' && error.stack ? error.stack : undefined;
    
    // Get severity from AppError or default to 'medium'
    const severity = error instanceof AppError ? error.severity : 'medium';
    
    // Prepare error context by combining global and local context
    const mergedContext: ErrorContext = {
      ...this.globalContext,
      ...context,
      // Add URL if not provided
      url: context.url || (typeof window !== 'undefined' ? window.location.href : undefined),
    };
    
    // Create the error record
    const errorRecord: ErrorRecord = {
      id: uuidv4(),
      message: errorMessage,
      stack,
      timestamp: new Date().toISOString(),
      category,
      severity,
      context: mergedContext,
      isHandled: false,
      isReported: false
    };
    
    // Add to error history, keeping only the most recent errors
    this.errorHistory = [errorRecord, ...this.errorHistory.slice(0, MAX_ERROR_HISTORY - 1)];
    
    // Call category handler if one exists
    const categoryHandler = this.categoryHandlers.get(category);
    if (categoryHandler) {
      try {
        categoryHandler(errorRecord);
        errorRecord.isHandled = true;
      } catch (handlerError) {
        console.error('Error in category handler:', handlerError);
      }
    }
    
    // Log to console for development
    if (process.env.NODE_ENV !== 'production') {
      console.error(`[${category}] ${errorMessage}`, errorRecord);
    }
    
    return errorRecord;
  }
  
  /**
   * Report an error to external monitoring services
   */
  public async reportError(errorRecord: ErrorRecord, options: ErrorReportOptions = {}): Promise<void> {
    if (errorRecord.isReported && !options.silent) {
      console.warn('Error already reported:', errorRecord.id);
      return;
    }
    
    try {
      // Here you would integrate with external error reporting services like Sentry
      // For now, we'll just mark it as reported
      
      // Example of what actual reporting might look like:
      /*
      await fetch('/api/error-reporting', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error: {
            message: errorRecord.message,
            stack: options.includeStack ? errorRecord.stack : undefined,
            category: errorRecord.category,
            severity: errorRecord.severity,
            timestamp: errorRecord.timestamp,
            context: options.includeContext ? errorRecord.context : undefined
          }
        })
      });
      */
      
      // Update error record to mark as reported
      const index = this.errorHistory.findIndex(e => e.id === errorRecord.id);
      if (index >= 0) {
        this.errorHistory[index] = {
          ...errorRecord,
          isReported: true
        };
      }
    } catch (error) {
      console.error('Error reporting failed:', error);
    }
  }
  
  /**
   * Get all recorded errors
   */
  public getErrors(): ErrorRecord[] {
    return [...this.errorHistory];
  }
  
  /**
   * Clear all recorded errors
   */
  public async clearErrors(): Promise<void> {
    this.errorHistory = [];
  }
  
  /**
   * Set global error context that will be included with all errors
   */
  public setGlobalContext(context: Partial<ErrorContext>): void {
    this.globalContext = {
      ...this.globalContext,
      ...context
    };
  }
  
  /**
   * Get user-friendly message for an error
   */
  public getUserFriendlyMessage(error: Error | ErrorRecord): string {
    // If it's an AppError, use its getUserFriendlyMessage method
    if (error instanceof AppError) {
      return error.getUserFriendlyMessage();
    }
    
    // If it's an ErrorRecord, provide a friendly message based on category
    if ('category' in error) {
      switch (error.category) {
        case 'network':
          return 'A network error occurred. Please check your connection and try again.';
        case 'authentication':
          return 'Your session may have expired. Please log in again.';
        case 'validation':
          return 'Please check your input and try again.';
        case 'permission':
          return 'You don\'t have permission to perform this action.';
        case 'business':
          return error.message || 'An error occurred with your request.';
        default:
          return error.message || 'An unexpected error occurred.';
      }
    }
    
    // For standard Error objects or strings
    return error.message || 'An unexpected error occurred.';
  }
  
  /**
   * Register a custom error handler for specific error categories
   */
  public registerCategoryHandler(category: ErrorCategory, handler: (error: ErrorRecord) => void): void {
    this.categoryHandlers.set(category, handler);
  }
} 