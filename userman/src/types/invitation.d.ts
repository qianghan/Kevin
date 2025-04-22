import mongoose from 'mongoose';
import { InvitationDocument } from '../models/invitation_model';

declare module 'mongoose' {
  interface Model<T> {
    findPendingByEmailAndInviter?(email: string, inviterId: string): Promise<InvitationDocument | null>;
    findPendingByEmail?(email: string): Promise<InvitationDocument[]>;
    findExpired?(): Promise<InvitationDocument[]>;
  }
} 