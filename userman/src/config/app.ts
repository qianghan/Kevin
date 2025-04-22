import express from 'express';
import mongoose from 'mongoose';
import cors from 'cors';
import helmet from 'helmet';
import { AuthService } from '../services/auth_service';
import { AuditLogService } from '../services/audit_log_service';
import userRouter from '../routes/user_routes';
import authRouter from '../routes/auth_routes';
import serviceRouter from '../routes/service_routes';
import { initAdminRoutes } from '../routes/admin_routes';
import { getUserModel } from '../models/user_model';

/**
 * Application setup
 */
export const setupApp = async (config: {
  mongoUri: string;
  jwtSecret: string;
  corsOptions?: cors.CorsOptions;
}) => {
  // Create Express app
  const app = express();
  
  // Connect to MongoDB
  await mongoose.connect(config.mongoUri);
  console.log('Connected to MongoDB');
  
  // Middleware
  app.use(helmet());
  app.use(cors(config.corsOptions));
  app.use(express.json());
  
  // Create services
  const userModel = getUserModel();
  const userRepository = {
    // Simplified user repository for example
    findById: (id: string) => userModel.findById(id),
    findByEmail: (email: string) => userModel.findByEmail(email),
    // Other methods would be implemented here
  };
  
  const sessionRepository = {
    // Mock session repository for example
    // This would be implemented with proper session storage
  };
  
  // Create services
  const auditLogService = new AuditLogService({
    enableConsoleLogging: true,
    logLevel: 'info',
    maxRetention: 90
  });
  
  const authService = new AuthService(
    userRepository,
    sessionRepository,
    {
      jwtSecret: config.jwtSecret,
      tokenExpiresIn: '1d',
      emailVerificationRequired: true
    },
    auditLogService
  );
  
  // Routes
  app.use('/api/auth', authRouter);
  app.use('/api/users', userRouter);
  app.use('/api/services', serviceRouter);
  
  // Admin routes with audit log access
  const adminRouter = express.Router();
  initAdminRoutes(adminRouter, auditLogService);
  app.use('/api/admin', adminRouter);
  
  return { app, authService, auditLogService };
}; 