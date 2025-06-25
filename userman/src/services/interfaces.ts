import { UserDocument, UserPreferences, UserRole } from '../models/user_model';
import { RelationshipType, InvitationStatus } from '../models/invitation_model';

/**
 * User profile data transfer object
 */
export interface UserProfileDTO {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  emailVerified?: boolean;
  createdAt?: Date;
  updatedAt?: Date;
}

/**
 * User profile update data transfer object
 */
export interface UserProfileUpdateDTO {
  firstName?: string;
  lastName?: string;
  email?: string;
  password?: string;
}

/**
 * User session interface
 */
export interface UserSession {
  id: string;
  userId: string;
  createdAt: Date;
  expiresAt: Date;
  device?: string;
  ipAddress?: string;
  userAgent?: string;
}

/**
 * User authentication service interface
 * Handles user authentication and token generation
 */
export interface IAuthenticationService {
  /**
   * Authenticate a user with email and password
   */
  authenticate(email: string, password: string, metadata?: { device?: string; ipAddress?: string; userAgent?: string }): Promise<{ user: UserProfileDTO; token: string }>;
  
  /**
   * Register a new user
   */
  register(userData: Partial<UserProfileDTO>, password: string, metadata?: { ipAddress?: string; userAgent?: string }): Promise<UserProfileDTO>;
  
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
  resetPassword(token: string, newPassword: string, metadata?: { ipAddress?: string; userAgent?: string }): Promise<boolean>;
  
  /**
   * Change a user's password (requires current password)
   */
  changePassword(userId: string, currentPassword: string, newPassword: string, metadata?: { ipAddress?: string; userAgent?: string }): Promise<boolean>;

  /**
   * Create a new session for a user
   */
  createSession(userId: string, metadata?: { device?: string, ipAddress?: string }): Promise<UserSession>;

  /**
   * Get all active sessions for a user
   */
  getUserSessions(userId: string): Promise<UserSession[]>;

  /**
   * Invalidate a specific session (logout)
   */
  invalidateSession(sessionId: string): Promise<boolean>;

  /**
   * Invalidate all sessions for a user (force logout from all devices)
   */
  invalidateAllSessions(userId: string): Promise<boolean>;

  /**
   * Validate a token against active sessions
   */
  validateToken(token: string): Promise<{ isValid: boolean; userId?: string }>;
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
 * Admin service interface
 * Handles administrative operations
 */
export interface IAdminService {
  /**
   * Get all users with optional filtering
   */
  getAllUsers(filter?: Partial<UserProfileDTO>): Promise<UserProfileDTO[]>;
  
  /**
   * Toggle test mode for a user
   */
  setTestMode(userId: string, enabled: boolean): Promise<UserProfileDTO>;
  
  /**
   * Get all users in test mode
   */
  getTestModeUsers(): Promise<UserProfileDTO[]>;
  
  /**
   * Force logout a user
   */
  forceLogout(userId: string): Promise<boolean>;
  
  /**
   * Disable a user account
   */
  disableAccount(userId: string): Promise<boolean>;
  
  /**
   * Enable a user account
   */
  enableAccount(userId: string): Promise<boolean>;
}

/**
 * Comprehensive user service interface
 * Combines all user-related service interfaces
 */
export interface IUserService extends IAuthenticationService, IUserProfileService, IUserRelationshipService, IAdminService {
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
  create(user: Partial<UserDocument>): Promise<UserDocument>;
  
  /**
   * Update a user
   */
  update(id: string, data: Partial<UserDocument>): Promise<UserDocument>;
  
  /**
   * Delete a user
   */
  delete(id: string): Promise<boolean>;
  
  /**
   * Get the user model
   */
  getUserModel(): any;

  /**
   * Update a user's password
   */
  updatePassword(id: string, hashedPassword: string): Promise<UserDocument>;

  /**
   * Update user preferences
   */
  updatePreferences(id: string, preferences: Partial<UserPreferences>): Promise<UserPreferences>;
}

/**
 * Session repository interface
 */
export interface ISessionRepository {
  /**
   * Create a new session
   */
  createSession(sessionData: Partial<UserSession>): Promise<UserSession>;
  
  /**
   * Find a session by token
   */
  findSessionByToken(token: string): Promise<UserSession | null>;
  
  /**
   * Find all sessions for a user
   */
  findSessionsByUser(userId: string): Promise<UserSession[]>;
  
  /**
   * Invalidate a session by ID
   */
  invalidateSession(sessionId: string): Promise<boolean>;
  
  /**
   * Invalidate all sessions for a user
   */
  invalidateAllUserSessions(userId: string): Promise<boolean>;
  
  /**
   * Update a session
   */
  updateSession(sessionId: string, data: Partial<UserSession>): Promise<UserSession | null>;
  
  /**
   * Map a session document to DTO
   */
  mapSessionToDTO(session: UserSession): UserSession;
}

/**
 * Interface for invitation service
 */
export interface IInvitationService {
  /**
   * Create a new invitation
   * @param inviterId ID of the user sending the invitation
   * @param email Email of the recipient
   * @param relationship Type of relationship being established
   * @param message Optional message to include in the invitation
   * @param expiresIn Optional expiration time in hours (default 72)
   */
  createInvitation(
    inviterId: string,
    email: string,
    relationship: RelationshipType,
    message?: string,
    expiresIn?: number
  ): Promise<{ id: string; token: string }>;

