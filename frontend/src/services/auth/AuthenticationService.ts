/**
 * Authentication Service
 * 
 * This service provides a shared authentication mechanism for API access across
 * the frontend and /ui applications. It handles authentication, token management,
 * and user sessions.
 */

import { logError, logInfo } from '../logging/logger';

/**
 * Authentication token structure
 */
export interface AuthToken {
  token: string;
  expiresAt: number; // Timestamp in milliseconds
  tokenType: string;
}

/**
 * User structure
 */
export interface User {
  id: string;
  username: string;
  email: string;
  displayName?: string;
  avatarUrl?: string;
  roles?: string[];
  permissions?: string[];
}

/**
 * Authentication service interface
 */
export interface IAuthenticationService {
  /**
   * Get the current user
   */
  getCurrentUser(): Promise<User | null>;
  
  /**
   * Get the current authentication token
   */
  getAuthToken(): Promise<AuthToken | null>;
  
  /**
   * Check if the user is authenticated
   */
  isAuthenticated(): Promise<boolean>;
  
  /**
   * Log in with username and password
   */
  login(username: string, password: string): Promise<User>;
  
  /**
   * Log out the current user
   */
  logout(): Promise<void>;
  
  /**
   * Refresh the authentication token
   */
  refreshToken(): Promise<AuthToken>;
  
  /**
   * Check if the user has a specific permission
   */
  hasPermission(permission: string): Promise<boolean>;
  
  /**
   * Check if the user has a specific role
   */
  hasRole(role: string): Promise<boolean>;
  
  /**
   * Get an authentication header for API requests
   */
  getAuthHeader(): Promise<Record<string, string>>;
}

/**
 * Authentication service implementation
 */
export class AuthenticationService implements IAuthenticationService {
  private currentUser: User | null = null;
  private authToken: AuthToken | null = null;
  private authEndpoint: string;
  private tokenRefreshPromise: Promise<AuthToken> | null = null;
  private tokenRefreshThreshold: number = 5 * 60 * 1000; // 5 minutes in milliseconds
  
  /**
   * Create a new AuthenticationService
   */
  constructor(authEndpoint: string = '/api/auth') {
    this.authEndpoint = authEndpoint;
    this.loadStateFromStorage();
  }
  
  /**
   * Load authentication state from storage
   */
  private loadStateFromStorage(): void {
    try {
      // Load user
      const userJson = localStorage.getItem('auth_user');
      if (userJson) {
        this.currentUser = JSON.parse(userJson);
      }
      
      // Load token
      const tokenJson = localStorage.getItem('auth_token');
      if (tokenJson) {
        this.authToken = JSON.parse(tokenJson);
      }
    } catch (error) {
      logError('Failed to load authentication state from storage', error);
      // Clear potentially corrupted state
      this.clearState();
    }
  }
  
  /**
   * Save authentication state to storage
   */
  private saveStateToStorage(): void {
    try {
      if (this.currentUser) {
        localStorage.setItem('auth_user', JSON.stringify(this.currentUser));
      } else {
        localStorage.removeItem('auth_user');
      }
      
      if (this.authToken) {
        localStorage.setItem('auth_token', JSON.stringify(this.authToken));
      } else {
        localStorage.removeItem('auth_token');
      }
    } catch (error) {
      logError('Failed to save authentication state to storage', error);
    }
  }
  
  /**
   * Clear authentication state
   */
  private clearState(): void {
    this.currentUser = null;
    this.authToken = null;
    localStorage.removeItem('auth_user');
    localStorage.removeItem('auth_token');
  }
  
  /**
   * Check if a token is expired or close to expiry
   */
  private isTokenExpiredOrCloseToExpiry(token: AuthToken): boolean {
    const now = Date.now();
    return token.expiresAt - now < this.tokenRefreshThreshold;
  }
  
  /**
   * Get the current user
   */
  async getCurrentUser(): Promise<User | null> {
    // If we have a token but no user, try to fetch the user
    if (this.authToken && !this.currentUser) {
      try {
        // Fetch user profile from API
        const response = await fetch(`${this.authEndpoint}/profile`, {
          headers: await this.getAuthHeader()
        });
        
        if (response.ok) {
          this.currentUser = await response.json();
          this.saveStateToStorage();
        }
      } catch (error) {
        logError('Failed to fetch user profile', error);
      }
    }
    
    return this.currentUser;
  }
  
  /**
   * Get the current authentication token
   */
  async getAuthToken(): Promise<AuthToken | null> {
    // If token exists but is close to expiry, refresh it
    if (this.authToken && this.isTokenExpiredOrCloseToExpiry(this.authToken)) {
      try {
        await this.refreshToken();
      } catch (error) {
        // If refresh fails, return the current token anyway
        logError('Failed to refresh token', error);
      }
    }
    
    return this.authToken;
  }
  
