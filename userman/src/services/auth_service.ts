import { compare, hash } from 'bcrypt';
import { IUserRepository, ISessionRepository, IAuditLogService, AuditEventType } from './interfaces';
import { IAuthenticationService, UserProfileDTO, UserSession } from './interfaces';
import { UserDocument, UserRole } from '../models/user_model';
import { TokenType } from '../models/verification_token_model';
import * as jwt from 'jsonwebtoken';
import crypto from 'crypto';
import { isPasswordValid, validatePassword, PasswordValidationResult } from '../utils/password_validator';

/**
 * Configuration for authentication service
 */
export interface AuthServiceConfig {
  jwtSecret: string;
  tokenExpiresIn: string; // e.g., '1d', '8h'
  emailVerificationRequired: boolean;
  emailService?: any; // Optional email service for sending verification emails
  maxLoginAttempts?: number; // Maximum number of failed login attempts before lockout
  lockoutDuration?: number; // Lockout duration in minutes
}

/**
 * Default configuration
 */
const DEFAULT_CONFIG: AuthServiceConfig = {
  jwtSecret: process.env.JWT_SECRET || 'dev-secret-key',
  tokenExpiresIn: '1d',
  emailVerificationRequired: false,
  maxLoginAttempts: 5,
  lockoutDuration: 30
};

/**
 * Implementation of the authentication service
 */
export class AuthService implements IAuthenticationService {
  private userRepository: IUserRepository;
  private sessionRepository: ISessionRepository;
  private auditLogService?: IAuditLogService;
  private config: AuthServiceConfig;
  private BCRYPT_ROUNDS = 12;
  private readonly DEFAULT_MAX_LOGIN_ATTEMPTS = 5;
  private readonly DEFAULT_LOCKOUT_DURATION = 30; // 30 minutes
  
  /**
   * Constructor with dependency injection
   */
  constructor(
    userRepository: IUserRepository,
    sessionRepository: ISessionRepository,
    config: Partial<AuthServiceConfig> = {},
    auditLogService?: IAuditLogService
  ) {
    this.userRepository = userRepository;
    this.sessionRepository = sessionRepository;
    this.auditLogService = auditLogService;
    this.config = { ...DEFAULT_CONFIG, ...config };
  }
  
  /**
   * Authenticate a user with email and password
   */
  async authenticate(
    email: string,
    password: string,
    metadata?: { device?: string; ipAddress?: string; userAgent?: string }
  ): Promise<{ user: UserProfileDTO; token: string }> {
    try {
      const user = await this.userRepository.findByEmail(email);
      
      if (!user) {
        // Log failed login attempt
        await this.logAuditEvent(
          AuditEventType.USER_LOGIN_FAILED,
          undefined,
          false,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { reason: 'User not found', email }
          }
        );
        
        throw new Error('Invalid email or password');
      }
      
      // Check if account is locked
      if (user.lockedUntil && new Date(user.lockedUntil) > new Date()) {
        const minutesLeft = Math.ceil(
          (new Date(user.lockedUntil).getTime() - new Date().getTime()) / (60 * 1000)
        );
        
        // Log failed login attempt due to account being locked
        await this.logAuditEvent(
          AuditEventType.USER_LOGIN_FAILED,
          user.id,
          false,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { reason: 'Account locked', minutesLeft }
          }
        );
        
        throw new Error(`Account is locked. Please try again in ${minutesLeft} minutes.`);
      }
      
      // Check password
      const isPasswordValid = user.password && await compare(password, user.password);
      
      if (!isPasswordValid) {
        // Increment failed login attempts
        const failedAttempts = (user.failedLoginAttempts || 0) + 1;
        const updateData: any = { failedLoginAttempts: failedAttempts };
        
        // Lock account if max attempts reached
        if (failedAttempts >= this.config.maxLoginAttempts!) {
          const lockoutTime = new Date();
          lockoutTime.setMinutes(lockoutTime.getMinutes() + this.config.lockoutDuration!);
          updateData.lockedUntil = lockoutTime;
          
          // Log account lockout
          await this.logAuditEvent(
            AuditEventType.ACCOUNT_LOCKED,
            user.id,
            true,
            { 
              ipAddress: metadata?.ipAddress,
              userAgent: metadata?.userAgent,
              details: { reason: 'Max failed login attempts reached', failedAttempts, lockoutMinutes: this.config.lockoutDuration }
            }
          );
        }
        
        await this.userRepository.updateById(user.id, updateData);
        
        // Log failed login attempt
        await this.logAuditEvent(
          AuditEventType.USER_LOGIN_FAILED,
          user.id,
          false,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { reason: 'Invalid password', failedAttempts }
          }
        );
        
