import { backendApiService } from '@/lib/services/BackendApiService';

// Re-export the user interface types for compatibility
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

export interface UserPreferences {
  theme?: 'light' | 'dark' | 'system';
  emailNotifications?: boolean;
  language?: string;
}

// Custom error types
export class ApiError extends Error {
  status?: number;
  data?: any;
  
  constructor(message: string, status?: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export class NetworkError extends ApiError {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

export class AuthorizationError extends ApiError {
  constructor(message: string, status?: number, data?: any) {
    super(message, status, data);
    this.name = 'AuthorizationError';
  }
}

// Helper for logging
const logRequest = (methodName: string, params: any) => {
  if (process.env.NODE_ENV !== 'production') {
    console.log(`[ApiUserService:${methodName}]`, params);
  }
};

/**
 * API-based implementation of user service
 */
export class ApiUserService {
  /**
   * Get the current user profile
   */
  async getCurrentUser(): Promise<UserProfile | null> {
    logRequest('getCurrentUser', {});
    
    try {
      const response = await backendApiService.get('/api/users/profile');
      return response.data;
    } catch (error: any) {
      if (error.status === 401) {
        return null;
      }
      throw this.processError('getCurrentUser', error);
    }
  }
  
  /**
   * Update user profile
   */
  async updateProfile(profile: Partial<UserProfile>): Promise<UserProfile> {
    logRequest('updateProfile', profile);
    
    try {
      const response = await backendApiService.put('/api/users/profile', profile);
      return response.data;
    } catch (error: any) {
      throw this.processError('updateProfile', error);
    }
  }
  
  /**
   * Update user preferences
   */
  async updatePreferences(preferences: UserPreferences): Promise<UserPreferences> {
    logRequest('updatePreferences', preferences);
    
    try {
      const response = await backendApiService.put('/api/users/preferences', preferences);
      return response.data;
    } catch (error: any) {
      throw this.processError('updatePreferences', error);
    }
  }
  
  /**
   * Get user preferences
   */
  async getPreferences(): Promise<UserPreferences> {
    logRequest('getPreferences', {});
    
    try {
      const response = await backendApiService.get('/api/users/preferences');
      return response.data;
    } catch (error: any) {
      throw this.processError('getPreferences', error);
    }
  }
  
  /**
   * Link student to parent or parent to student
   */
  async linkAccounts(targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean> {
    logRequest('linkAccounts', { targetUserId, relationship });
    
    try {
      const response = await backendApiService.post('/api/users/link', { 
        targetUserId, 
        relationship 
      });
      return response.data.success;
    } catch (error: any) {
      throw this.processError('linkAccounts', error);
    }
  }
  
  /**
   * Search for users (for linking accounts)
   */
  async searchUsers(query: string): Promise<UserProfile[]> {
    logRequest('searchUsers', { query });
    
    try {
      const response = await backendApiService.get(`/api/users/search?q=${encodeURIComponent(query)}`);
      return response.data;
    } catch (error: any) {
      throw this.processError('searchUsers', error);
    }
  }
  
  /**
   * Get linked users (students, parents, or partners)
   */
  async getLinkedUsers(relationship: 'students' | 'parents' | 'partners'): Promise<UserProfile[]> {
    logRequest('getLinkedUsers', { relationship });
    
    try {
      const response = await backendApiService.get(`/api/users/linked/${relationship}`);
      return response.data;
    } catch (error: any) {
      throw this.processError('getLinkedUsers', error);
    }
  }
  
  /**
   * Process and standardize errors
   */
  private processError(methodName: string, error: any): ApiError {
    console.error(`[ApiUserService:${methodName}] Error:`, error);
    
    if (error?.response) {
      // API error with response
      const status = error.response.status;
      const data = error.response.data;
      
      if (status === 401 || status === 403) {
        return new AuthorizationError(
          data?.message || 'Authorization error',
          status,
          data
        );
      }
      
      return new ApiError(
        data?.message || `API error: ${status}`,
        status,
        data
      );
    } else if (error?.request) {
      // Network error
      return new NetworkError('Network error: No response from server');
    }
    
    // Unknown error
    return new ApiError(error?.message || 'Unknown error', undefined, error);
  }
}

// Export a singleton instance
export const apiUserService = new ApiUserService(); 