import { IUserRepository } from './interfaces';
import { UserDocument, UserModel } from '../models/user_model';
import mongoose from 'mongoose';
import { NotFoundError } from '../utils/errors';

/**
 * MongoDB implementation of the user repository
 * Follows Repository pattern for data access
 */
export class MongoUserRepository implements IUserRepository {
  private User: UserModel;

  /**
   * Constructor initializes the User model
   */
  constructor() {
    this.User = mongoose.model<UserDocument, UserModel>('User');
  }

  /**
   * Find a user by ID
   * @param id User ID
   * @returns User document or null if not found
   */
  async findById(id: string): Promise<UserDocument | null> {
    return this.User.findById(id);
  }

  /**
   * Find a user by email
   * @param email User email
   * @returns User document or null if not found
   */
  async findByEmail(email: string): Promise<UserDocument | null> {
    return this.User.findByEmail(email);
  }

  /**
   * Create a new user
   * @param data User data to create
   * @returns Created user document
   */
  async create(data: Partial<UserDocument>): Promise<UserDocument> {
    const user = new this.User(data);
    return user.save();
  }

  /**
   * Update a user
   * @param id User ID
   * @param data User data to update
   * @returns Updated user document or null if not found
   */
  async update(id: string, data: Partial<UserDocument>): Promise<UserDocument> {
    const user = await this.User.findByIdAndUpdate(id, data, { new: true });
    if (!user) {
      throw new NotFoundError('User not found');
    }
    return user;
  }

  /**
   * Delete a user
   * @param id User ID
   * @returns True if deleted, false otherwise
   */
  async delete(id: string): Promise<boolean> {
    const result = await this.User.findByIdAndDelete(id);
    return !!result;
  }

  /**
   * Find linked users
   * @param userId User ID
   * @param relationship Relationship type ('students', 'parents', 'partners')
   * @returns Array of linked users
   */
  async findLinkedUsers(userId: string, relationship: string): Promise<UserDocument[]> {
    try {
      switch (relationship) {
        case 'students':
          return await this.findStudents(userId);
        case 'parents':
          return await this.findParents(userId);
        case 'partners':
          const user = await this.findById(userId);
          if (!user || !user.partnerIds) return [];
          return await this.findByIds(user.partnerIds.map(id => id.toString()));
        default:
          return [];
      }
    } catch (error) {
      console.error(`Error finding ${relationship}:`, error);
      return [];
    }
  }

  /**
   * Search users by query
   * @param query Search query
   * @param excludeId ID to exclude from results
   * @param limit Maximum number of results (default 10)
   * @returns Array of matching users
   */
  async search(query: string, excludeId?: string, limit: number = 10): Promise<UserDocument[]> {
    try {
      const searchQuery: any = {
        $or: [
          { name: { $regex: query, $options: 'i' } },
          { email: { $regex: query, $options: 'i' } }
        ]
      };

      if (excludeId) {
        searchQuery._id = { $ne: new mongoose.Types.ObjectId(excludeId) };
      }

      return await this.User.find(searchQuery).limit(limit);
    } catch (error) {
      console.error('Error searching users:', error);
      return [];
    }
  }

  /**
   * Find all users with optional filter
   * @param filter Optional filter to apply
   * @returns Array of users matching the filter
   */
  async findAll(filter?: Partial<UserDocument>): Promise<UserDocument[]> {
    try {
      return await this.User.find(filter || {}).exec();
    } catch (error) {
      console.error('Error finding all users:', error);
      throw new Error('Database error while finding users');
    }
  }

  /**
   * Get the user model
   * @returns The user model
   */
  getUserModel(): UserModel {
    return this.User;
  }

  async updatePassword(id: string, hashedPassword: string): Promise<UserDocument> {
    const user = await this.User.findByIdAndUpdate(
      id,
      { password: hashedPassword },
      { new: true }
    );

    if (!user) {
      throw new NotFoundError('User not found');
    }

    return user;
  }

  async updatePreferences(id: string, preferences: any): Promise<UserDocument> {
    const user = await this.User.findByIdAndUpdate(
      id,
      { preferences },
      { new: true }
    );

    if (!user) {
      throw new NotFoundError('User not found');
    }

    return user;
  }

  async findByIds(ids: string[]): Promise<UserDocument[]> {
    return this.User.find({ _id: { $in: ids } });
  }

  async findByRole(role: string): Promise<UserDocument[]> {
    return this.User.find({ role });
  }

  async findByRoles(roles: string[]): Promise<UserDocument[]> {
    return this.User.find({ role: { $in: roles } });
  }

  async findByService(serviceName: string): Promise<UserDocument[]> {
    return this.User.find({ services: serviceName });
  }

  async findByServiceAndRole(serviceName: string, role: string): Promise<UserDocument[]> {
    return this.User.find({ services: serviceName, role });
  }

  async findByServiceAndRoles(serviceName: string, roles: string[]): Promise<UserDocument[]> {
    return this.User.find({ services: serviceName, role: { $in: roles } });
  }

  async findStudents(userId: string): Promise<UserDocument[]> {
    const user = await this.findById(userId);
    if (!user || !user.studentIds || user.studentIds.length === 0) {
      return [];
    }
    return this.findByIds(user.studentIds.map(id => id.toString()));
  }

  async findParents(userId: string): Promise<UserDocument[]> {
    const user = await this.findById(userId);
    if (!user || !user.parentIds || user.parentIds.length === 0) {
      return [];
    }
    return this.findByIds(user.parentIds.map(id => id.toString()));
  }

  async findPartners(userId: string): Promise<UserDocument[]> {
    const user = await this.findById(userId);
    if (!user || !user.partnerIds || user.partnerIds.length === 0) {
      return [];
    }
    return this.findByIds(user.partnerIds.map(id => id.toString()));
  }
} 