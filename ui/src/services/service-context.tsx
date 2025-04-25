/**
 * Service Context
 * 
 * This file implements dependency injection for services using React Context.
 * It allows components to access services without direct coupling to implementations.
 */

import React, { createContext, useContext, ReactNode } from 'react';

import { IAuthService } from '../interfaces/services/auth.service';
import { IChatService } from '../interfaces/services/chat.service';
import { IProfileService } from '../interfaces/services/profile.service';
import { IAgentService } from '../interfaces/services/agent.service';
import { IStorageService } from '../interfaces/services/storage.service';
import { INotificationService } from '../interfaces/services/notification.service';
import { IErrorService } from '../interfaces/services/error.service';
import { ILoggingService } from '../interfaces/services/logging.service';

// Import default service implementations
import { services, ServiceContainer } from './index';

// Create the service context
const ServiceContext = createContext<ServiceContainer | null>(null);

/**
 * Props for the ServiceProvider component
 */
interface ServiceProviderProps {
  services?: Partial<ServiceContainer>;
  children: ReactNode;
}

/**
 * ServiceProvider component for dependency injection
 * 
 * This component provides services to the component tree.
 * It allows for overriding default services with custom implementations.
 */
export const ServiceProvider: React.FC<ServiceProviderProps> = ({
  services: customServices,
  children,
}) => {
  // Merge default services with any custom services provided
  const mergedServices = {
    ...services,
    ...customServices,
  };

  return (
    <ServiceContext.Provider value={mergedServices}>
      {children}
    </ServiceContext.Provider>
  );
};

/**
 * Custom hook for accessing the auth service
 */
export const useAuthService = (): IAuthService => {
  const context = useContext(ServiceContext);
  if (!context) {
    throw new Error('useAuthService must be used within a ServiceProvider');
  }
  return context.auth;
};

/**
 * Custom hook for accessing the chat service
 */
export const useChatService = (): IChatService => {
  const context = useContext(ServiceContext);
  if (!context) {
    throw new Error('useChatService must be used within a ServiceProvider');
  }
  return context.chat;
};

/**
 * Custom hook for accessing the profile service
 */
export const useProfileService = (): IProfileService => {
  const context = useContext(ServiceContext);
  if (!context) {
    throw new Error('useProfileService must be used within a ServiceProvider');
  }
  return context.profile;
};

/**
 * Custom hook for accessing the agent service
 */
export const useAgentService = (): IAgentService => {
  const context = useContext(ServiceContext);
  if (!context) {
    throw new Error('useAgentService must be used within a ServiceProvider');
  }
  return context.agent;
};

/**
 * Custom hook for accessing the storage service
 */
export const useStorageService = (): IStorageService => {
  const context = useContext(ServiceContext);
  if (!context) {
    throw new Error('useStorageService must be used within a ServiceProvider');
  }
  return context.storage;
};

/**
 * Custom hook for accessing the notification service
 */
export const useNotificationService = (): INotificationService => {
  const context = useContext(ServiceContext);
  if (!context) {
    throw new Error('useNotificationService must be used within a ServiceProvider');
  }
  return context.notification;
};

/**
 * Custom hook for accessing the error service
 */
export const useErrorService = (): IErrorService => {
  const context = useContext(ServiceContext);
  if (!context) {
    throw new Error('useErrorService must be used within a ServiceProvider');
  }
  return context.error;
};

/**
 * Custom hook for accessing the logging service
 */
export const useLoggingService = (): ILoggingService => {
  const context = useContext(ServiceContext);
  if (!context) {
    throw new Error('useLoggingService must be used within a ServiceProvider');
  }
  return context.logging;
};

/**
 * Custom hook for accessing all services
 */
export const useServices = (): ServiceContainer => {
  const context = useContext(ServiceContext);
  if (!context) {
    throw new Error('useServices must be used within a ServiceProvider');
  }
  return context;
}; 