/**
 * Chat Services Entry Point
 * 
 * This file exports the chat-related services and utilities for frontend use.
 * It acts as the primary integration point with the UI chat services.
 */

// Export the ChatAdapterService implementation
export { ChatAdapterService } from './chat-adapter.service';

// Export utility functions for working with UI chat services
export * from './ui-chat-service-utils';

// Re-export interfaces for convenience
export * from '../../interfaces/services/chat.service'; 