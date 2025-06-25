import { IUserService, UserSession, UserProfileDTO, UserProfileUpdateDTO } from './interfaces';
import { UserDocument, UserPreferences, UserRole } from '../models/user_model';
import { IUserRepository } from './interfaces';
import { hash, compare } from 'bcrypt';
import jwt from 'jsonwebtoken';

export class UserService implements IUserService {
  private readonly BCRYPT_ROUNDS = 10;
  private readonly JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
  private readonly SESSION_EXPIRY = '24h';
  private sessions: Map<string, UserSession> = new Map();

  constructor(private userRepository: IUserRepository) {}

  private mapToDTO(user: UserDocument): UserProfileDTO {
    return {
      id: user.id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      role: user.role,
      emailVerified: user.emailVerified,
      createdAt: user.createdAt,
      updatedAt: user.updatedAt
    };
  }

  async register(userData: Partial<UserProfileDTO>, password: string): Promise<UserProfileDTO> {
    // Hash password
    const hashedPassword = await hash(password, 12);

    // Create user
    const user = await this.userRepository.create({
      ...userData,
      password: hashedPassword,
      emailVerified: false,
      createdAt: new Date(),
      updatedAt: new Date()
    });

    return this.mapToDTO(user);
  }

  async authenticate(email: string, password: string, metadata?: { device?: string, ipAddress?: string }): Promise<{ user: UserProfileDTO, token: string }> {
    console.log('Authenticating user:', email);
    const user = await this.userRepository.findByEmail(email);
    
    if (!user || !user.password) {
      console.log('User not found or no password:', email);
      throw new Error('Invalid credentials');
    }
    
    console.log('Found user:', user.email, 'Comparing passwords...');
    const isValid = await compare(password, user.password);
    console.log('Password comparison result:', isValid);
    
    if (!isValid) {
      throw new Error('Invalid credentials');
    }

    const session = await this.createSession(user._id.toString(), metadata);
    return {
      user: this.mapToDTO(user),
      token: session.id
    };
  }

  async verifyEmail(token: string): Promise<boolean> {
    // TODO: Implement email verification
    return false;
  }

  async requestPasswordReset(email: string): Promise<boolean> {
    // TODO: Implement password reset request
    return false;
  }

  async resetPassword(token: string, newPassword: string): Promise<boolean> {
    // TODO: Implement password reset
    return false;
  }

  async changePassword(userId: string, currentPassword: string, newPassword: string): Promise<boolean> {
    const user = await this.userRepository.findById(userId);
    if (!user || !user.password) {
      return false;
    }

    const isValid = await compare(currentPassword, user.password);
    if (!isValid) {
      return false;
    }

    const hashedPassword = await hash(newPassword, this.BCRYPT_ROUNDS);
    await this.userRepository.updatePassword(userId, hashedPassword);
    return true;
  }

  async getUserById(id: string): Promise<UserProfileDTO | null> {
    const user = await this.userRepository.findById(id);
    return user ? this.mapToDTO(user) : null;
  }

  async getUserByEmail(email: string): Promise<UserProfileDTO | null> {
    const user = await this.userRepository.findByEmail(email);
    return user ? this.mapToDTO(user) : null;
  }

  async updateUser(id: string, data: Partial<UserProfileDTO>): Promise<UserProfileDTO> {
    const user = await this.userRepository.update(id, {
      ...data,
      updatedAt: new Date()
    });

    if (!user) {
      throw new Error('User not found');
    }

    return this.mapToDTO(user);
  }

  async getPreferences(userId: string): Promise<UserPreferences> {
    const user = await this.userRepository.findById(userId);
    if (!user) {
      throw new Error('User not found');
    }
    return user.preferences || {};
  }

  async updatePreferences(userId: string, preferences: Partial<UserPreferences>): Promise<UserPreferences> {
    const user = await this.userRepository.findById(userId);
    if (!user) {
      throw new Error('User not found');
    }

    const updatedPreferences = {
      ...(user.preferences || {}),
      ...preferences
    };

    const updatedUser = await this.userRepository.update(userId, {
      preferences: updatedPreferences
    });

    return updatedUser.preferences || {};
  }

