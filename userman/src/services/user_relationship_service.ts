import { IUserRelationshipService, UserProfileDTO } from './interfaces';
import mongoose from 'mongoose';
import { NotFoundError, ValidationError, AuthorizationError } from '../utils/errors';
import { RelationshipType } from '../models/invitation_model';

// Get models directly from mongoose
const UserModel = mongoose.model('User');

export class UserRelationshipService implements IUserRelationshipService {
  /**
   * Link one user to another based on relationship type
   */
  async linkAccounts(
    userId: string, 
    targetUserId: string, 
    relationship: 'student' | 'parent' | 'partner'
  ): Promise<boolean> {
    // Verify both users exist
    const [user, targetUser] = await Promise.all([
      UserModel.findById(userId),
      UserModel.findById(targetUserId)
    ]);

    if (!user) {
      throw new NotFoundError('User not found');
    }

    if (!targetUser) {
      throw new NotFoundError('Target user not found');
    }

    // Prevent self-linking
    if (userId === targetUserId) {
      throw new ValidationError('Cannot link a user to themselves');
    }

    // Check if the link already exists
    switch (relationship) {
      case 'student':
        if (user.studentIds?.includes(targetUserId)) {
          throw new ValidationError('This student is already linked to this account');
        }
        
        // Add student to user and parent to target
        await Promise.all([
          UserModel.findByIdAndUpdate(userId, { $addToSet: { studentIds: targetUserId } }),
          UserModel.findByIdAndUpdate(targetUserId, { $addToSet: { parentIds: userId } })
        ]);
        break;

      case 'parent':
        if (user.parentIds?.includes(targetUserId)) {
          throw new ValidationError('This parent is already linked to this account');
        }
        
        // Add parent to user and student to target
        await Promise.all([
          UserModel.findByIdAndUpdate(userId, { $addToSet: { parentIds: targetUserId } }),
          UserModel.findByIdAndUpdate(targetUserId, { $addToSet: { studentIds: userId } })
        ]);
        break;

      case 'partner':
        if (user.partnerIds?.includes(targetUserId)) {
          throw new ValidationError('This partner is already linked to this account');
        }
        
        // Add partner to both users (bidirectional relationship)
        await Promise.all([
          UserModel.findByIdAndUpdate(userId, { $addToSet: { partnerIds: targetUserId } }),
          UserModel.findByIdAndUpdate(targetUserId, { $addToSet: { partnerIds: userId } })
        ]);
        break;

      default:
        throw new ValidationError('Invalid relationship type');
    }

    return true;
  }

  /**
   * Unlink one user from another
   */
  async unlinkAccounts(
    userId: string, 
    targetUserId: string, 
    relationship: 'student' | 'parent' | 'partner'
  ): Promise<boolean> {
    // Verify both users exist
    const [user, targetUser] = await Promise.all([
      UserModel.findById(userId),
      UserModel.findById(targetUserId)
    ]);

    if (!user) {
      throw new NotFoundError('User not found');
    }

    if (!targetUser) {
      throw new NotFoundError('Target user not found');
    }

    // Check if the link exists before removing
    switch (relationship) {
      case 'student':
        if (!user.studentIds?.includes(targetUserId)) {
          throw new ValidationError('This student is not linked to this account');
        }
        
        // Remove student from user and parent from target
        await Promise.all([
          UserModel.findByIdAndUpdate(userId, { $pull: { studentIds: targetUserId } }),
          UserModel.findByIdAndUpdate(targetUserId, { $pull: { parentIds: userId } })
        ]);
        break;

      case 'parent':
        if (!user.parentIds?.includes(targetUserId)) {
          throw new ValidationError('This parent is not linked to this account');
        }
        
        // Remove parent from user and student from target
        await Promise.all([
          UserModel.findByIdAndUpdate(userId, { $pull: { parentIds: targetUserId } }),
          UserModel.findByIdAndUpdate(targetUserId, { $pull: { studentIds: userId } })
        ]);
        break;

      case 'partner':
        if (!user.partnerIds?.includes(targetUserId)) {
          throw new ValidationError('This partner is not linked to this account');
        }
        
        // Remove partner from both users
        await Promise.all([
          UserModel.findByIdAndUpdate(userId, { $pull: { partnerIds: targetUserId } }),
          UserModel.findByIdAndUpdate(targetUserId, { $pull: { partnerIds: userId } })
        ]);
        break;

      default:
        throw new ValidationError('Invalid relationship type');
    }

    return true;
  }