        throw new Error('Invalid email or password');
      }
      
      // Reset failed login attempts on successful login
      if (user.failedLoginAttempts) {
        await this.userRepository.updateById(user.id, {
          failedLoginAttempts: 0,
          lockedUntil: undefined
        });
        
        // Log account unlock if it was previously locked
        if (user.lockedUntil) {
          await this.logAuditEvent(
            AuditEventType.ACCOUNT_UNLOCKED,
            user.id,
            true,
            { 
              ipAddress: metadata?.ipAddress,
              userAgent: metadata?.userAgent,
              details: { reason: 'Successful login after failed attempts' }
            }
          );
        }
      }
      
      // Check if email is verified (if required)
      if (this.config.emailVerificationRequired && !user.emailVerified) {
        await this.logAuditEvent(
          AuditEventType.USER_LOGIN_FAILED,
          user.id,
          false,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { reason: 'Email not verified' }
          }
        );
        
        throw new Error('Email not verified. Please verify your email before logging in.');
      }
      
      // Create session
      const session = await this.createSession(user.id, metadata);
      
      // Log successful login
      await this.logAuditEvent(
        AuditEventType.USER_LOGIN,
        user.id,
        true,
        { 
          ipAddress: metadata?.ipAddress,
          userAgent: metadata?.userAgent,
          details: { sessionId: session.id }
        }
      );
      
      // Map user to profile DTO
      const userProfile = this.mapUserToProfile(user);
      
      return {
        user: userProfile,
        token: session.token
      };
    } catch (error) {
      console.error('Authentication error:', error);
      throw error;
    }
  }
  
  /**
   * Register a new user
   */
  async register(
    userData: Partial<UserProfileDTO>, 
    password: string,
    metadata?: { ipAddress?: string; userAgent?: string }
  ): Promise<UserProfileDTO> {
    try {
      // Check if user already exists
      const existingUser = await this.userRepository.findByEmail(userData.email);
      
      if (existingUser) {
        await this.logAuditEvent(
          AuditEventType.USER_CREATED,
          undefined,
          false,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { reason: 'Email already exists', email: userData.email }
          }
        );
        
        throw new Error('User with this email already exists');
      }
      
      // Validate password strength
      const validationResult = validatePassword(password);
      if (!validationResult.isValid) {
        await this.logAuditEvent(
          AuditEventType.USER_CREATED,
          undefined,
          false,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { reason: 'Password too weak', email: userData.email, errors: validationResult.errors }
          }
        );
        
        throw new Error(`Password is not strong enough: ${validationResult.errors.join(', ')}`);
      }
      
      // Hash password
      const hashedPassword = await hash(password, this.BCRYPT_ROUNDS);
      
      // Create new user
      const createdUser = await this.userRepository.create({
        email: userData.email || '',
        name: userData.name || '',
        password: hashedPassword,
        role: (userData.role as UserRole) || 'student',
        image: userData.image,
        preferences: userData.preferences
      });
      
      // Send verification email if required
      if (this.config.emailVerificationRequired && this.config.emailService) {
        await this.sendVerificationEmail(createdUser);
        
        await this.logAuditEvent(
          AuditEventType.EMAIL_VERIFICATION,
          createdUser.id,
          true,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { action: 'Verification email sent' }
          }
        );
      } else if (!this.config.emailVerificationRequired) {
        // Auto-verify email if not required
        await this.userRepository.updateById(createdUser.id, {
          emailVerified: new Date()
        });
      }
      
      // Log user creation
      await this.logAuditEvent(
        AuditEventType.USER_CREATED,
        createdUser.id,
        true,
        { 
          ipAddress: metadata?.ipAddress,
          userAgent: metadata?.userAgent,
          details: { email: createdUser.email, role: createdUser.role }
        }
      );
      
      return this.mapUserToProfile(createdUser);
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  }
  
  /**
   * Verify a user's email address
   */
  async verifyEmail(token: string): Promise<boolean> {
    try {
      // Verify the token
      const tokenData = await this.verifyToken(token, TokenType.EMAIL_VERIFICATION);
      
      if (!tokenData) {
        return false;
      }
      
      const { userId } = tokenData;
      
      // Update user email verified status
      const updated = await this.userRepository.update(userId, {
        emailVerified: new Date()
      });
      
      return !!updated;
    } catch (error) {
      console.error('Email verification error:', error);
      return false;
    }
  }
  
  /**
   * Request a password reset
   */
  async requestPasswordReset(email: string): Promise<boolean> {
    try {
      const user = await this.userRepository.findByEmail(email);
      
      if (!user) {
        // Don't reveal if the email exists or not for security
        return true;
      }
      
      // Create password reset token
      const token = await this.createToken(user.id, TokenType.PASSWORD_RESET);
      
      // Send password reset email
      if (this.config.emailService) {
        await this.sendPasswordResetEmail(user, token);
      }
      
      return true;
    } catch (error) {
      console.error('Password reset request error:', error);
      return false;
    }
  }
  
  /**
   * Reset a user's password with a token
   */
  async resetPassword(
    token: string, 
    newPassword: string,
    metadata?: { ipAddress?: string; userAgent?: string }
  ): Promise<boolean> {
    try {
      // Verify the token
      const tokenData = await this.verifyToken(token, TokenType.PASSWORD_RESET);
      
      if (!tokenData) {
        await this.logAuditEvent(
          AuditEventType.PASSWORD_RESET,
          undefined,
          false,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { reason: 'Invalid token' }
          }
        );
        
        return false;
      }
      
      // Validate password strength
      const validationResult = validatePassword(newPassword);
      if (!validationResult.isValid) {
        await this.logAuditEvent(
          AuditEventType.PASSWORD_RESET,
          tokenData.userId,
          false,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { reason: 'Password too weak', errors: validationResult.errors }
          }
        );
        
        throw new Error(`Password is not strong enough: ${validationResult.errors.join(', ')}`);
      }
      
      const { userId } = tokenData;
      
      // Hash new password
      const hashedPassword = await hash(newPassword, this.BCRYPT_ROUNDS);
      
      // Update user password
      const updated = await this.userRepository.updateById(userId, {
        password: hashedPassword
      });
      
      if (updated) {
        // Invalidate all existing sessions for security
        await this.invalidateAllSessions(userId);
        
        // Log successful password reset
        await this.logAuditEvent(
          AuditEventType.PASSWORD_RESET,
          userId,
          true,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent
          }
        );
      }
      
      return !!updated;
    } catch (error) {
      console.error('Password reset error:', error);
      return false;
    }
  }
  
  /**
   * Change a user's password (requires current password)
   */
  async changePassword(
    userId: string, 
    currentPassword: string, 
    newPassword: string,
    metadata?: { ipAddress?: string; userAgent?: string }
  ): Promise<boolean> {
    try {
      const user = await this.userRepository.findById(userId);
      
      if (!user || !user.password) {
        await this.logAuditEvent(
          AuditEventType.PASSWORD_CHANGED,
          userId,
          false,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { reason: 'User not found or no password set' }
          }
        );
        
        return false;
      }
      
      const isCurrentPasswordValid = await compare(currentPassword, user.password);
      
      if (!isCurrentPasswordValid) {
        await this.logAuditEvent(
          AuditEventType.PASSWORD_CHANGED,
          userId,
          false,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { reason: 'Current password invalid' }
          }
        );
        
        return false;
      }
      
      // Validate password strength
      const validationResult = validatePassword(newPassword);
      if (!validationResult.isValid) {
        await this.logAuditEvent(
          AuditEventType.PASSWORD_CHANGED,
          userId,
          false,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { reason: 'Password too weak', errors: validationResult.errors }
          }
        );
        
        throw new Error(`Password is not strong enough: ${validationResult.errors.join(', ')}`);
      }
      
      // Hash new password
      const hashedPassword = await hash(newPassword, this.BCRYPT_ROUNDS);
      
      // Update password
      const updated = await this.userRepository.updateById(userId, {
        password: hashedPassword
      });
      
      if (updated) {
        await this.logAuditEvent(
          AuditEventType.PASSWORD_CHANGED,
          userId,
          true,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent
          }
        );
      }
      
      return !!updated;
    } catch (error) {
      console.error('Password change error:', error);
      return false;
    }
  }
  
  /**
   * Create a new session for a user
   */
  async createSession(userId: string, metadata?: { device?: string; ipAddress?: string }): Promise<UserSession> {
    try {
      // Generate JWT token
      const token = this.generateJWT(userId);
      
      // Calculate expiration date
      const expiresAt = new Date();
      if (this.config.tokenExpiresIn.endsWith('d')) {
        const days = parseInt(this.config.tokenExpiresIn.slice(0, -1));
        expiresAt.setDate(expiresAt.getDate() + days);
      } else if (this.config.tokenExpiresIn.endsWith('h')) {
        const hours = parseInt(this.config.tokenExpiresIn.slice(0, -1));
        expiresAt.setHours(expiresAt.getHours() + hours);
      } else {
        // Default to 1 day
        expiresAt.setDate(expiresAt.getDate() + 1);
      }
      
      // Create session in database
      const session = await this.sessionRepository.createSession({
        userId: userId as any,
        token,
        device: metadata?.device,
        ipAddress: metadata?.ipAddress,
        expiresAt,
        lastActive: new Date()
      });
      
      return this.sessionRepository.mapSessionToDTO(session);
    } catch (error) {
      console.error('Create session error:', error);
      throw new Error('Failed to create session');
    }
  }
  
  /**
   * Get all active sessions for a user
   */
  async getUserSessions(userId: string): Promise<UserSession[]> {
    try {
      const sessions = await this.sessionRepository.findSessionsByUser(userId);
      return sessions.map(session => this.sessionRepository.mapSessionToDTO(session));
    } catch (error) {
      console.error('Get user sessions error:', error);
      return [];
    }
  }
  
  /**
   * Invalidate a specific session (logout)
   */
  async invalidateSession(
    sessionId: string,
    userId?: string,
    metadata?: { ipAddress?: string; userAgent?: string }
  ): Promise<boolean> {
    try {
      const success = await this.sessionRepository.invalidateSession(sessionId);
      
      if (success && userId) {
        await this.logAuditEvent(
          AuditEventType.USER_LOGOUT,
          userId,
          true,
          { 
            ipAddress: metadata?.ipAddress,
            userAgent: metadata?.userAgent,
            details: { sessionId }
          }
        );
      }
      
      return success;
    } catch (error) {
      console.error('Invalidate session error:', error);
      return false;
    }
  }
  
  /**
   * Invalidate all sessions for a user (force logout from all devices)
   */
  async invalidateAllSessions(userId: string): Promise<boolean> {
    try {
      return await this.sessionRepository.invalidateAllUserSessions(userId);
    } catch (error) {
      console.error('Invalidate all sessions error:', error);
      return false;
    }
  }
  
  /**
   * Validate a token against active sessions
   */
  async validateToken(token: string): Promise<{ isValid: boolean; userId?: string }> {
    try {
      const session = await this.sessionRepository.findSessionByToken(token);
      
      if (!session || !session.isValid || session.expiresAt < new Date()) {
        return { isValid: false };
      }
      
      // Update last active timestamp
      await this.sessionRepository.updateSession(session.id, {
        lastActive: new Date()
      });
      
      return {
        isValid: true,
        userId: session.userId.toString()
      };
    } catch (error) {
      console.error('Validate token error:', error);
      return { isValid: false };
    }
  }
  
  /**
   * Generate a JWT token
   */
  private generateJWT(userId: string): string {
    const payload = { userId };
    const secret = this.config.jwtSecret;
    const options = { expiresIn: this.config.tokenExpiresIn };
    
    return jwt.sign(payload, secret, options);
  }
  
  /**
   * Create a verification token
   */
  private async createToken(userId: string, type: TokenType, email?: string): Promise<string> {
    // This would be implemented with a TokenRepository
    // For now, just generate a token
    return crypto.randomBytes(32).toString('hex');
  }
  
  /**
   * Verify a token
   */
  private async verifyToken(token: string, type: TokenType): Promise<{ userId: string; email?: string } | null> {
    // This would be implemented with a TokenRepository
    // For now, return null (token invalid)
    return null;
  }
  
  /**
   * Send verification email
   */
  private async sendVerificationEmail(user: UserDocument): Promise<void> {
    if (!this.config.emailService) {
      return;
    }
    
    // Create token
    const token = await this.createToken(user.id, TokenType.EMAIL_VERIFICATION);
    
    // Send email (implementation depends on email service)
    // this.config.emailService.sendVerificationEmail(user.email, token);
  }
  
  /**
   * Send password reset email
   */
  private async sendPasswordResetEmail(user: UserDocument, token: string): Promise<void> {
    if (!this.config.emailService) {
      return;
    }
    
    // Send email (implementation depends on email service)
    // this.config.emailService.sendPasswordResetEmail(user.email, token);
  }
  
  /**
   * Map a user document to a user profile DTO
   */
  private mapUserToProfile(user: UserDocument): UserProfileDTO {
    return {
      id: user.id,
      name: user.name,
      email: user.email,
      image: user.image,
      role: user.role,
      testMode: user.testMode,
      studentIds: user.studentIds?.map(id => id.toString()),
      parentIds: user.parentIds?.map(id => id.toString()),
      partnerIds: user.partnerIds?.map(id => id.toString()),
      preferences: user.preferences,
      createdAt: user.createdAt,
      updatedAt: user.updatedAt
    };
  }
  
  /**
   * Log an audit event if the audit log service is available
   */
  private async logAuditEvent(
    eventType: AuditEventType,
    userId?: string,
    success: boolean = true,
    metadata?: {
      targetUserId?: string;
      ipAddress?: string;
      userAgent?: string;
      details?: Record<string, any>;
    }
  ): Promise<void> {
    if (this.auditLogService) {
      try {
        await this.auditLogService.logEvent(eventType, userId, success, metadata);
      } catch (error) {
        console.error('Error logging audit event:', error);
      }
    }
  }
} 