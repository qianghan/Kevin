import { 
  IWebSocketClient, 
  IProfileClient,
  IDocumentClient,
  IRecommendationClient,
  WebSocketConfig
} from './interfaces';
import { WebSocketClient } from './websocket-client';
import { ProfileClient } from './profile-client';

/**
 * Factory for creating API client instances.
 * This is a singleton that provides access to all API clients.
 */
export class ApiClientFactory {
  private static instance: ApiClientFactory;
  private clients: Map<string, any> = new Map();
  
  private constructor() {
    // Private constructor to enforce singleton
  }
  
  /**
   * Get the singleton instance of the ApiClientFactory
   */
  public static getInstance(): ApiClientFactory {
    if (!ApiClientFactory.instance) {
      ApiClientFactory.instance = new ApiClientFactory();
    }
    return ApiClientFactory.instance;
  }
  
  /**
   * Get a WebSocket client instance
   * @param userId The user ID for the WebSocket connection
   */
  public getWebSocketClient(userId: string): IWebSocketClient {
    const clientKey = `websocket:${userId}`;
    
    if (!this.clients.has(clientKey)) {
      const config: WebSocketConfig = { userId };
      this.clients.set(clientKey, new WebSocketClient(config));
    }
    
    return this.clients.get(clientKey) as IWebSocketClient;
  }
  
  /**
   * Get a Profile client instance
   * @param userId The user ID for the profile
   */
  public getProfileClient(userId: string): IProfileClient {
    const clientKey = `profile:${userId}`;
    
    if (!this.clients.has(clientKey)) {
      const config: WebSocketConfig = { userId };
      this.clients.set(clientKey, new ProfileClient(config));
    }
    
    return this.clients.get(clientKey) as IProfileClient;
  }
  
  /**
   * Shutdown all clients
   */
  public shutdownAll(): void {
    this.clients.forEach(client => {
      if (client && typeof client.shutdown === 'function') {
        client.shutdown();
      }
    });
    this.clients.clear();
  }
} 