  /**
   * Get users linked to this user by relationship type
   */
  async getLinkedUsers(
    userId: string, 
    relationship: 'students' | 'parents' | 'partners'
  ): Promise<UserProfileDTO[]> {
    const user = await UserModel.findById(userId);
    
    if (!user) {
      throw new NotFoundError('User not found');
    }
    
    let linkedUserIds: string[] = [];
    
    switch (relationship) {
      case 'students':
        linkedUserIds = user.studentIds || [];
        break;
      case 'parents':
        linkedUserIds = user.parentIds || [];
        break;
      case 'partners':
        linkedUserIds = user.partnerIds || [];
        break;
      default:
        throw new ValidationError('Invalid relationship type');
    }
    
    if (linkedUserIds.length === 0) {
      return [];
    }
    
    // Convert string IDs to ObjectIds
    const objectIds = linkedUserIds.map(id => new mongoose.Types.ObjectId(id));
    
    // Find all users with these IDs
    const linkedUsers = await UserModel.find({ _id: { $in: objectIds } });
    
    // Map to DTOs
    return linkedUsers.map(user => this.mapToDTO(user));
  }

  /**
   * Search for users to link accounts
   */
  async searchUsers(query: string, excludeUserId?: string): Promise<UserProfileDTO[]> {
    if (!query || query.length < 3) {
      throw new ValidationError('Search query must be at least 3 characters');
    }
    
    // Create a case-insensitive regex search for name or email
    const searchConditions = {
      $or: [
        { email: { $regex: query, $options: 'i' } },
        { firstName: { $regex: query, $options: 'i' } },
        { lastName: { $regex: query, $options: 'i' } }
      ]
    };
    
    // Exclude the current user if provided
    if (excludeUserId) {
      Object.assign(searchConditions, { _id: { $ne: excludeUserId } });
    }
    
    const users = await UserModel.find(searchConditions).limit(10);
    
    return users.map(user => this.mapToDTO(user));
  }

  /**
   * Update relationship based on accepted invitation
   */
  async establishRelationshipFromInvitation(
    userId: string,
    inviterId: string,
    relationship: RelationshipType
  ): Promise<boolean> {
    // Map RelationshipType to our internal relationship types
    switch (relationship) {
      case RelationshipType.ParentToStudent:
        // Inviter is parent, userId is student
        return this.linkAccounts(inviterId, userId, 'student');
        
      case RelationshipType.CoParent:
        // Both are partners
        return this.linkAccounts(inviterId, userId, 'partner');
        
      case RelationshipType.TeacherToStudent:
        // We could handle this differently or extend the relationship types
        // For now, treat teachers like parents in terms of relationship
        return this.linkAccounts(inviterId, userId, 'student');
        
      case RelationshipType.AdminToUser:
        // This might need special handling outside the normal relationships
        throw new ValidationError('Admin relationships must be handled separately');
        
      default:
        throw new ValidationError('Unsupported relationship type');
    }
  }

  /**
   * Map a user document to a UserProfileDTO
   */
  private mapToDTO(user: any): UserProfileDTO {
    return {
      id: user._id.toString(),
      name: user.fullName || `${user.firstName} ${user.lastName}`,
      email: user.email,
      image: user.image,
      role: user.role,
      testMode: user.testMode,
      studentIds: user.studentIds?.map((id: any) => id.toString()) || [],
      parentIds: user.parentIds?.map((id: any) => id.toString()) || [],
      partnerIds: user.partnerIds?.map((id: any) => id.toString()) || [],
      preferences: user.preferences,
      createdAt: user.createdAt,
      updatedAt: user.updatedAt
    };
  }
} 