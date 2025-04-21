/**
 * User Management System
 * 
 * This is the main entry point for the User Management system.
 * It exports all the components needed for integration with other services.
 */

// Export models
export * from './models/user_model';

// Export interfaces
export * from './services/interfaces';

// Export implementations
export { UserService } from './services/user_service';
export { MongoUserRepository } from './services/user_repository';

// Export routers
export { createUserRouter } from './api/user_router';
export { createAuthRouter } from './api/auth_router';

// Factory function to create a complete user management system
import { UserService } from './services/user_service';
import { MongoUserRepository } from './services/user_repository';
import { createUserRouter } from './api/user_router';
import { createAuthRouter } from './api/auth_router';

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