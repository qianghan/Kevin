/**
 * API error handling strategies with retry mechanisms.
 * 
 * This module provides utilities for handling API errors and implementing
 * retry strategies for failed API calls.
 */

import { ErrorCode, ErrorResponse } from '../../models/api_models';

/**
 * Categorizes API errors to help with handling strategies.
 */
export enum ErrorCategory {
  /** Network-related errors like timeout or no connection */
  NETWORK = 'network',
  /** Authentication errors (401, 403) */
  AUTH = 'auth',
  /** Validation errors (400) */
  VALIDATION = 'validation',
  /** Resource not found (404) */
  NOT_FOUND = 'not_found',
  /** Server errors (500) */
  SERVER = 'server',
  /** Rate limiting or throttling */
  RATE_LIMIT = 'rate_limit',
  /** Unknown errors */
  UNKNOWN = 'unknown'
}

/**
 * Configuration for retry strategies.
 */
export interface RetryConfig {
  /** Maximum number of retry attempts */
  maxRetries: number;
  /** Base delay in milliseconds between retries (will be multiplied for backoff) */
  baseDelay: number;
  /** Maximum delay in milliseconds between retries */
  maxDelay: number;
  /** Whether to use exponential backoff (true) or linear retry (false) */
  useExponentialBackoff: boolean;
  /** Error categories that should not be retried */
  noRetryCategories: ErrorCategory[];
}

/**
 * Default retry configuration.
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 300,
  maxDelay: 5000,
  useExponentialBackoff: true,
  noRetryCategories: [
    ErrorCategory.AUTH,
    ErrorCategory.VALIDATION,
    ErrorCategory.NOT_FOUND
  ]
};

/**
 * Context for API error handling.
 */
export interface ApiErrorContext {
  /** Error that occurred */
  error: Error;
  /** Request URL */
  url?: string;
  /** HTTP method */
  method?: string;
  /** Request data */
  data?: any;
  /** HTTP status code if available */
  status?: number;
  /** Error response body if available */
  errorResponse?: ErrorResponse;
  /** Current retry attempt number (0-based) */
  retryAttempt?: number;
}

/**
 * Determines the error category from an API error.
 * 
 * @param error The error or error context to categorize
 * @returns The error category
 */
export function categorizeError(error: Error | ApiErrorContext): ErrorCategory {
  const context: ApiErrorContext = 'error' in error ? error : { error };
  const { status, errorResponse } = context;
  const actualError = context.error;
  
  // Check for network errors
  if (actualError.name === 'NetworkError' || actualError.message.includes('network') || 
      actualError.message.includes('timeout') || actualError.message.includes('connection')) {
    return ErrorCategory.NETWORK;
  }
  
  // Categorize based on HTTP status if available
  if (status) {
    if (status === 401 || status === 403) {
      return ErrorCategory.AUTH;
    }
    
    if (status === 400) {
      return ErrorCategory.VALIDATION;
    }
    
    if (status === 404) {
      return ErrorCategory.NOT_FOUND;
    }
    
    if (status === 429) {
      return ErrorCategory.RATE_LIMIT;
    }
    
    if (status >= 500) {
      return ErrorCategory.SERVER;
    }
  }
  
  // Check error response code if available
  if (errorResponse) {
    switch (errorResponse.code) {
      case 'unauthorized':
      case 'forbidden':
        return ErrorCategory.AUTH;
      case 'validation_error':
        return ErrorCategory.VALIDATION;
      case 'not_found':
        return ErrorCategory.NOT_FOUND;
      case 'service_unavailable':
      case 'internal_server_error':
        return ErrorCategory.SERVER;
    }
  }
  
  return ErrorCategory.UNKNOWN;
}

/**
 * Calculates the retry delay based on the retry configuration and current attempt.
 * 
 * @param retryAttempt Current retry attempt (0-based)
 * @param config Retry configuration
 * @returns Delay in milliseconds before the next retry
 */
export function calculateRetryDelay(retryAttempt: number, config: RetryConfig = DEFAULT_RETRY_CONFIG): number {
  const { baseDelay, maxDelay, useExponentialBackoff } = config;
  
  let delay: number;
  
  if (useExponentialBackoff) {
    // Exponential backoff: baseDelay * 2^attempt with some jitter
    const exponentialDelay = baseDelay * Math.pow(2, retryAttempt);
    const jitter = exponentialDelay * 0.2 * Math.random(); // Add up to 20% jitter
    delay = exponentialDelay + jitter;
  } else {
    // Linear backoff: baseDelay * attempt with some jitter
    delay = baseDelay * (retryAttempt + 1);
    const jitter = baseDelay * 0.2 * Math.random(); // Add up to 20% jitter
    delay += jitter;
  }
  
  // Cap at maxDelay
  return Math.min(delay, maxDelay);
}

