/**
 * Service Layer Index
 * 
 * This file exports the concrete implementations of all service interfaces.
 * It provides a single entry point for accessing services throughout the application.
 */

import { AuthService } from './auth/auth.service';
import { ChatService } from './chat/chat.service';
import { ProfileService } from './profile/profile.service';
import { AgentService } from './agent/agent.service';
import { StorageService } from './storage/storage.service';
import { NotificationService } from './notification/notification.service';
import { ErrorService } from './error/error.service';
import { LoggingService } from './logging/logging.service';

// Export concrete service implementations
export { 
  AuthService,
  ChatService,
  ProfileService,
  AgentService,
  StorageService,
  NotificationService,
  ErrorService,
  LoggingService
};

// Export a service container with all services
export interface ServiceContainer {
  auth: AuthService;
  chat: ChatService;
  profile: ProfileService;
  agent: AgentService;
  storage: StorageService;
  notification: NotificationService;
  error: ErrorService;
  logging: LoggingService;
}

// Default service container with all service instances
export const services: ServiceContainer = {
  auth: new AuthService(),
  chat: new ChatService(),
  profile: new ProfileService(),
  agent: new AgentService(),
  storage: new StorageService(),
  notification: new NotificationService(),
  error: new ErrorService(),
  logging: new LoggingService()
}; 