/**
 * Error Models
 * 
 * Defines standardized error structures and categorizations for the application.
 * Follows Single Responsibility Principle by focusing only on error representation.
 */

import { ErrorSeverity, ErrorCategory } from '../interfaces/services/error.service';

/**
 * Base application error class
 */
export class AppError extends Error {
  category: ErrorCategory;
  severity: ErrorSeverity;
  code: string;
  timestamp: Date;
  details?: Record<string, any>;

  constructor(message: string, options: {
    category?: ErrorCategory;
    severity?: ErrorSeverity;
    code?: string;
    details?: Record<string, any>;
    cause?: Error;
  } = {}) {
    super(message);
    
    // Set name for better debugging
    this.name = this.constructor.name;
    
    // Ensure stack trace is captured
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, this.constructor);
    }
    
    // Set error properties
    this.category = options.category || 'unknown';
    this.severity = options.severity || 'medium';
    this.code = options.code || 'ERR_UNKNOWN';
    this.timestamp = new Date();
    this.details = options.details;
    
    // Set cause if provided (for error chaining)
    if (options.cause) {
      this.cause = options.cause;
    }
  }

  /**
   * Get a user-friendly message for this error
   */
  getUserFriendlyMessage(): string {
    return this.message;
  }
}

/**
 * Network-related errors
 */
export class NetworkError extends AppError {
  constructor(message: string, options: {
    severity?: ErrorSeverity;
    code?: string;
    details?: Record<string, any>;
    cause?: Error;
  } = {}) {
    super(message, { 
      ...options, 
      category: 'network',
      code: options.code || 'ERR_NETWORK'
    });
  }

  getUserFriendlyMessage(): string {
    return 'Network connection issue. Please check your internet connection and try again.';
  }
}

/**
 * API-related errors
 */
export class ApiError extends NetworkError {
  statusCode?: number;
  
  constructor(message: string, statusCode?: number, options: {
    severity?: ErrorSeverity;
    details?: Record<string, any>;
    cause?: Error;
  } = {}) {
    super(message, { 
      ...options, 
      code: `ERR_API_${statusCode || 'UNKNOWN'}`
    });
    this.statusCode = statusCode;
  }

  getUserFriendlyMessage(): string {
    switch (this.statusCode) {
      case 401:
        return 'Your session has expired. Please log in again.';
      case 403:
        return 'You don\'t have permission to access this resource.';
      case 404:
        return 'The requested resource could not be found.';
      case 422:
        return 'The provided data is invalid. Please check your input and try again.';
      case 500:
      case 502:
      case 503:
      case 504:
        return 'The server encountered an error. Please try again later.';
      default:
        return 'An error occurred while communicating with the server. Please try again.';
    }
  }
}

/**
 * Authentication-related errors
 */
export class AuthenticationError extends AppError {
  constructor(message: string, options: {
    severity?: ErrorSeverity;
    details?: Record<string, any>;
    cause?: Error;
  } = {}) {
    super(message, { 
      ...options, 
      category: 'authentication',
      code: 'ERR_AUTH' 
    });
  }

  getUserFriendlyMessage(): string {
    return 'Authentication failed. Please check your credentials and try again.';
  }
}

/**
 * Validation errors for form inputs and data
 */
export class ValidationError extends AppError {
  fieldErrors?: Record<string, string>;
  
  constructor(message: string, fieldErrors?: Record<string, string>, options: {
    severity?: ErrorSeverity;
    details?: Record<string, any>;
    cause?: Error;
  } = {}) {
    super(message, { 
      ...options, 
      category: 'validation',
      code: 'ERR_VALIDATION' 
    });
    this.fieldErrors = fieldErrors;
  }

  getUserFriendlyMessage(): string {
    if (this.fieldErrors && Object.keys(this.fieldErrors).length > 0) {
      const fields = Object.keys(this.fieldErrors).join(', ');
      return `Please check the following field(s): ${fields}`;
    }
    return 'Please check your input and try again.';
  }
}

/**
 * Permission/authorization errors
 */
export class PermissionError extends AppError {
  requiredPermission?: string;
  
  constructor(message: string, requiredPermission?: string, options: {
    severity?: ErrorSeverity;
    details?: Record<string, any>;
    cause?: Error;
  } = {}) {
    super(message, { 
      ...options, 
      category: 'permission',
      code: 'ERR_PERMISSION' 
    });
    this.requiredPermission = requiredPermission;
  }

  getUserFriendlyMessage(): string {
    return 'You don\'t have permission to perform this action.';
  }
}

/**
 * Business logic errors
 */
export class BusinessError extends AppError {
  constructor(message: string, options: {
    severity?: ErrorSeverity;
    code?: string;
    details?: Record<string, any>;
    cause?: Error;
  } = {}) {
    super(message, { 
      ...options, 
      category: 'business',
      code: options.code || 'ERR_BUSINESS' 
    });
  }
}

/**
 * Map HTTP status codes to error classes
 */
export function createErrorFromHttpStatus(status: number, message: string, details?: Record<string, any>): AppError {
  switch (status) {
    case 400:
      return new ValidationError(message, undefined, { details });
    case 401:
    case 403:
      return new AuthenticationError(message, { details });
    case 404:
      return new ApiError(message, status, { details });
    case 500:
    case 502:
    case 503:
    case 504:
      return new ApiError(message, status, { 
        severity: 'high',
        details 
      });
    default:
      return new ApiError(message, status, { details });
  }
} 