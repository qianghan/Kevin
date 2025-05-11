/**
 * Chat Service Factory
 * 
 * This factory implements the strategy pattern for creating chat service instances,
 * delegating to either frontend or /ui implementations based on the strategy selected.
 * It follows the Dependency Inversion Principle (DIP) by depending on abstractions
 * rather than concrete implementations.
 */

import { IChatService } from '../../interfaces/services/chat.service';
import { ChatAdapterService } from './chat-adapter.service';
import { MockChatService } from './mock-chat.service';
import { loadUIChatService } from './ui-chat-service-utils';
import { initializeUIChatService } from './initialize-ui-service';

/**
 * Chat Service Strategy types
 */
export type ChatServiceStrategy = 'ui-adapter' | 'frontend' | 'mock' | 'auto';

/**
 * Interface for creating chat service implementations
 */
export interface IChatServiceFactory {
  /**
   * Create a chat service based on the specified strategy
   */
  createChatService(strategy?: ChatServiceStrategy): IChatService;
  
  /**
   * Register a custom service creator function
   */
  registerServiceCreator(name: string, creator: () => IChatService): void;
}

/**
 * Factory class for creating chat service instances
 */
export class ChatServiceFactory implements IChatServiceFactory {
  private serviceCreators: Map<string, () => IChatService> = new Map();
  private defaultStrategy: ChatServiceStrategy = 'auto';
  private lastInitAttempt: number = 0;
  private initializationPromise: Promise<void> | null = null;
  
  /**
   * Create a new ChatServiceFactory
   * @param defaultStrategy The default strategy to use if none is specified
   */
  constructor(defaultStrategy: ChatServiceStrategy = 'auto') {
    this.defaultStrategy = defaultStrategy;
    
    // Register built-in service creators
    this.registerServiceCreator('ui-adapter', this.createUiAdapterService);
    this.registerServiceCreator('frontend', this.createFrontendService);
    this.registerServiceCreator('mock', this.createMockService);
    this.registerServiceCreator('auto', this.createAutoDetectService);
  }
  
  /**
   * Create a chat service based on the specified strategy
   * @param strategy The strategy to use for creating the service
   * @returns An implementation of IChatService
   */
  createChatService(strategy: ChatServiceStrategy = this.defaultStrategy): IChatService {
    const creator = this.serviceCreators.get(strategy);
    
    if (!creator) {
      throw new Error(`Unknown chat service strategy: ${strategy}`);
    }
    
    try {
      return creator();
    } catch (error) {
      console.error(`Error creating chat service with strategy "${strategy}":`, error);
      
      // If the requested strategy fails and it's not already a fallback,
      // try to use the mock service as a last resort
      if (strategy !== 'mock') {
        console.warn(`Falling back to mock service due to error with ${strategy} strategy`);
        return this.createMockService();
      }
      
      throw error;
    }
  }
  
  /**
   * Register a custom service creator function
   * @param name The name of the service creator
   * @param creator The function that creates the service
   */
  registerServiceCreator(name: string, creator: () => IChatService): void {
    this.serviceCreators.set(name, creator);
  }
  
  /**
   * Try to initialize the UI service if it's not already initialized
   * Limit initialization attempts to once every 10 seconds to prevent excessive retries
   */
  private initializeUIServiceIfNeeded = async (): Promise<boolean> => {
    if (typeof window === 'undefined') {
      return false;
    }
    
    // Check if service is already initialized
    if ((window as any).KAI_UI?.services?.chat) {
      return true;
    }
    
    // Limit initialization attempts
    const now = Date.now();
    if (now - this.lastInitAttempt < 10000) {
      return false;
    }
    
    this.lastInitAttempt = now;
    
    // If we're already initializing, wait for that to complete
    if (this.initializationPromise) {
      try {
        await this.initializationPromise;
        return (window as any).KAI_UI?.services?.chat != null;
      } catch (error) {
        console.warn('Previous initialization attempt failed:', error);
        return false;
      }
    }
    
    // Start a new initialization
    this.initializationPromise = (async () => {
      try {
        console.log('Attempting to initialize UI chat service');
        await initializeUIChatService();
        console.log('UI chat service initialization successful');
      } catch (error) {
        console.error('Failed to initialize UI chat service:', error);
      } finally {
        this.initializationPromise = null;
      }
    })();
    
    await this.initializationPromise;
    return (window as any).KAI_UI?.services?.chat != null;
  }
  
  /**
   * Create a UI adapter service that wraps the UI chat service
   */
  private createUiAdapterService = (): IChatService => {
    // First check if the UI service is already available
    const uiService = loadUIChatService();
    
    if (uiService) {
      console.log('Found existing UI chat service, using adapter');
      return new ChatAdapterService(uiService);
    }
    
    // Try to initialize it if it's not available
    console.log('No existing UI chat service found, attempting to initialize');
    const newService = initializeUIChatService();
    
    if (!newService) {
      throw new Error('UI chat service initialization failed');
    }
    
    return new ChatAdapterService(newService);
  };
  
  /**
   * Create a frontend-specific chat service implementation
   */
  private createFrontendService = (): IChatService => {
    // This would be implemented with a frontend-native chat service
    // For now, we'll throw an error as it's not implemented yet
    throw new Error('Native frontend chat service not implemented');
  };
  
  /**
   * Create a mock chat service for testing
   */
  private createMockService = (): IChatService => {
    console.log('Creating mock chat service');
    return new MockChatService();
  };
  
  /**
   * Create a service by auto-detecting the available implementations
   */
  private createAutoDetectService = (): IChatService => {
    // Try UI adapter first
    try {
      // Check if the UI service is already available
      const uiService = loadUIChatService();
      
      if (uiService) {
        console.log('Auto-detected UI chat service');
        return new ChatAdapterService(uiService);
      }
      
      // If we're in a browser, try to initialize the UI service
      if (typeof window !== 'undefined') {
        // Attempt to initialize the UI service
        this.initializeUIServiceIfNeeded().catch(error => {
          console.warn('Background UI service initialization failed:', error);
        });
        
        // If initialization was quick enough, use the UI service
        const initializedService = loadUIChatService();
        if (initializedService) {
          console.log('Successfully initialized UI chat service through auto-detection');
          return new ChatAdapterService(initializedService);
        }
      }
    } catch (error) {
      console.warn('Error trying to use UI chat service:', error);
    }
    
    // Otherwise use the mock service as a fallback
    console.warn('UI chat service not available, falling back to mock service');
    return this.createMockService();
  };
}

/**
 * Create and export a singleton instance of the chat service factory
 */
export const chatServiceFactory = new ChatServiceFactory();

/**
 * Helper function to get a chat service using the default factory
 */
export function getChatService(strategy: ChatServiceStrategy = 'auto'): IChatService {
  return chatServiceFactory.createChatService(strategy);
} 