import { AuthService } from './auth_service';
import { UserService } from './user_service';
import { ServiceManagementService } from './service_management_service';
import { PermissionService } from './permission_service';
import { AuditLogService } from './audit_log_service';
import { UserRelationshipService } from './user_relationship_service';
import { InvitationService } from './invitation_service';
import { MongoUserRepository } from '../repositories/mongo_user_repository';
import { MongoSessionRepository } from '../repositories/mongo_session_repository';

// Export service creation functions
export const getAuthService = () => {
  const userRepository = new MongoUserRepository();
  const sessionRepository = new MongoSessionRepository();
  const auditLogService = new AuditLogService();
  
  return new AuthService(
    userRepository,
    sessionRepository,
    {
      emailVerificationRequired: false,
      maxLoginAttempts: 5,
      lockoutDuration: 30
    },
    auditLogService
  );
};
export const getUserService = () => new UserService();
export const getServiceManagementService = () => new ServiceManagementService();
export const getPermissionService = () => new PermissionService();
export const getAuditLogService = () => new AuditLogService();
export const getUserRelationshipService = () => new UserRelationshipService();
export const getInvitationService = () => new InvitationService(); 