  async changeEmail(userId: string, newEmail: string, password: string): Promise<boolean> {
    const user = await this.userRepository.findById(userId);
    if (!user || !user.password) {
      return false;
    }

    const isValid = await compare(password, user.password);
    if (!isValid) {
      return false;
    }

    const existingUser = await this.userRepository.findByEmail(newEmail);
    if (existingUser) {
      throw new Error('Email already in use');
    }

    await this.userRepository.update(userId, { email: newEmail });
    return true;
  }

  async linkAccounts(userId: string, targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean> {
    // TODO: Implement account linking
    return false;
  }

  async unlinkAccounts(userId: string, targetUserId: string, relationship: 'student' | 'parent' | 'partner'): Promise<boolean> {
    // TODO: Implement account unlinking
    return false;
  }

  async getLinkedUsers(userId: string, relationship: 'students' | 'parents' | 'partners'): Promise<UserProfileDTO[]> {
    // TODO: Implement getting linked users
    return [];
  }

  async searchUsers(query: string, excludeUserId?: string): Promise<UserProfileDTO[]> {
    // TODO: Implement user search
    return [];
  }

  async getAllUsers(filter?: Partial<UserProfileDTO>): Promise<UserProfileDTO[]> {
    // TODO: Implement getting all users
    return [];
  }

  async setTestMode(userId: string, enabled: boolean): Promise<UserProfileDTO> {
    // TODO: Implement test mode
    throw new Error('Not implemented');
  }

  async getTestModeUsers(): Promise<UserProfileDTO[]> {
    // TODO: Implement getting test mode users
    return [];
  }

  async disableAccount(userId: string): Promise<boolean> {
    // TODO: Implement account disabling
    return false;
  }

  async enableAccount(userId: string): Promise<boolean> {
    // TODO: Implement account enabling
    return false;
  }

  async deleteUser(id: string): Promise<boolean> {
    return await this.userRepository.delete(id);
  }

  async createSession(userId: string, metadata?: { device?: string; ipAddress?: string }): Promise<UserSession> {
    const sessionId = jwt.sign({ userId }, this.JWT_SECRET, { expiresIn: this.SESSION_EXPIRY });
    const expiresAt = new Date();
    expiresAt.setHours(expiresAt.getHours() + 24);

    const session: UserSession = {
      id: sessionId,
      userId,
      device: metadata?.device,
      ipAddress: metadata?.ipAddress,
      createdAt: new Date(),
      expiresAt
    };

    this.sessions.set(sessionId, session);
    return session;
  }

  async validateToken(token: string): Promise<{ isValid: boolean; userId?: string }> {
    try {
      const session = this.sessions.get(token);
      if (!session) {
        return { isValid: false };
      }

      if (new Date() > session.expiresAt) {
        this.sessions.delete(token);
        return { isValid: false };
      }

      return { isValid: true, userId: session.userId };
    } catch (error) {
      return { isValid: false };
    }
  }

  async invalidateSession(sessionId: string): Promise<boolean> {
    const session = this.sessions.get(sessionId);
    if (!session) {
      return false;
    }

    this.sessions.delete(sessionId);
    return true;
  }

  async invalidateAllSessions(userId: string): Promise<boolean> {
    for (const [sessionId, session] of this.sessions.entries()) {
      if (session.userId === userId) {
        this.sessions.delete(sessionId);
      }
    }
    return true;
  }

  async getUserSessions(userId: string): Promise<UserSession[]> {
    return Array.from(this.sessions.values()).filter(session => session.userId === userId);
  }

  async forceLogout(userId: string): Promise<boolean> {
    return this.invalidateAllSessions(userId);
  }

  async updateProfile(userId: string, profileData: Partial<UserProfileDTO>): Promise<UserProfileDTO> {
    const user = await this.userRepository.update(userId, {
      ...profileData,
      updatedAt: new Date()
    });

    if (!user) {
      throw new Error('User not found');
    }

    return this.mapToDTO(user);
  }
} 