import mongoose from 'mongoose';
import { SessionDocument, getSessionModel } from '../models/session_model';
import { UserSession } from './interfaces';

/**
 * Session repository interface
 */
export interface ISessionRepository {
  createSession(session: Partial<SessionDocument>): Promise<SessionDocument>;
  findSessionById(id: string): Promise<SessionDocument | null>;
  findSessionByToken(token: string): Promise<SessionDocument | null>;
  findSessionsByUser(userId: string): Promise<SessionDocument[]>;
  updateSession(id: string, data: Partial<SessionDocument>): Promise<SessionDocument | null>;
  invalidateSession(id: string): Promise<boolean>;
  invalidateAllUserSessions(userId: string): Promise<boolean>;
}

/**
 * MongoDB implementation of the session repository
 */
export class MongoSessionRepository implements ISessionRepository {
  private Session: ReturnType<typeof getSessionModel>;

  constructor() {
    this.Session = getSessionModel();
  }

  /**
   * Create a new session
   */
  async createSession(session: Partial<SessionDocument>): Promise<SessionDocument> {
    try {
      const newSession = new this.Session(session);
      return await newSession.save();
    } catch (error) {
      console.error('Error creating session:', error);
      throw new Error('Failed to create session');
    }
  }

  /**
   * Find a session by ID
   */
  async findSessionById(id: string): Promise<SessionDocument | null> {
    try {
      return await this.Session.findById(id);
    } catch (error) {
      console.error('Error finding session by id:', error);
      return null;
    }
  }

  /**
   * Find a session by token
   */
  async findSessionByToken(token: string): Promise<SessionDocument | null> {
    try {
      return await this.Session.findByToken(token);
    } catch (error) {
      console.error('Error finding session by token:', error);
      return null;
    }
  }

  /**
   * Find all active sessions for a user
   */
  async findSessionsByUser(userId: string): Promise<SessionDocument[]> {
    try {
      return await this.Session.findActiveSessionsByUser(userId);
    } catch (error) {
      console.error('Error finding sessions by user:', error);
      return [];
    }
  }

  /**
   * Update a session
   */
  async updateSession(id: string, data: Partial<SessionDocument>): Promise<SessionDocument | null> {
    try {
      return await this.Session.findByIdAndUpdate(
        id,
        { $set: data },
        { new: true }
      );
    } catch (error) {
      console.error('Error updating session:', error);
      return null;
    }
  }

  /**
   * Invalidate a session (logout)
   */
  async invalidateSession(id: string): Promise<boolean> {
    try {
      return await this.Session.invalidateSession(id);
    } catch (error) {
      console.error('Error invalidating session:', error);
      return false;
    }
  }

  /**
   * Invalidate all sessions for a user (force logout from all devices)
   */
  async invalidateAllUserSessions(userId: string): Promise<boolean> {
    try {
      return await this.Session.invalidateUserSessions(userId);
    } catch (error) {
      console.error('Error invalidating user sessions:', error);
      return false;
    }
  }

  /**
   * Map a session document to the UserSession interface
   */
  mapSessionToDTO(session: SessionDocument): UserSession {
    return {
      id: session._id.toString(),
      userId: session.userId.toString(),
      token: session.token,
      device: session.device,
      ipAddress: session.ipAddress,
      lastActive: session.lastActive,
      expiresAt: session.expiresAt,
      isValid: session.isValid
    };
  }
} 