/**
 * Determines if a retry should be attempted based on the error and configuration.
 * 
 * @param context Error context
 * @param config Retry configuration
 * @returns Whether to retry the request
 */
export function shouldRetry(
  context: ApiErrorContext,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): boolean {
  const { retryAttempt = 0 } = context;
  
  // Don't retry if we've reached the max attempts
  if (retryAttempt >= config.maxRetries) {
    return false;
  }
  
  // Categorize the error
  const category = categorizeError(context);
  
  // Don't retry if the error category is in the noRetry list
  if (config.noRetryCategories.includes(category)) {
    return false;
  }
  
  return true;
}

/**
 * Enhances a fetch function with retry capabilities.
 * 
 * @param fetchFn The original fetch function to enhance
 * @param config Retry configuration
 * @returns A new fetch function with retry logic
 */
export function withRetry<T>(
  fetchFn: (...args: any[]) => Promise<T>,
  config: RetryConfig = DEFAULT_RETRY_CONFIG
): (...args: any[]) => Promise<T> {
  return async function retryableFetch(...args: any[]): Promise<T> {
    let lastError: Error;
    
    for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
      try {
        // Attempt the fetch
        return await fetchFn(...args);
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        // Create error context
        const context: ApiErrorContext = {
          error: lastError,
          retryAttempt: attempt,
          // Add other context if available in args
          url: typeof args[0] === 'string' ? args[0] : undefined,
          method: args[1]?.method,
          data: args[1]?.body,
        };
        
        // Check if we should retry
        if (shouldRetry(context, config)) {
          // Calculate delay and wait
          const delay = calculateRetryDelay(attempt, config);
          await new Promise(resolve => setTimeout(resolve, delay));
          // Continue to next attempt
          continue;
        }
        
        // No more retries, throw the error
        throw lastError;
      }
    }
    
    // This should never be reached due to the throw in the catch block,
    // but TypeScript needs it for type safety
    throw lastError!;
  };
}

/**
 * Creates a fetch API wrapper that includes error handling and retry logic.
 * 
 * @param baseUrl Base URL for API requests
 * @param retryConfig Retry configuration
 * @returns Enhanced fetch function
 */
export function createApiClient(
  baseUrl: string,
  retryConfig: RetryConfig = DEFAULT_RETRY_CONFIG
) {
  /**
   * Makes an API request with error handling and retry capabilities.
   */
  async function apiFetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint}`;
    
    // Apply default headers
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.headers,
    };
    
    try {
      // Make the request
      const response = await fetch(url, {
        ...options,
        headers,
      });
      
      // Parse the response body
      let data: any;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }
      
      // Check if response is OK
      if (!response.ok) {
        const errorResponse = typeof data === 'object' ? data : { message: data };
        throw createApiError(errorResponse, response.status, url, options.method as string);
      }
      
      return data as T;
    } catch (error) {
      const apiError = error instanceof ApiError
        ? error
        : createApiError({ message: error instanceof Error ? error.message : String(error) }, undefined, url, options.method as string);
      
      // Re-throw the enhanced error
      throw apiError;
    }
  }
  
  // Return the fetch function with retry capabilities
  return withRetry(apiFetch, retryConfig);
}

/**
 * API-specific error class with additional context.
 */
export class ApiError extends Error {
  public readonly status?: number;
  public readonly url?: string;
  public readonly method?: string;
  public readonly category: ErrorCategory;
  public readonly errorResponse?: ErrorResponse;
  
  constructor(
    message: string,
    status?: number,
    url?: string,
    method?: string,
    errorResponse?: ErrorResponse
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.url = url;
    this.method = method;
    this.errorResponse = errorResponse;
    this.category = categorizeError({
      error: this,
      status,
      errorResponse,
      url,
      method
    });
  }
}

/**
 * Creates an API error from a response.
 */
function createApiError(
  data: any,
  status?: number,
  url?: string,
  method?: string
): ApiError {
  const errorResponse = data as ErrorResponse;
  const message = errorResponse.message || 'Unknown API error';
  
  return new ApiError(message, status, url, method, errorResponse);
}

/**
 * Default implementation of an API client with error handling and retries.
 */
export const apiClient = createApiClient(
  typeof window !== 'undefined' ? (window as any).__NEXT_DATA__?.runtimeConfig?.API_URL || '/api' : '/api',
  DEFAULT_RETRY_CONFIG
); 