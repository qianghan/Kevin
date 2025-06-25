/**
 * User Management System
 * 
 * This is the main entry point for the User Management system.
 * It exports all the components needed for integration with other services.
 */

// Export models
import User from './models/user_model';

// Export interfaces
export * from './services/interfaces';

// Export implementations
export { UserService } from './services/user_service';
export { MongoUserRepository } from './repositories/mongo_user_repository';

// Export routers
export { createUserRouter } from './api/user_router';
export { createAuthRouter } from './api/auth_router';
export { default as serviceRouter } from './routes/service_routes';

// Factory function to create a complete user management system
import { UserService } from './services/user_service';
import { MongoUserRepository } from './repositories/mongo_user_repository';
import { createUserRouter } from './api/user_router';
import { createAuthRouter } from './api/auth_router';
import { Router } from 'express';
import { UserRole } from './models/user_model';

const createDefaultAdminUser = async (userService: UserService) => {
  try {
    const defaultEmail = 'admin@example.com';
    const defaultPassword = 'admin123';
    
    // Check if admin user exists
    const existingUser = await userService.getUserByEmail(defaultEmail);
    if (!existingUser) {
      // Create default admin user
      await userService.register({
        firstName: 'Admin',
        lastName: 'User',
        email: defaultEmail,
        role: UserRole.ADMIN
      }, defaultPassword);
      console.log('Default admin user created successfully');
    }
  } catch (error) {
    console.error('Error creating default admin user:', error);
  }
};

/**
 * Create a user management system with all components
 * 
 * @returns Object containing userService, userRepository, userRouter, and authRouter
 */
export function createUserManagementSystem() {
  // Create repository
  const userRepository = new MongoUserRepository();
  
  // Create service
  const userService = new UserService(userRepository);
  
  // Create default admin user
  createDefaultAdminUser(userService);
  
  // Create routers
  const userRouter = createUserRouter(userService);
  const authRouter = createAuthRouter(userService);
  
  return {
    userService,
    userRepository,
    userRouter,
    authRouter
  };
} 