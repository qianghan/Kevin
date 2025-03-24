import axios, { AxiosError, AxiosResponse } from 'axios';
import { UserPreferences as ModelUserPreferences } from '@/lib/models/User';

// Define types for user requests and responses
export interface UserProfile {
  id?: string;
  name?: string;
  email?: string;
  image?: string;
  role?: 'student' | 'parent';
  studentIds?: string[];
  parentIds?: string[];
  partnerIds?: string[];
  preferences?: UserPreferences;
  createdAt?: Date;
  updatedAt?: Date;
}

// Re-export UserPreferences for compatibility
export type UserPreferences = ModelUserPreferences;

// Error types for more detailed error handling
export class ServiceError extends Error {
  details?: any;
  
  constructor(message: string, details?: any) {
    super(message);
    this.name = 'ServiceError';
    this.details = details;
  }
}

export class DatabaseError extends ServiceError {
  constructor(message: string, details?: any) {
    super(message, details);
    this.name = 'DatabaseError';
  }
}

export class ApiRequestError extends ServiceError {
  status?: number;
  
  constructor(message: string, status?: number, details?: any) {
    super(message, details);
    this.name = 'ApiRequestError';
    this.status = status;
  }
}

export class AuthError extends ServiceError {
  constructor(message: string, details?: any) {
    super(message, details);
    this.name = 'AuthError';
  }
}

// Constants
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

// Logger helper
const logAction = (methodName: string, params: any, component = 'UserService') => {
  if (process.env.NODE_ENV === 'development') {
    console.log(`[${component}:${methodName}]`, params);
  }
};

// Error handler helper
const handleError = (error: any, methodName: string): never => {
  console.error(`[UserService:${methodName}] Error:`, error);
  
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    
    if (axiosError.response) {
      // API responded with error status
      const status = axiosError.response.status;
      const data = axiosError.response.data;
      
      if (status === 401 || status === 403) {
        throw new AuthError('Authentication failed', { status, data });
      }
      
      throw new ApiRequestError(
        `API request failed with status ${status}`,
        status,
        data
      );
    } else if (axiosError.request) {
      // No response received
      throw new ApiRequestError(
        'No response received from server',
        0,
        { request: axiosError.request }
      );
    }
  } else if (error.name === 'AuthError') {
    throw error;
  } else if (error.name === 'DatabaseError') {
    throw error;
  } else if (error.name === 'ApiRequestError') {
    throw error;
  } else if (error.name === 'ServiceError') {
    throw error;
  }
  
  // Unknown error
  throw new ServiceError(`Unknown error in ${methodName}`, { originalError: error });
};

// Generic retry mechanism
const retry = async <T>(
  operation: () => Promise<T>,
  methodName: string,
  retries = MAX_RETRIES,
  delay = RETRY_DELAY
): Promise<T> => {
  try {
    return await operation();
  } catch (error) {
    if (retries <= 0) {
      return handleError(error, methodName);
    }
    
    console.warn(`[UserService:${methodName}] Retrying... (${retries} attempts left)`);
    await new Promise(resolve => setTimeout(resolve, delay));
    return retry(operation, methodName, retries - 1, delay * 1.5);
  }
};

export class UserService {
  /**
   * Get the current user profile
   */
  async getCurrentUser(): Promise<UserProfile | null> {
    const methodName = 'getCurrentUser';
    logAction(methodName, {});
    
    try {
      const operation = async () => {
        const response = await axios.get('/api/user/profile');
        return response.data;
      };
      
      return await retry(operation, methodName);
    } catch (error) {
      if ((error as ServiceError).name === 'AuthError') {
        // Not authenticated is a valid state, return null
        return null;
      }
      return handleError(error, methodName);
    }
  }
  
