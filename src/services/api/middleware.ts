/**
 * Data validation middleware for API requests and responses.
 * 
 * This module provides middleware functions for validating API requests and responses
 * against JSON schema definitions.
 */

import Ajv, { ValidateFunction } from 'ajv';
import addFormats from 'ajv-formats';

/**
 * Interface for schema validation options.
 */
export interface ValidationOptions {
  /** Whether to validate responses (default: true) */
  validateResponses?: boolean;
  /** Whether to throw errors on validation failure (default: true) */
  throwOnError?: boolean;
  /** Custom error message prefix */
  errorPrefix?: string;
}

/**
 * Validation error containing details about the validation failure.
 */
export class ValidationError extends Error {
  public readonly errors: any[];
  public readonly path: string;
  public readonly data: any;
  
  constructor(message: string, errors: any[], path: string, data: any) {
    super(message);
    this.name = 'ValidationError';
    this.errors = errors;
    this.path = path;
    this.data = data;
  }
}

// Create Ajv instance with proper configuration
const ajv = new Ajv({
  allErrors: true,
  removeAdditional: false, // Don't remove additional properties
  useDefaults: true,
  coerceTypes: true,
  strict: false,
});

// Add formats like 'email', 'uuid', etc.
addFormats(ajv);

/**
 * Cache of compiled schema validators.
 */
const validators = new Map<object, ValidateFunction>();

/**
 * Gets or creates a validator function for the given schema.
 */
function getValidator(schema: object): ValidateFunction {
  if (!validators.has(schema)) {
    validators.set(schema, ajv.compile(schema));
  }
  return validators.get(schema)!;
}

/**
 * Validates data against a JSON schema.
 * 
 * @param data The data to validate
 * @param schema The JSON schema to validate against
 * @param path The path to the data (for error reporting)
 * @param options Validation options
 * @returns The validated data (potentially with defaults applied)
 * @throws ValidationError if validation fails and throwOnError is true
 */
export function validateData<T>(
  data: any,
  schema: object,
  path: string,
  options: ValidationOptions = {}
): T {
  const { throwOnError = true, errorPrefix = 'Validation failed' } = options;
  
  const validate = getValidator(schema);
  const valid = validate(data);
  
  if (!valid && validate.errors && validate.errors.length > 0) {
    const errors = validate.errors;
    
    // Format a helpful error message
    const errorDetails = errors.map(err => {
      const instancePath = err.instancePath || '/';
      const message = err.message || 'Unknown validation error';
      return `${instancePath}: ${message}`;
    }).join('; ');
    
    const errorMessage = `${errorPrefix}: ${errorDetails}`;
    
    if (throwOnError) {
      throw new ValidationError(errorMessage, errors, path, data);
    }
    
    console.error(errorMessage);
  }
  
  return data as T;
}

/**
 * Validates a request body against a JSON schema.
 * 
 * @param body The request body to validate
 * @param schema The JSON schema to validate against
 * @param options Validation options
 * @returns The validated request body (potentially with defaults applied)
 * @throws ValidationError if validation fails and throwOnError is true
 */
export function validateRequest<T>(
  body: any,
  schema: object,
  options: ValidationOptions = {}
): T {
  return validateData<T>(
    body, 
    schema, 
    'request.body', 
    { errorPrefix: 'Request validation failed', ...options }
  );
}

/**
 * Validates a response body against a JSON schema.
 * 
 * @param body The response body to validate
 * @param schema The JSON schema to validate against
 * @param options Validation options
 * @returns The validated response body (potentially with defaults applied)
 * @throws ValidationError if validation fails and throwOnError is true
 */
export function validateResponse<T>(
  body: any,
  schema: object,
  options: ValidationOptions = {}
): T {
  return validateData<T>(
    body, 
    schema, 
    'response.body', 
    { errorPrefix: 'Response validation failed', ...options }
  );
}

/**
 * Creates middleware for validating requests and responses.
 * 
 * @param requestSchema Schema for validating request body
 * @param responseSchema Schema for validating response body
 * @param options Validation options
 * @returns A middleware function
 */
export function createValidationMiddleware(
  requestSchema: object,
  responseSchema?: object,
  options: ValidationOptions = {}
) {
  const { validateResponses = true, throwOnError = true } = options;
  
  return async (req: any, res: any, next: () => void) => {
    try {
      // Validate request
      if (requestSchema) {
        req.body = validateRequest(req.body, requestSchema, { throwOnError });
      }
      
      // Store original res.json to intercept response validation
      if (validateResponses && responseSchema) {
        const originalJson = res.json;
        
        res.json = function(body: any) {
          try {
            // Validate response
            body = validateResponse(body, responseSchema!, { throwOnError });
          } catch (error) {
            console.error('Response validation error:', error);
            if (throwOnError) {
              throw error;
            }
          }
          
          return originalJson.call(this, body);
        };
      }
      
      next();
    } catch (error) {
      if (error instanceof ValidationError) {
        res.status(400).json({
          code: 'validation_error',
          message: error.message,
          details: error.errors
        });
      } else {
        next(error);
      }
    }
  };
} 