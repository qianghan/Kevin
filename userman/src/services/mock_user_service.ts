import { IUserService, UserProfileDTO } from './interfaces';
import { UserPreferences } from '../models/user_model';

/**
 * Mock implementation of the user service for testing and development
 */
export class MockUserService implements IUserService {
  private mockUsers: Map<string, UserProfileDTO> = new Map();
  private mockSessions: Map<string, { userId: string, token: string }> = new Map();

  constructor() {
    // Initialize with a test user
    const testUser: UserProfileDTO = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'student',
      preferences: {
        theme: 'light',
        language: 'en',
        emailNotifications: true
      },
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.mockUsers.set(testUser.id!, testUser);
  }

  async authenticate(email: string, password: string): Promise<{ user: UserProfileDTO, token: string }> {
    const user = Array.from(this.mockUsers.values()).find(u => u.email === email);
    if (!user) {
      throw new Error('Invalid credentials');
    }

    const token = `mock-token-${Date.now()}`;
    this.mockSessions.set(token, { userId: user.id!, token });

    return { user, token };
  }

  async register(userData: Partial<UserProfileDTO>, password: string): Promise<UserProfileDTO> {
    const existingUser = Array.from(this.mockUsers.values()).find(u => u.email === userData.email);
    if (existingUser) {
      throw new Error('User already exists');
    }

    const newUser: UserProfileDTO = {
      id: `${this.mockUsers.size + 1}`,
      email: userData.email!,
      name: userData.name!,
      role: userData.role || 'student',
      preferences: userData.preferences || {
        theme: 'light',
        language: 'en',
        emailNotifications: true
      },
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.mockUsers.set(newUser.id!, newUser);
    return newUser;
  }

  async verifyEmail(token: string): Promise<boolean> {
    return true;
  }

  async requestPasswordReset(email: string): Promise<boolean> {
    return true;
  }

  async resetPassword(token: string, newPassword: string): Promise<boolean> {
    return true;
  }

  async changePassword(userId: string, currentPassword: string, newPassword: string): Promise<boolean> {
    return true;
  }

  async createSession(userId: string): Promise<any> {
    const token = `mock-session-${Date.now()}`;
    this.mockSessions.set(token, { userId, token });
    return { token };
  }

  async getUserSessions(userId: string): Promise<any[]> {
    return Array.from(this.mockSessions.values()).filter(s => s.userId === userId);
  }

  async invalidateSession(sessionId: string): Promise<boolean> {
    return this.mockSessions.delete(sessionId);
  }

  async invalidateAllSessions(userId: string): Promise<boolean> {
    for (const [token, session] of this.mockSessions.entries()) {
      if (session.userId === userId) {
        this.mockSessions.delete(token);
      }
    }
    return true;
  }

  async validateToken(token: string): Promise<{ isValid: boolean, userId?: string }> {
    const session = this.mockSessions.get(token);
    return {
      isValid: !!session,
      userId: session?.userId
    };
  }

  async getUserById(userId: string): Promise<UserProfileDTO | null> {
    return this.mockUsers.get(userId) || null;
  }

  async getUserByEmail(email: string): Promise<UserProfileDTO | null> {
    return Array.from(this.mockUsers.values()).find(u => u.email === email) || null;
  }

  async updateProfile(userId: string, profileData: Partial<UserProfileDTO>): Promise<UserProfileDTO> {
    const user = this.mockUsers.get(userId);
    if (!user) {
      throw new Error('User not found');
    }

    const updatedUser = {
      ...user,
      ...profileData,
      updatedAt: new Date()
    };

    this.mockUsers.set(userId, updatedUser);
    return updatedUser;
  }

  async getPreferences(userId: string): Promise<UserPreferences> {
    const user = this.mockUsers.get(userId);
    if (!user) {
      throw new Error('User not found');
    }
    return user.preferences || {
      theme: 'light',
      language: 'en',
      emailNotifications: true
    };
  }

  async updatePreferences(userId: string, preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    const user = this.mockUsers.get(userId);
    if (!user) {
      throw new Error('User not found');
    }

    const updatedPreferences = {
      ...user.preferences,
      ...preferences
    };

    user.preferences = updatedPreferences;
    user.updatedAt = new Date();
    this.mockUsers.set(userId, user);

    return updatedPreferences;
  }

  async changeEmail(userId: string, newEmail: string, password: string): Promise<boolean> {
    const user = this.mockUsers.get(userId);
    if (!user) {
      throw new Error('User not found');
    }

    user.email = newEmail;
    user.updatedAt = new Date();
    this.mockUsers.set(userId, user);

    return true;
  }

  async linkAccounts(): Promise<boolean> {
    return true;
  }

  async unlinkAccounts(): Promise<boolean> {
    return true;
  }

  async getLinkedUsers(): Promise<UserProfileDTO[]> {
    return [];
  }

  async searchUsers(): Promise<UserProfileDTO[]> {
    return Array.from(this.mockUsers.values());
  }

  async getAllUsers(): Promise<UserProfileDTO[]> {
    return Array.from(this.mockUsers.values());
  }

  async setTestMode(): Promise<UserProfileDTO> {
    throw new Error('Not implemented');
  }

  async getTestModeUsers(): Promise<UserProfileDTO[]> {
    return [];
  }

  async forceLogout(): Promise<boolean> {
    return true;
  }

  async disableAccount(): Promise<boolean> {
    return true;
  }

  async enableAccount(): Promise<boolean> {
    return true;
  }
} 