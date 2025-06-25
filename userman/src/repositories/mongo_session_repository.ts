import { ISessionRepository } from '../services/interfaces';
import { UserSession } from '../services/interfaces';
import { MongoClient, Collection } from 'mongodb';

export class MongoSessionRepository implements ISessionRepository {
  private collection: Collection;
  private client: MongoClient;

  constructor() {
    this.client = new MongoClient('mongodb://localhost:27017');
    this.collection = this.client.db('userman').collection('sessions');
  }

  async createSession(sessionData: Partial<UserSession>): Promise<UserSession> {
    const session = {
      ...sessionData,
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours from now
    };
    await this.collection.insertOne(session);
    return this.mapSessionToDTO(session);
  }

  async findSessionByToken(token: string): Promise<UserSession | null> {
    const session = await this.collection.findOne({ id: token });
    if (!session) return null;
    return this.mapSessionToDTO(session);
  }

  async findSessionById(sessionId: string): Promise<UserSession | null> {
    const session = await this.collection.findOne({ id: sessionId });
    if (!session) return null;
    return this.mapSessionToDTO(session);
  }

  async findSessionsByUser(userId: string): Promise<UserSession[]> {
    const sessions = await this.collection.find({ userId }).toArray();
    return sessions.map(session => this.mapSessionToDTO(session));
  }

  async invalidateSession(sessionId: string): Promise<boolean> {
    const result = await this.collection.deleteOne({ id: sessionId });
    return result.deletedCount > 0;
  }

  async invalidateAllUserSessions(userId: string): Promise<boolean> {
    const result = await this.collection.deleteMany({ userId });
    return result.deletedCount > 0;
  }

  async updateSession(sessionId: string, data: Partial<UserSession>): Promise<UserSession> {
    const result = await this.collection.findOneAndUpdate(
      { id: sessionId },
      { $set: data },
      { returnDocument: 'after' }
    );
    if (!result) throw new Error('Session not found');
    return this.mapSessionToDTO(result);
  }

  async validateSession(token: string): Promise<boolean> {
    const session = await this.findSessionByToken(token);
    if (!session) return false;
    return new Date(session.expiresAt) > new Date();
  }

  mapSessionToDTO(session: any): UserSession {
    return {
      id: session.id,
      userId: session.userId,
      device: session.device,
      ipAddress: session.ipAddress,
      createdAt: new Date(session.createdAt),
      expiresAt: new Date(session.expiresAt)
    };
  }
} 