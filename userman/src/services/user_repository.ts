import mongoose from 'mongoose';
import { IUserRepository } from './interfaces';
import { UserDocument, getUserModel } from '../models/user_model';

/**
 * MongoDB implementation of the user repository
 * Follows Repository pattern for data access
 */
export class MongoUserRepository implements IUserRepository {
  private User: ReturnType<typeof getUserModel>;

  /**
   * Constructor initializes the User model
   */
  constructor() {
    this.User = getUserModel();
  }

  /**
   * Find a user by ID
   * @param id User ID
   * @returns User document or null if not found
   */
  async findById(id: string): Promise<UserDocument | null> {
    try {
      return await this.User.findById(id);
    } catch (error) {
      console.error('Error finding user by ID:', error);
      return null;
    }
  }

  /**
   * Find a user by email
   * @param email User email
   * @returns User document or null if not found
   */
  async findByEmail(email: string): Promise<UserDocument | null> {
    try {
      return await this.User.findByEmail(email);
    } catch (error) {
      console.error('Error finding user by email:', error);
      return null;
    }
  }

  /**
   * Create a new user
   * @param userData User data to create
   * @returns Created user document
   */
  async create(userData: Partial<UserDocument>): Promise<UserDocument> {
    try {
      const user = new this.User(userData);
      return await user.save();
    } catch (error) {
      console.error('Error creating user:', error);
      throw error;
    }
  }

  /**
   * Update a user
   * @param id User ID
   * @param userData User data to update
   * @returns Updated user document or null if not found
   */
  async update(id: string, userData: Partial<UserDocument>): Promise<UserDocument | null> {
    try {
      return await this.User.findByIdAndUpdate(
        id,
        { $set: userData },
        { new: true }
      );
    } catch (error) {
      console.error('Error updating user:', error);
      return null;
    }
  }

  /**
   * Delete a user
   * @param id User ID
   * @returns True if deleted, false otherwise
   */
  async delete(id: string): Promise<boolean> {
    try {
      const result = await this.User.findByIdAndDelete(id);
      return !!result;
    } catch (error) {
      console.error('Error deleting user:', error);
      return false;
    }
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
          return await this.User.findStudents(userId);
        case 'parents':
          return await this.User.findParents(userId);
        case 'partners':
          return await this.User.find({ partnerIds: userId });
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
      const UserModel = getUserModel();
      return await UserModel.find(filter || {}).exec();
    } catch (error) {
      console.error('Error finding all users:', error);
      throw new Error('Database error while finding users');
    }
  }
} 