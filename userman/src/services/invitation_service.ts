import { IInvitationService, InvitationDTO } from './interfaces';
import { InvitationStatus, RelationshipType, InvitationModel } from '../models/invitation_model';
import mongoose from 'mongoose';
import { generateRandomToken } from '../utils/crypto';
import { NotFoundError, ValidationError, AuthorizationError } from '../utils/errors';
import { UserRelationshipService } from './user_relationship_service';

// Get UserModel directly from mongoose
const UserModel = mongoose.model('User');

export class InvitationService implements IInvitationService {
  async createInvitation(
    inviterId: string,
    email: string,
    relationship: RelationshipType,
    message?: string,
    expiresIn: number = 72
  ): Promise<{ id: string; token: string }> {
    // Find the inviter to get their name
    const inviter = await UserModel.findById(inviterId);
    if (!inviter) {
      throw new NotFoundError('Inviter not found');
    }

    // Check if there's already a pending invitation for this email from this inviter
    const existingInvitation = await InvitationModel.findOne({
      email,
      inviterId,
      status: InvitationStatus.PENDING
    });
    
    if (existingInvitation) {
      throw new ValidationError('A pending invitation already exists for this email');
    }

    // Generate a unique token
    const token = generateRandomToken();
    
    // Calculate expiration date
    const expiresAt = new Date();
    expiresAt.setHours(expiresAt.getHours() + expiresIn);

    // Create new invitation
    const invitation = new InvitationModel({
      email,
      inviterId,
      inviterName: inviter.fullName || `${inviter.firstName} ${inviter.lastName}`,
      inviterEmail: inviter.email,
      inviterRole: inviter.role,
      relationship,
      status: InvitationStatus.PENDING,
      token,
      message,
      expiresAt,
    });

    await invitation.save();
    return { id: invitation._id.toString(), token };
  }

  async getInvitationByToken(token: string): Promise<InvitationDTO | null> {
    const invitation = await InvitationModel.findOne({ token });
    return invitation ? this.mapToDTO(invitation) : null;
  }

  async getInvitationsByInviter(userId: string): Promise<InvitationDTO[]> {
    const invitations = await InvitationModel.find({ inviterId: userId });
    return invitations.map((invitation: any) => this.mapToDTO(invitation));
  }

  async getInvitationsByEmail(email: string): Promise<InvitationDTO[]> {
    const invitations = await InvitationModel.find({ email });
    return invitations.map((invitation: any) => this.mapToDTO(invitation));
  }

  async getPendingInvitationsByEmail(email: string): Promise<InvitationDTO[]> {
    const invitations = await InvitationModel.find({
      email,
      status: InvitationStatus.PENDING
    });
    return invitations.map((invitation: any) => this.mapToDTO(invitation));
  }

  async acceptInvitation(token: string, userId: string): Promise<InvitationDTO> {
    const invitation = await InvitationModel.findOne({ token });
    if (!invitation) {
      throw new NotFoundError('Invitation not found');
    }

    if (invitation.status !== InvitationStatus.PENDING) {
      throw new ValidationError(`Invitation is ${invitation.status}, not pending`);
    }

    if (invitation.expiresAt < new Date()) {
      invitation.status = InvitationStatus.EXPIRED;
      await invitation.save();
      throw new ValidationError('Invitation has expired');
    }

    // Update invitation
    invitation.status = InvitationStatus.ACCEPTED;
    invitation.acceptedById = new mongoose.Types.ObjectId(userId);
    invitation.acceptedAt = new Date();
    await invitation.save();

    // Establish the relationship between users
    const relationshipService = new UserRelationshipService();
    try {
      await relationshipService.establishRelationshipFromInvitation(
        userId,
        invitation.inviterId.toString(),
        invitation.relationship
      );
    } catch (error) {
      // Log error but don't fail the invitation acceptance
      console.error('Failed to establish relationship:', error);
    }

    return this.mapToDTO(invitation);
  }

  async rejectInvitation(token: string): Promise<InvitationDTO> {
    const invitation = await InvitationModel.findOne({ token });
    if (!invitation) {
      throw new NotFoundError('Invitation not found');
    }

    if (invitation.status !== InvitationStatus.PENDING) {
      throw new ValidationError(`Invitation is ${invitation.status}, not pending`);
    }

    invitation.status = InvitationStatus.REJECTED;
    invitation.rejectedAt = new Date();
    await invitation.save();

    return this.mapToDTO(invitation);
  }

  async cancelInvitation(invitationId: string, inviterId: string): Promise<boolean> {
    const invitation = await InvitationModel.findById(invitationId);
    if (!invitation) {
      throw new NotFoundError('Invitation not found');
    }

    // Only the inviter can cancel the invitation
    if (invitation.inviterId.toString() !== inviterId) {
      throw new AuthorizationError('Only the inviter can cancel this invitation');
    }

    if (invitation.status !== InvitationStatus.PENDING) {
      throw new ValidationError(`Cannot cancel invitation with status: ${invitation.status}`);
    }

    invitation.status = InvitationStatus.CANCELLED;
    await invitation.save();

    return true;
  }

  async expireInvitations(): Promise<number> {
    const now = new Date();
    const result = await InvitationModel.updateMany(
      {
        status: InvitationStatus.PENDING,
        expiresAt: { $lt: now }
      },
      {
        $set: { status: InvitationStatus.EXPIRED }
      }
    );

    return result.modifiedCount;
  }

  private mapToDTO(invitation: any): InvitationDTO {
    return {
      id: invitation._id.toString(),
      email: invitation.email,
      inviterId: invitation.inviterId.toString(),
      inviterName: invitation.inviterName,
      inviterEmail: invitation.inviterEmail,
      inviterRole: invitation.inviterRole,
      relationship: invitation.relationship,
      status: invitation.status,
      message: invitation.message,
      expiresAt: invitation.expiresAt,
      createdAt: invitation.createdAt,
      updatedAt: invitation.updatedAt,
      acceptedById: invitation.acceptedById?.toString(),
      acceptedAt: invitation.acceptedAt,
      rejectedAt: invitation.rejectedAt,
    };
  }
} 