/**
 * Authentication Service Interface
 * 
 * Defines the contract for authentication-related operations.
 * This follows the Interface Segregation Principle by including
 * only methods related to authentication.
 */

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  preferences: UserPreferences;
}

export type UserRole = 'student' | 'parent' | 'counselor' | 'admin';

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: 'en' | 'zh' | 'fr';
  notifications: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegistrationData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
}

export interface ResetPasswordData {
  email: string;
}

export interface IAuthService {
  /**
   * Log in a user with email and password
   * @param credentials User login credentials
   * @returns Promise resolving to authentication response
   */
  login(credentials: LoginCredentials): Promise<AuthResponse>;
  
  /**
   * Register a new user
   * @param data User registration data
   * @returns Promise resolving to authentication response
   */
  register(data: RegistrationData): Promise<AuthResponse>;
  
  /**
   * Log out the current user
   * @returns Promise that resolves when logout is complete
   */
  logout(): Promise<void>;
  
  /**
   * Get the currently authenticated user
   * @returns Promise resolving to the current user or null if not authenticated
   */
  getCurrentUser(): Promise<User | null>;
  
  /**
   * Check if the current user is authenticated
   * @returns Promise resolving to boolean indicating authentication status
   */
  isAuthenticated(): Promise<boolean>;
  
  /**
   * Refresh the authentication token
   * @returns Promise resolving to new authentication response
   */
  refreshToken(): Promise<AuthResponse>;
  
  /**
   * Request a password reset for a user
   * @param data Password reset data
   * @returns Promise that resolves when request is sent
   */
  requestPasswordReset(data: ResetPasswordData): Promise<void>;
  
  /**
   * Verify email with verification token
   * @param token Verification token
   * @returns Promise resolving to success status
   */
  verifyEmail(token: string): Promise<boolean>;
} 