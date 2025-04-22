import { Router } from 'express';
import { AdminController } from '../controllers/admin_controller';
import { PermissionService } from '../services/permission_service';
import { ResourceType, ActionType } from '../models/permission_model';
import express from 'express';
import { AuditController } from '../controllers/audit_controller';
import { IAuditLogService } from '../services/interfaces';
import { checkAdminRole } from '../middleware/auth_middleware';

// Create router
const router = Router();

// Create controller instance
const adminController = new AdminController();

// Create permission service for authorization middleware
const permissionService = new PermissionService();

// Create middleware for admin routes
const requireAdmin = permissionService.createAuthorizationMiddleware(
  ResourceType.User,
  ActionType.Manage
);

// Create middleware for support read-only access
const requireSupport = permissionService.createAuthorizationMiddleware(
  ResourceType.User,
  ActionType.Read
);

// Admin-only routes
router.get('/users', requireAdmin, adminController.getAllUsers);
router.get('/users/:id', requireAdmin, adminController.getUserDetails);
router.put('/users/:id/role', requireAdmin, adminController.updateUserRole);
router.put('/users/:id/test-mode', requireAdmin, adminController.toggleTestMode);
router.get('/users/test-mode', requireAdmin, adminController.getTestModeUsers);

// Service management routes
router.post('/services/access', requireAdmin, adminController.manageServiceAccess);

// Permission management routes
router.get('/permissions', requireAdmin, adminController.getAllPermissions);
router.put('/permissions/:role', requireAdmin, adminController.updateRolePermissions);

// Support read-only routes
router.get('/view/users', requireSupport, adminController.getAllUsers);
router.get('/view/users/:id', requireSupport, adminController.getUserDetails);
router.get('/view/permissions', requireSupport, adminController.getAllPermissions);

/**
 * Initialize admin routes
 */
export const initAdminRoutes = (
  router: express.Router,
  auditLogService: IAuditLogService
) => {
  const auditController = new AuditController(auditLogService);

  // Audit log routes (admin only)
  router.get(
    '/audit/logs',
    checkAdminRole,
    auditController.getAuditLogs.bind(auditController)
  );

  router.get(
    '/audit/logs/user/:userId',
    checkAdminRole,
    auditController.getUserAuditLogs.bind(auditController)
  );

  router.get(
    '/audit/logs/ip/:ipAddress',
    checkAdminRole,
    auditController.getIPSecurityEvents.bind(auditController)
  );

  return router;
};

export default router; 