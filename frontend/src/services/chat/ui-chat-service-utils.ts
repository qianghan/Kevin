/**
 * UI Chat Service Utilities
 * 
 * This file contains utilities for working with UI chat services from the frontend.
 * It provides functions to load, initialize, and synchronize with UI chat services.
 */

import { IChatService } from '../../interfaces/services/chat.service';
import { ChatAdapterService } from './chat-adapter.service';

/**
 * Interface describing what we need from a UI service loader
 */
interface UIServiceLoader {
  getChatService: () => any;
}

/**
 * Load a UI chat service from the global scope
 * @returns The UI chat service instance or null if not found
 */
export function loadUIChatService(): any | null {
  try {
    // Check if the UI package is available in the global scope
    if (typeof window !== 'undefined' && (window as any).KAI_UI && (window as any).KAI_UI.services) {
      return (window as any).KAI_UI.services.chat;
    }
    return null;
  } catch (error) {
    console.error('Error loading UI chat service:', error);
    return null;
  }
}

/**
 * Create a wrapped chat service using the UI implementation
 * @param uiChatService The UI chat service instance
 * @returns A frontend-compatible chat service
 */
export function createChatServiceFromUI(uiChatService: any): IChatService {
  return new ChatAdapterService(uiChatService);
}

/**
 * Try to load and adapt the UI chat service, with fallback to mock implementation
 * @param mockService Optional mock service to use if UI service is not available
 * @returns A frontend-compatible chat service
 */
export function loadAndAdaptChatService(mockService?: IChatService): IChatService {
  const uiService = loadUIChatService();
  
  if (uiService) {
    console.log('UI chat service found, using adapter');
    return createChatServiceFromUI(uiService);
  }
  
  if (mockService) {
    console.log('UI chat service not found, using provided mock');
    return mockService;
  }
  
  console.warn('UI chat service not found and no mock provided');
  throw new Error('Chat service could not be initialized');
}

/**
 * Checks if the UI chat service is available
 * @returns True if the UI chat service is available
 */
export function isUIChatServiceAvailable(): boolean {
  return loadUIChatService() !== null;
}

/**
 * Register a frontend chat service to be available to UI components
 * @param chatService The frontend chat service to register
 */
export function registerFrontendChatService(chatService: IChatService): void {
  if (typeof window !== 'undefined') {
    // Create or access the KAI_FRONTEND namespace
    (window as any).KAI_FRONTEND = (window as any).KAI_FRONTEND || {};
    (window as any).KAI_FRONTEND.services = (window as any).KAI_FRONTEND.services || {};
    
    // Register the chat service
    (window as any).KAI_FRONTEND.services.chat = chatService;
  }
} 