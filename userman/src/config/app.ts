import express from 'express';
import mongoose from 'mongoose';
import cors from 'cors';
import helmet from 'helmet';
import { AuthService } from '../services/auth_service';
import { AuditLogService } from '../services/audit_log_service';
import { IUserRepository, ISessionRepository } from '../services/interfaces';
import { User, UserDocument } from '../models/user_model';
import userRouter from '../routes/user_routes';
import authRouter from '../routes/auth_routes';
import serviceRouter from '../routes/service_routes';
import { initAdminRoutes } from '../routes/admin_routes';
import { initializeServices } from './service_init';

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
  
  // Initialize services registry
  const serviceRegistry = await initializeServices();
  console.log('Service registry initialized');
  
  // Middleware
  app.use(helmet());
  app.use(cors(config.corsOptions));
  app.use(express.json());
  
  // Create services
  const userRepository: IUserRepository = {
    findById: async (id: string) => await User.findById(id),
    findByEmail: async (email: string) => await User.findOne({ email }),
    create: async (user: Partial<UserDocument>) => await User.create(user),
    update: async (id: string, data: Partial<UserDocument>) => {
      const updatedUser = await User.findByIdAndUpdate(id, data, { new: true });
      if (!updatedUser) {
        throw new Error(`User with id ${id} not found`);
      }
      return updatedUser;
    },
    delete: async (id: string) => {
      const deletedUser = await User.findByIdAndDelete(id);
      return !!deletedUser;
    },
    getUserModel: () => User,
    updatePassword: async (id: string, hashedPassword: string) => {
      const updatedUser = await User.findByIdAndUpdate(id, { password: hashedPassword }, { new: true });
      if (!updatedUser) {
        throw new Error(`User with id ${id} not found`);
      }
      return updatedUser;
    },
    updatePreferences: async (id: string, preferences) => {
      const updatedUser = await User.findByIdAndUpdate(id, { preferences }, { new: true });
      if (!updatedUser) {
        throw new Error(`User with id ${id} not found`);
      }
      return updatedUser.preferences || {};
    }
  };
  
  // Create session repository
  const sessionRepository: ISessionRepository = {
    createSession: async (sessionData) => {
      // For now, store sessions in memory
      // In production, use Redis or another session store
      const session = {
        id: Math.random().toString(36).substring(7),
        ...sessionData,
        createdAt: new Date(),
        expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours
      };
      return session;
    },
    findSessionByToken: async (token) => {
      // Implement session lookup
      return null;
    },
    findSessionsByUser: async (userId) => {
      // Implement user sessions lookup
      return [];
    },
    invalidateSession: async (sessionId) => {
      // Implement session invalidation
      return true;
    },
    invalidateAllUserSessions: async (userId) => {
      // Implement all sessions invalidation
      return true;
    },
    updateSession: async (sessionId, data) => {
      // Implement session update
      return null;
    },
    mapSessionToDTO: (session) => {
      // Map session to DTO
      return session;
    }
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
  
  return { app, authService, auditLogService, serviceRegistry };
}; 