  /**
   * Update user profile
   */
  async updateProfile(profile: Partial<UserProfile>): Promise<UserProfile> {
    const methodName = 'updateProfile';
    logAction(methodName, { profile });
    
    try {
      const operation = async () => {
        const response = await axios.put('/api/user/profile', profile);
        return response.data;
      };
      
      return await retry(operation, methodName);
    } catch (error) {
      return handleError(error, methodName);
    }
  }
  
  /**
   * Update user preferences
   */
  async updatePreferences(preferences: UserPreferences): Promise<UserPreferences> {
    const methodName = 'updatePreferences';
    logAction(methodName, { preferences });
    
    try {
      const operation = async () => {
        const response = await axios.put('/api/user/preferences', preferences);
        return response.data;
      };
      
      return await retry(operation, methodName);
    } catch (error) {
      return handleError(error, methodName);
    }
  }
  
  /**
   * Get user preferences
   */
  async getPreferences(): Promise<UserPreferences> {
    const methodName = 'getPreferences';
    logAction(methodName, {});
    
    try {
      const operation = async () => {
        const response = await axios.get('/api/user/preferences');
        return response.data;
      };
      
      return await retry(operation, methodName);
    } catch (error) {
      return handleError(error, methodName);
    }
  }
  
  /**
   * Link student to parent or parent to student
   */
  async linkAccounts(targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean> {
    const methodName = 'linkAccounts';
    logAction(methodName, { targetUserId, relationship });
    
    try {
      const operation = async () => {
        const response = await axios.post('/api/user/link', { 
          targetUserId, 
          relationship 
        });
        return response.data.success;
      };
      
      return await retry(operation, methodName);
    } catch (error) {
      return handleError(error, methodName);
    }
  }
  
  /**
   * Search for users (for linking accounts)
   */
  async searchUsers(query: string): Promise<UserProfile[]> {
    const methodName = 'searchUsers';
    logAction(methodName, { query });
    
    try {
      const operation = async () => {
        const response = await axios.get(`/api/user/search?q=${encodeURIComponent(query)}`);
        return response.data;
      };
      
      return await retry(operation, methodName);
    } catch (error) {
      return handleError(error, methodName);
    }
  }
  
  /**
   * Get linked users (students, parents, or partners)
   */
  async getLinkedUsers(relationship: 'students' | 'parents' | 'partners'): Promise<UserProfile[]> {
    const methodName = 'getLinkedUsers';
    logAction(methodName, { relationship });
    
    try {
      const operation = async () => {
        const response = await axios.get(`/api/user/linked/${relationship}`);
        return response.data;
      };
      
      return await retry(operation, methodName);
    } catch (error) {
      return handleError(error, methodName);
    }
  }
  
  /**
   * Remove link between users
   */
  async unlinkAccount(targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean> {
    const methodName = 'unlinkAccount';
    logAction(methodName, { targetUserId, relationship });
    
    try {
      const operation = async () => {
        const response = await axios.delete(`/api/user/link`, { 
          data: { targetUserId, relationship } 
        });
        return response.data.success;
      };
      
      return await retry(operation, methodName);
    } catch (error) {
      return handleError(error, methodName);
    }
  }
  
  /**
   * Change email
   */
  async changeEmail(newEmail: string, password: string): Promise<boolean> {
    const methodName = 'changeEmail';
    logAction(methodName, { newEmail });
    
    try {
      const operation = async () => {
        const response = await axios.put('/api/user/email', { 
          newEmail, 
          password 
        });
        return response.data.success;
      };
      
      return await retry(operation, methodName);
    } catch (error) {
      return handleError(error, methodName);
    }
  }
  
  /**
   * Change password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<boolean> {
    const methodName = 'changePassword';
    logAction(methodName, {});
    
    try {
      const operation = async () => {
        const response = await axios.put('/api/user/password', {
          currentPassword,
          newPassword
        });
        return response.data.success;
      };
      
      return await retry(operation, methodName);
    } catch (error) {
      return handleError(error, methodName);
    }
  }
}

// Export a singleton instance
export const userService = new UserService(); 