import { compare, hash } from 'bcrypt';
import { IUserService, UserProfileDTO } from './interfaces';
import { IUserRepository } from './interfaces';
import { UserDocument, UserPreferences } from '../models/user_model';

/**
 * Converts a UserDocument to a UserProfileDTO
 */
const mapUserToDTO = (user: UserDocument): UserProfileDTO => {
  return {
    id: user._id?.toString(),
    name: user.name,
    email: user.email,
    image: user.image,
    role: user.role,
    studentIds: user.studentIds?.map(id => id.toString()),
    parentIds: user.parentIds?.map(id => id.toString()),
    partnerIds: user.partnerIds?.map(id => id.toString()),
    preferences: user.preferences,
    createdAt: user.createdAt,
    updatedAt: user.updatedAt
  };
};

/**
 * Implementation of the user service
 * Follows Single Responsibility Principle by delegating data access to repository
 */
export class UserService implements IUserService {
  private userRepository: IUserRepository;
  private BCRYPT_ROUNDS = 12;
  
  /**
   * Constructor with dependency injection for repository
   */
  constructor(userRepository: IUserRepository) {
    this.userRepository = userRepository;
  }
  
  /**
   * Authenticate a user with email and password
   */
  async authenticate(email: string, password: string): Promise<UserProfileDTO | null> {
    try {
      const user = await this.userRepository.findByEmail(email);
      
      if (!user || !user.password) {
        return null;
      }
      
      const isPasswordValid = await compare(password, user.password);
      
      if (!isPasswordValid) {
        return null;
      }
      
      return mapUserToDTO(user);
    } catch (error) {
      console.error('Authentication error:', error);
      return null;
    }
  }
  
