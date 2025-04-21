import { UserDocument, UserPreferences } from '../models/user_model';

/**
 * User profile data transfer object
 */
export interface UserProfileDTO {
  id?: string;
  name?: string;
  email?: string;
  image?: string;
  role?: string;
  studentIds?: string[];
  parentIds?: string[];
  partnerIds?: string[];
  preferences?: UserPreferences;
  createdAt?: Date;
  updatedAt?: Date;
}

/**
 * User authentication service interface
 * Handles user authentication and token generation
 */
export interface IAuthenticationService {
  /**
   * Authenticate a user with email and password
   */
  authenticate(email: string, password: string): Promise<UserProfileDTO | null>;
  
  /**
   * Register a new user
   */
  register(userData: Partial<UserProfileDTO>, password: string): Promise<UserProfileDTO>;
  
  /**
   * Verify a user's email address
   */
  verifyEmail(token: string): Promise<boolean>;
  
  /**
   * Request a password reset
   */
  requestPasswordReset(email: string): Promise<boolean>;
  
  /**
   * Reset a user's password with a token
   */
  resetPassword(token: string, newPassword: string): Promise<boolean>;
  
  /**
   * Change a user's password (requires current password)
   */
  changePassword(userId: string, currentPassword: string, newPassword: string): Promise<boolean>;
}

/**
 * User profile service interface
 * Handles user profile management
 */
export interface IUserProfileService {
  /**
   * Get user profile by ID
   */
  getUserById(userId: string): Promise<UserProfileDTO | null>;
  
  /**
   * Get user profile by email
   */
  getUserByEmail(email: string): Promise<UserProfileDTO | null>;
  
  /**
   * Update user profile
   */
  updateProfile(userId: string, profileData: Partial<UserProfileDTO>): Promise<UserProfileDTO>;
  
  /**
   * Get user preferences
   */
  getPreferences(userId: string): Promise<UserPreferences>;
  
  /**
   * Update user preferences
   */
  updatePreferences(userId: string, preferences: Partial<UserPreferences>): Promise<UserPreferences>;
  
  /**
   * Change user email (requires password verification)
   */
  changeEmail(userId: string, newEmail: string, password: string): Promise<boolean>;
}

/**
 * User relationship service interface
 * Handles user relationships (parent-student, partnerships)
 */
export interface IUserRelationshipService {
  /**
   * Link one user to another
   */
  linkAccounts(userId: string, targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean>;
  
  /**
   * Unlink one user from another
   */
  unlinkAccounts(userId: string, targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean>;
  
  /**
   * Get users linked to this user
   */
  getLinkedUsers(userId: string, relationship: 'students' | 'parents' | 'partners'): Promise<UserProfileDTO[]>;
  
  /**
   * Search for users (for linking accounts)
   */
  searchUsers(query: string, excludeUserId?: string): Promise<UserProfileDTO[]>;
}

/**
 * Comprehensive user service interface
 * Combines all user-related service interfaces
 */
export interface IUserService extends IAuthenticationService, IUserProfileService, IUserRelationshipService {
  // This interface combines all the functionality from the specialized interfaces
}

/**
 * Data repository interface for User
 * Follows the Repository pattern for data access
 */
export interface IUserRepository {
  /**
   * Find a user by ID
   */
  findById(id: string): Promise<UserDocument | null>;
  
  /**
   * Find a user by email
   */
  findByEmail(email: string): Promise<UserDocument | null>;
  
  /**
   * Create a new user
   */
  create(userData: Partial<UserDocument>): Promise<UserDocument>;
  
  /**
   * Update a user
   */
  update(id: string, userData: Partial<UserDocument>): Promise<UserDocument | null>;
  
  /**
   * Delete a user
   */
  delete(id: string): Promise<boolean>;
  
  /**
   * Find linked users
   */
  findLinkedUsers(userId: string, relationship: string): Promise<UserDocument[]>;
  
  /**
   * Search users by query
   */
  search(query: string, excludeId?: string, limit?: number): Promise<UserDocument[]>;
} 