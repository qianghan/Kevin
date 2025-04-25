/**
 * Authentication Service Implementation
 * 
 * This is a concrete implementation of the IAuthService interface.
 * It provides authentication functionality for the application.
 */

import { 
  IAuthService, 
  User, 
  LoginCredentials, 
  RegistrationData, 
  AuthResponse, 
  ResetPasswordData 
} from '../../interfaces/services/auth.service';

/**
 * Authentication Service that implements the IAuthService interface
 */
export class AuthService implements IAuthService {
  private API_URL = '/api/auth';
  private currentToken: string | null = null;
  private currentRefreshToken: string | null = null;
  
  /**
   * Login a user with email and password
   */
  public async login(credentials: LoginCredentials): Promise<AuthResponse> {
    try {
      const response = await fetch(`${this.API_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });
      
      if (!response.ok) {
        throw new Error('Login failed');
      }
      
      const data = await response.json();
      this.setTokens(data.token, data.refreshToken);
      
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }
  
  /**
   * Register a new user
   */
  public async register(data: RegistrationData): Promise<AuthResponse> {
    try {
      const response = await fetch(`${this.API_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error('Registration failed');
      }
      
      const responseData = await response.json();
      this.setTokens(responseData.token, responseData.refreshToken);
      
      return responseData;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  }
  
  /**
   * Logout the current user
   */
  public async logout(): Promise<void> {
    try {
      if (this.currentToken) {
        await fetch(`${this.API_URL}/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.currentToken}`,
          },
        });
      }
      
      this.clearTokens();
    } catch (error) {
      console.error('Logout error:', error);
      // Still clear tokens on error
      this.clearTokens();
    }
  }
  
  /**
   * Get the currently authenticated user
   */
  public async getCurrentUser(): Promise<User | null> {
    if (!this.currentToken) {
      return null;
    }
    
    try {
      const response = await fetch(`${this.API_URL}/me`, {
        headers: {
          'Authorization': `Bearer ${this.currentToken}`,
        },
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          this.clearTokens();
          return null;
        }
        throw new Error('Failed to get current user');
      }
      
      return await response.json();
    } catch (error) {
      console.error('Get current user error:', error);
      return null;
    }
  }
  
  /**
   * Check if the current user is authenticated
   */
  public async isAuthenticated(): Promise<boolean> {
    const user = await this.getCurrentUser();
    return user !== null;
  }
  
  /**
   * Refresh the authentication token
   */
  public async refreshToken(): Promise<AuthResponse> {
    if (!this.currentRefreshToken) {
      throw new Error('No refresh token available');
    }
    
    try {
      const response = await fetch(`${this.API_URL}/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refreshToken: this.currentRefreshToken }),
      });
      
      if (!response.ok) {
        this.clearTokens();
        throw new Error('Token refresh failed');
      }
      
      const data = await response.json();
      this.setTokens(data.token, data.refreshToken);
      
      return data;
    } catch (error) {
      console.error('Token refresh error:', error);
      this.clearTokens();
      throw error;
    }
  }
  
  /**
   * Request a password reset for a user
   */
  public async requestPasswordReset(data: ResetPasswordData): Promise<void> {
    try {
      const response = await fetch(`${this.API_URL}/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) {
        throw new Error('Password reset request failed');
      }
    } catch (error) {
      console.error('Password reset request error:', error);
      throw error;
    }
  }
  
  /**
   * Verify email with verification token
   */
  public async verifyEmail(token: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.API_URL}/verify-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });
      
      if (!response.ok) {
        throw new Error('Email verification failed');
      }
      
      const data = await response.json();
      return data.success;
    } catch (error) {
      console.error('Email verification error:', error);
      return false;
    }
  }
  
  /**
   * Set authentication tokens
   */
  private setTokens(token: string, refreshToken: string): void {
    this.currentToken = token;
    this.currentRefreshToken = refreshToken;
    
    // Store tokens in localStorage for persistence
    localStorage.setItem('auth_token', token);
    localStorage.setItem('refresh_token', refreshToken);
  }
  
  /**
   * Clear authentication tokens
   */
  private clearTokens(): void {
    this.currentToken = null;
    this.currentRefreshToken = null;
    
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
  }
  
  /**
   * Initialize service by loading tokens from storage
   */
  public initialize(): void {
    this.currentToken = localStorage.getItem('auth_token');
    this.currentRefreshToken = localStorage.getItem('refresh_token');
  }
} 