  /**
   * Get invitation by token
   * @param token Unique invitation token
   */
  getInvitationByToken(token: string): Promise<InvitationDTO | null>;

  /**
   * Get all invitations sent by a user
   * @param userId ID of the inviter
   */
  getInvitationsByInviter(userId: string): Promise<InvitationDTO[]>;

  /**
   * Get all invitations received by an email
   * @param email Email of the recipient
   */
  getInvitationsByEmail(email: string): Promise<InvitationDTO[]>;

  /**
   * Get all pending invitations for an email
   * @param email Email of the recipient
   */
  getPendingInvitationsByEmail(email: string): Promise<InvitationDTO[]>;

  /**
   * Accept an invitation
   * @param token Invitation token
   * @param userId ID of the user accepting the invitation
   */
  acceptInvitation(token: string, userId: string): Promise<InvitationDTO>;

  /**
   * Reject an invitation
   * @param token Invitation token
   */
  rejectInvitation(token: string): Promise<InvitationDTO>;

  /**
   * Cancel an invitation (by the original sender)
   * @param invitationId ID of the invitation
   * @param inviterId ID of the user who sent the invitation
   */
  cancelInvitation(invitationId: string, inviterId: string): Promise<boolean>;

  /**
   * Expire all pending invitations that have passed their expiration date
   */
  expireInvitations(): Promise<number>;
}

/**
 * Data Transfer Object for Invitation
 */
export interface InvitationDTO {
  id: string;
  email: string;
  inviterId: string;
  inviterName: string;
  inviterEmail: string;
  inviterRole: string;
  relationship: RelationshipType;
  status: InvitationStatus;
  message?: string;
  expiresAt: Date;
  createdAt: Date;
  updatedAt: Date;
  acceptedById?: string;
  acceptedAt?: Date;
  rejectedAt?: Date;
}

/**
 * Audit log event types for sensitive operations
 */
export enum AuditEventType {
  USER_LOGIN = 'user_login',
  USER_LOGIN_FAILED = 'user_login_failed',
  USER_LOGOUT = 'user_logout',
  USER_CREATED = 'user_created',
  USER_UPDATED = 'user_updated',
  USER_DELETED = 'user_deleted',
  PASSWORD_RESET_REQUESTED = 'password_reset_requested',
  PASSWORD_RESET = 'password_reset',
  PASSWORD_CHANGED = 'password_changed',
  EMAIL_VERIFIED = 'email_verified',
  EMAIL_CHANGED = 'email_changed',
  ACCOUNT_LOCKED = 'account_locked',
  ACCOUNT_UNLOCKED = 'account_unlocked',
  RELATIONSHIP_ADDED = 'relationship_added',
  RELATIONSHIP_REMOVED = 'relationship_removed',
  INVITATION_CREATED = 'invitation_created',
  INVITATION_ACCEPTED = 'invitation_accepted',
  INVITATION_REJECTED = 'invitation_rejected',
  INVITATION_CANCELLED = 'invitation_cancelled',
  ADMIN_ACTION = 'admin_action',
  SESSION_CREATED = 'session_created',
  SESSION_INVALIDATED = 'session_invalidated',
  ALL_SESSIONS_INVALIDATED = 'all_sessions_invalidated'
}

/**
 * Audit log entry data transfer object
 */
export interface AuditLogEntryDTO {
  id: string;
  timestamp: Date;
  userId?: string;
  targetUserId?: string;
  eventType: AuditEventType;
  ipAddress?: string;
  userAgent?: string;
  details?: Record<string, any>;
  success: boolean;
}

/**
 * Audit log service interface
 * Handles logging of security-relevant events for audit purposes
 */
export interface IAuditLogService {
  /**
   * Log an audit event
   * @param eventType Type of event being logged
   * @param userId ID of the user performing the action (if available)
   * @param success Whether the operation was successful
   * @param metadata Additional metadata about the event
   */
  logEvent(
    eventType: AuditEventType,
    userId?: string,
    success?: boolean,
    metadata?: {
      targetUserId?: string;
      ipAddress?: string;
      userAgent?: string;
      details?: Record<string, any>;
    }
  ): Promise<void>;

  /**
   * Get audit log entries for a specific user
   * @param userId ID of the user
   * @param limit Maximum number of entries to return
   * @param offset Number of entries to skip
   */
  getUserAuditLog(userId: string, limit?: number, offset?: number): Promise<AuditLogEntryDTO[]>;

  /**
   * Get all audit log entries
   * @param filter Optional filter criteria
   * @param limit Maximum number of entries to return
   * @param offset Number of entries to skip
   */
  getAuditLog(
    filter?: {
      eventTypes?: AuditEventType[];
      startDate?: Date;
      endDate?: Date;
      userId?: string;
      success?: boolean;
    },
    limit?: number,
    offset?: number
  ): Promise<AuditLogEntryDTO[]>;

  /**
   * Get security events for a specific IP address
   * @param ipAddress IP address to check
   * @param limit Maximum number of entries to return
   */
  getIPSecurityEvents(ipAddress: string, limit?: number): Promise<AuditLogEntryDTO[]>;
} 