import { AuthService } from './auth_service';
import { UserService } from './user_service';
import { ServiceManagementService } from './service_management_service';
import { PermissionService } from './permission_service';
import { AuditLogService } from './audit_log_service';
import { UserRelationshipService } from './user_relationship_service';
import { InvitationService } from './invitation_service';

// Export service creation functions
export const getAuthService = () => new AuthService();
export const getUserService = () => new UserService();
export const getServiceManagementService = () => new ServiceManagementService();
export const getPermissionService = () => new PermissionService();
export const getAuditLogService = () => new AuditLogService();
export const getUserRelationshipService = () => new UserRelationshipService();
export const getInvitationService = () => new InvitationService(); 