  /**
   * Register a new user
   */
  async register(userData: Partial<UserProfileDTO>, password: string): Promise<UserProfileDTO> {
    try {
      // Check if user already exists
      const existingUser = await this.userRepository.findByEmail(userData.email!);
      
      if (existingUser) {
        throw new Error('User with this email already exists');
      }
      
      // Hash password
      const hashedPassword = await hash(password, this.BCRYPT_ROUNDS);
      
      // Create new user
      const createdUser = await this.userRepository.create({
        email: userData.email!,
        name: userData.name!,
        password: hashedPassword,
        role: userData.role as any || 'student',
        image: userData.image,
        preferences: userData.preferences
      });
      
      return mapUserToDTO(createdUser);
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  }
  
  /**
   * Verify a user's email address
   */
  async verifyEmail(token: string): Promise<boolean> {
    // TODO: Implement email verification logic
    return false;
  }
  
  /**
   * Request a password reset
   */
  async requestPasswordReset(email: string): Promise<boolean> {
    // TODO: Implement password reset request logic
    return false;
  }
  
  /**
   * Reset a user's password with a token
   */
  async resetPassword(token: string, newPassword: string): Promise<boolean> {
    // TODO: Implement password reset logic
    return false;
  }
  
  /**
   * Change a user's password (requires current password)
   */
  async changePassword(userId: string, currentPassword: string, newPassword: string): Promise<boolean> {
    try {
      const user = await this.userRepository.findById(userId);
      
      if (!user || !user.password) {
        return false;
      }
      
      const isPasswordValid = await compare(currentPassword, user.password);
      
      if (!isPasswordValid) {
        return false;
      }
      
      const hashedPassword = await hash(newPassword, this.BCRYPT_ROUNDS);
      
      const updated = await this.userRepository.update(userId, {
        password: hashedPassword
      });
      
      return !!updated;
    } catch (error) {
      console.error('Change password error:', error);
      return false;
    }
  }
  
  /**
   * Get user profile by ID
   */
  async getUserById(userId: string): Promise<UserProfileDTO | null> {
    try {
      const user = await this.userRepository.findById(userId);
      return user ? mapUserToDTO(user) : null;
    } catch (error) {
      console.error('Get user by ID error:', error);
      return null;
    }
  }
  
  /**
   * Get user profile by email
   */
  async getUserByEmail(email: string): Promise<UserProfileDTO | null> {
    try {
      const user = await this.userRepository.findByEmail(email);
      return user ? mapUserToDTO(user) : null;
    } catch (error) {
      console.error('Get user by email error:', error);
      return null;
    }
  }
  
  /**
   * Update user profile
   */
  async updateProfile(userId: string, profileData: Partial<UserProfileDTO>): Promise<UserProfileDTO> {
    try {
      // Extract only updatable fields (exclude sensitive fields)
      const { id, email, password, ...updatableFields } = profileData;
      
      const updatedUser = await this.userRepository.update(userId, updatableFields as any);
      
      if (!updatedUser) {
        throw new Error('User not found or could not be updated');
      }
      
      return mapUserToDTO(updatedUser);
    } catch (error) {
      console.error('Update profile error:', error);
      throw error;
    }
  }
  
  /**
   * Get user preferences
   */
  async getPreferences(userId: string): Promise<UserPreferences> {
    try {
      const user = await this.userRepository.findById(userId);
      
      if (!user) {
        throw new Error('User not found');
      }
      
      return user.preferences || {
        theme: 'system',
        emailNotifications: true,
        language: 'en'
      };
    } catch (error) {
      console.error('Get preferences error:', error);
      throw error;
    }
  }
  
  /**
   * Update user preferences
   */
  async updatePreferences(userId: string, preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    try {
      const user = await this.userRepository.findById(userId);
      
      if (!user) {
        throw new Error('User not found');
      }
      
      // Merge existing preferences with new ones
      const updatedPreferences = {
        ...(user.preferences || {}),
        ...preferences
      };
      
      const updatedUser = await this.userRepository.update(userId, {
        preferences: updatedPreferences
      });
      
      if (!updatedUser) {
        throw new Error('User preferences could not be updated');
      }
      
      return updatedUser.preferences || {};
    } catch (error) {
      console.error('Update preferences error:', error);
      throw error;
    }
  }
  
  /**
   * Change user email (requires password verification)
   */
  async changeEmail(userId: string, newEmail: string, password: string): Promise<boolean> {
    try {
      const user = await this.userRepository.findById(userId);
      
      if (!user || !user.password) {
        return false;
      }
      
      // Check if email is already taken
      const existingUser = await this.userRepository.findByEmail(newEmail);
      
      if (existingUser) {
        throw new Error('Email already in use');
      }
      
      // Verify password
      const isPasswordValid = await compare(password, user.password);
      
      if (!isPasswordValid) {
        return false;
      }
      
      // Update email
      const updated = await this.userRepository.update(userId, {
        email: newEmail
      });
      
      return !!updated;
    } catch (error) {
      console.error('Change email error:', error);
      throw error;
    }
  }
  
  /**
   * Link one user to another
   */
  async linkAccounts(userId: string, targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean> {
    try {
      const user = await this.userRepository.findById(userId);
      const targetUser = await this.userRepository.findById(targetUserId);
      
      if (!user || !targetUser) {
        return false;
      }
      
      // Update based on relationship type
      if (relationship === 'student') {
        // Parent (user) adds a student (targetUser)
        if (user.studentIds?.includes(targetUser._id)) {
          return true; // Already linked
        }
        
        await this.userRepository.update(userId, {
          studentIds: [...(user.studentIds || []), targetUser._id]
        });
        
        await this.userRepository.update(targetUserId, {
          parentIds: [...(targetUser.parentIds || []), user._id]
        });
      } else if (relationship === 'parent') {
        // Student (user) adds a parent (targetUser)
        if (user.parentIds?.includes(targetUser._id)) {
          return true; // Already linked
        }
        
        await this.userRepository.update(userId, {
          parentIds: [...(user.parentIds || []), targetUser._id]
        });
        
        await this.userRepository.update(targetUserId, {
          studentIds: [...(targetUser.studentIds || []), user._id]
        });
      } else if (relationship === 'partner') {
        // Parent (user) adds a partner (targetUser)
        if (user.partnerIds?.includes(targetUser._id)) {
          return true; // Already linked
        }
        
        await this.userRepository.update(userId, {
          partnerIds: [...(user.partnerIds || []), targetUser._id]
        });
        
        await this.userRepository.update(targetUserId, {
          partnerIds: [...(targetUser.partnerIds || []), user._id]
        });
      }
      
      return true;
    } catch (error) {
      console.error('Link accounts error:', error);
      return false;
    }
  }
  
  /**
   * Unlink one user from another
   */
  async unlinkAccounts(userId: string, targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean> {
    try {
      const user = await this.userRepository.findById(userId);
      const targetUser = await this.userRepository.findById(targetUserId);
      
      if (!user || !targetUser) {
        return false;
      }
      
      // Update based on relationship type
      if (relationship === 'student') {
        // Parent (user) removes a student (targetUser)
        await this.userRepository.update(userId, {
          studentIds: (user.studentIds || []).filter(id => !id.equals(targetUser._id))
        });
        
        await this.userRepository.update(targetUserId, {
          parentIds: (targetUser.parentIds || []).filter(id => !id.equals(user._id))
        });
      } else if (relationship === 'parent') {
        // Student (user) removes a parent (targetUser)
        await this.userRepository.update(userId, {
          parentIds: (user.parentIds || []).filter(id => !id.equals(targetUser._id))
        });
        
        await this.userRepository.update(targetUserId, {
          studentIds: (targetUser.studentIds || []).filter(id => !id.equals(user._id))
        });
      } else if (relationship === 'partner') {
        // Parent (user) removes a partner (targetUser)
        await this.userRepository.update(userId, {
          partnerIds: (user.partnerIds || []).filter(id => !id.equals(targetUser._id))
        });
        
        await this.userRepository.update(targetUserId, {
          partnerIds: (targetUser.partnerIds || []).filter(id => !id.equals(user._id))
        });
      }
      
      return true;
    } catch (error) {
      console.error('Unlink accounts error:', error);
      return false;
    }
  }
  
  /**
   * Get users linked to this user
   */
  async getLinkedUsers(userId: string, relationship: 'students' | 'parents' | 'partners'): Promise<UserProfileDTO[]> {
    try {
      const linkedUsers = await this.userRepository.findLinkedUsers(userId, relationship);
      return linkedUsers.map(mapUserToDTO);
    } catch (error) {
      console.error(`Get ${relationship} error:`, error);
      return [];
    }
  }
  
  /**
   * Search for users (for linking accounts)
   */
  async searchUsers(query: string, excludeUserId?: string): Promise<UserProfileDTO[]> {
    try {
      const users = await this.userRepository.search(query, excludeUserId, 10);
      return users.map(mapUserToDTO);
    } catch (error) {
      console.error('Search users error:', error);
      return [];
    }
  }

  /**
   * Get all users with optional filtering
   * @param filter Optional filter for users
   * @returns Array of user profiles matching the filter
   */
  async getAllUsers(filter?: Partial<UserProfileDTO>): Promise<UserProfileDTO[]> {
    try {
      // Convert DTO filter to document filter
      const docFilter: Partial<UserDocument> = {};
      
      if (filter) {
        if (filter.role) docFilter.role = filter.role as any;
        if (filter.testMode !== undefined) docFilter.testMode = filter.testMode;
        // Add other filter mappings as needed
      }
      
      const users = await this.userRepository.findAll(docFilter);
      return users.map(user => this.mapUserToProfile(user));
    } catch (error) {
      console.error('Error getting all users:', error);
      throw new Error('Failed to get users');
    }
  }

  /**
   * Toggle test mode for a user
   * @param userId User ID to modify
   * @param enabled Whether test mode should be enabled
   * @returns Updated user profile
   */
  async setTestMode(userId: string, enabled: boolean): Promise<UserProfileDTO> {
    try {
      const user = await this.userRepository.update(userId, { testMode: enabled });
      
      if (!user) {
        throw new Error('User not found');
      }
      
      return this.mapUserToProfile(user);
    } catch (error) {
      console.error('Error setting test mode:', error);
      throw new Error('Failed to set test mode');
    }
  }

  /**
   * Get all users in test mode
   * @returns Array of user profiles with test mode enabled
   */
  async getTestModeUsers(): Promise<UserProfileDTO[]> {
    try {
      const users = await this.userRepository.findAll({ testMode: true });
      return users.map(user => this.mapUserToProfile(user));
    } catch (error) {
      console.error('Error getting test mode users:', error);
      throw new Error('Failed to get test mode users');
    }
  }

  /**
   * Force logout a user
   * This is a placeholder implementation. In a production system,
   * this would need to invalidate the user's active tokens.
   * @param userId User ID to log out
   * @returns Success status
   */
  async forceLogout(userId: string): Promise<boolean> {
    try {
      // Implementation would depend on how you're handling
      // token storage and validation
      console.log(`Force logout for user ${userId}`);
      return true;
    } catch (error) {
      console.error('Error forcing logout:', error);
      throw new Error('Failed to force logout');
    }
  }

  /**
   * Disable a user account
   * This is a placeholder implementation.
   * @param userId User ID to disable
   * @returns Success status
   */
  async disableAccount(userId: string): Promise<boolean> {
    try {
      // In a real implementation, you'd set an "enabled" flag to false
      // or implement a soft delete
      console.log(`Disable account for user ${userId}`);
      return true;
    } catch (error) {
      console.error('Error disabling account:', error);
      throw new Error('Failed to disable account');
    }
  }

  /**
   * Enable a user account
   * This is a placeholder implementation.
   * @param userId User ID to enable
   * @returns Success status
   */
  async enableAccount(userId: string): Promise<boolean> {
    try {
      // In a real implementation, you'd set an "enabled" flag to true
      console.log(`Enable account for user ${userId}`);
      return true;
    } catch (error) {
      console.error('Error enabling account:', error);
      throw new Error('Failed to enable account');
    }
  }
} 