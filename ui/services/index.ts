/**
 * Service exports
 * 
 * This file centralizes all service exports to avoid circular dependencies
 * and provide a clean import interface for service consumers.
 */

// Re-export user service
import { UserService } from './UserService';
export * from './UserService';

// Export a singleton instance of the user service
export const userService = new UserService();

// Export service types
export type { UserProfile, UserPreferences } from './UserService'; 