  /**
   * Check if the user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    // If we have a token, check if it's valid
    if (this.authToken) {
      // If token is expired, it's not valid
      if (this.authToken.expiresAt < Date.now()) {
        try {
          // Try to refresh the token
          await this.refreshToken();
          return true;
        } catch (error) {
          // If refresh fails, user is not authenticated
          this.clearState();
          return false;
        }
      }
      
      // Token is valid
      return true;
    }
    
    // No token, not authenticated
    return false;
  }
  
  /**
   * Log in with username and password
   */
  async login(username: string, password: string): Promise<User> {
    try {
      const response = await fetch(`${this.authEndpoint}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });
      
      if (!response.ok) {
        throw new Error(`Login failed: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Save the token
      this.authToken = {
        token: data.token,
        expiresAt: Date.now() + (data.expiresIn * 1000),
        tokenType: data.tokenType || 'Bearer'
      };
      
      // Save the user
      this.currentUser = data.user;
      
      // Save to storage
      this.saveStateToStorage();
      
      logInfo(`User ${username} logged in successfully`);
      
      if (!this.currentUser) {
        throw new Error('Login succeeded but user data is missing');
      }
      
      return this.currentUser;
    } catch (error) {
      logError(`Login failed for user ${username}`, error);
      throw error;
    }
  }
  
  /**
   * Log out the current user
   */
  async logout(): Promise<void> {
    if (this.authToken) {
      try {
        // Call logout endpoint
        await fetch(`${this.authEndpoint}/logout`, {
          method: 'POST',
          headers: await this.getAuthHeader()
        });
      } catch (error) {
        logError('Logout request failed', error);
        // Continue with local logout even if the request fails
      }
    }
    
    // Clear local state
    this.clearState();
    logInfo('User logged out');
  }
  
  /**
   * Refresh the authentication token
   */
  async refreshToken(): Promise<AuthToken> {
    // If a refresh is already in progress, return that promise
    if (this.tokenRefreshPromise) {
      return this.tokenRefreshPromise;
    }
    
    // Start a new refresh
    this.tokenRefreshPromise = (async () => {
      try {
        if (!this.authToken) {
          throw new Error('No token to refresh');
        }
        
        const response = await fetch(`${this.authEndpoint}/refresh`, {
          method: 'POST',
          headers: {
            'Authorization': `${this.authToken.tokenType} ${this.authToken.token}`
          }
        });
        
        if (!response.ok) {
          throw new Error(`Token refresh failed: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Update the token
        this.authToken = {
          token: data.token,
          expiresAt: Date.now() + (data.expiresIn * 1000),
          tokenType: data.tokenType || this.authToken.tokenType
        };
        
        // Save to storage
        this.saveStateToStorage();
        
        logInfo('Token refreshed successfully');
        return this.authToken;
      } catch (error) {
        logError('Token refresh failed', error);
        
        // If refresh fails, clear the state
        this.clearState();
        throw error;
      } finally {
        // Clear the refresh promise
        this.tokenRefreshPromise = null;
      }
    })();
    
    return this.tokenRefreshPromise;
  }
  
  /**
   * Check if the user has a specific permission
   */
  async hasPermission(permission: string): Promise<boolean> {
    const user = await this.getCurrentUser();
    
    if (!user || !user.permissions) {
      return false;
    }
    
    return user.permissions.includes(permission);
  }
  
  /**
   * Check if the user has a specific role
   */
  async hasRole(role: string): Promise<boolean> {
    const user = await this.getCurrentUser();
    
    if (!user || !user.roles) {
      return false;
    }
    
    return user.roles.includes(role);
  }
  
  /**
   * Get an authentication header for API requests
   */
  async getAuthHeader(): Promise<Record<string, string>> {
    const token = await this.getAuthToken();
    
    if (!token) {
      return {};
    }
    
    return {
      'Authorization': `${token.tokenType} ${token.token}`
    };
  }
  
  /**
   * Get a pre-request interceptor function for fetch
   * This can be used to automatically add authentication headers to requests
   */
  getRequestInterceptor(): (input: RequestInfo | URL, init?: RequestInit) => Promise<RequestInit> {
    return async (input: RequestInfo | URL, init?: RequestInit): Promise<RequestInit> => {
      const headers = await this.getAuthHeader();
      
      return {
        ...init,
        headers: {
          ...headers,
          ...(init?.headers || {})
        }
      };
    };
  }
}

/**
 * Create and export a singleton instance of the authentication service
 */
export const authService = new AuthenticationService();

/**
 * Get the authentication service instance
 */
export function getAuthService(): IAuthenticationService {
  return authService;
} 