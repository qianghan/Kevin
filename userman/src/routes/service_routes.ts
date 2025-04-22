import express from 'express';
import { ServiceController } from '../controllers/service_controller';
import { authenticate } from '../middleware/auth_middleware';
import { validateServiceAccess } from '../middleware/service_auth_middleware';
import { getAuthService } from '../services';

const router = express.Router();
const serviceController = new ServiceController();
const authService = getAuthService();

/**
 * Routes for service access and management
 */

// Get all services the authenticated user has access to
router.get(
  '/user-services',
  authenticate(authService),
  serviceController.getUserServices.bind(serviceController)
);

// Check if user has access to a specific service
router.get(
  '/access/:serviceName',
  authenticate(authService),
  serviceController.checkServiceAccess.bind(serviceController)
);

// Check if parent has access to student's service
router.get(
  '/student/:studentId/access/:serviceName',
  authenticate(authService),
  serviceController.checkParentStudentServiceAccess.bind(serviceController)
);

// Admin only: Get all services with details
router.get(
  '/all',
  authenticate(authService),
  serviceController.getAllServices.bind(serviceController)
);

export default router; 