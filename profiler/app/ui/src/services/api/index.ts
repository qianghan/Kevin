// Export interfaces
export * from './interfaces';

// Export implementations
export { WebSocketClient } from './websocket-client';
export { ProfileClient } from './profile-client';
export type { ProfileData } from './profile-client';

// Export factory
export { ApiClientFactory } from './api-client-factory';

// Re-export convenience function to get API clients
import { ApiClientFactory } from './api-client-factory';

/**
 * Get a WebSocket client for the specified user
 * @param userId The user ID for the WebSocket connection
 */
export function getWebSocketClient(userId: string) {
  return ApiClientFactory.getInstance().getWebSocketClient(userId);
}

/**
 * Get a Profile client for the specified user
 * @param userId The user ID for the profile
 */
export function getProfileClient(userId: string) {
  return ApiClientFactory.getInstance().getProfileClient(userId);
}

/**
 * Shutdown all API clients
 */
export function shutdownAllClients() {
  return ApiClientFactory.getInstance().shutdownAll();
} 