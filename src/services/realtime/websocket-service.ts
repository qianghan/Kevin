/**
 * WebSocket-based real-time data update service.
 * 
 * This module provides real-time data updates via WebSockets,
 * with automatic reconnection and event subscription.
 */

import { cacheService } from '../cache/cache_service';

/**
 * WebSocket connection states
 */
export enum ConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  RECONNECTING = 'reconnecting',
}

/**
 * Options for WebSocket configuration
 */
export interface WebSocketOptions {
  /** URL for WebSocket connection */
  url: string;
  /** Authentication token (optional) */
  authToken?: string;
  /** Auto-reconnect on disconnect (default: true) */
  autoReconnect?: boolean;
  /** Maximum reconnection attempts (default: Infinity) */
  maxReconnectAttempts?: number;
  /** Base delay for reconnection in ms (default: 1000) */
  reconnectDelay?: number;
  /** Maximum delay for reconnection in ms (default: 30000) */
  maxReconnectDelay?: number;
  /** Whether to use exponential backoff for reconnection (default: true) */
  useExponentialBackoff?: boolean;
  /** Ping interval in ms for keeping connection alive (default: 30000) */
  pingInterval?: number;
  /** Timeout for ping response in ms (default: 5000) */
  pingTimeout?: number;
}

/**
 * WebSocket event with payload
 */
export interface WebSocketEvent<T = any> {
  /** Event type */
  type: string;
  /** Event data */
  data: T;
  /** Timestamp when the event occurred */
  timestamp: number;
}

/**
 * Real-time data update service using WebSockets
 */
export class WebSocketService {
  private static instance: WebSocketService;
  private socket: WebSocket | null = null;
  private options: Required<WebSocketOptions>;
  private connectionState: ConnectionState = ConnectionState.DISCONNECTED;
  private reconnectAttempts: number = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private pongTimeout: ReturnType<typeof setTimeout> | null = null;
  private eventHandlers: Map<string, Set<(data: any) => void>> = new Map();
  private connectionStateHandlers: Set<(state: ConnectionState) => void> = new Set();
  
  /**
   * Default WebSocket options
   */
  private static DEFAULT_OPTIONS: Omit<Required<WebSocketOptions>, 'url'> = {
    authToken: '',
    autoReconnect: true,
    maxReconnectAttempts: Infinity,
    reconnectDelay: 1000,
    maxReconnectDelay: 30000,
    useExponentialBackoff: true,
    pingInterval: 30000,
    pingTimeout: 5000,
  };
  
  /**
   * Private constructor for singleton pattern
   */
  private constructor(options: WebSocketOptions) {
    this.options = { ...WebSocketService.DEFAULT_OPTIONS, ...options } as Required<WebSocketOptions>;
  }
  
  /**
   * Gets the singleton instance of the WebSocket service
   */
  public static getInstance(options?: WebSocketOptions): WebSocketService {
    if (!WebSocketService.instance && options) {
      WebSocketService.instance = new WebSocketService(options);
    } else if (!WebSocketService.instance && !options) {
      throw new Error('WebSocketService must be initialized with options first');
    }
    return WebSocketService.instance;
  }
  
  /**
   * Initializes the WebSocket service with the given options
   */
  public static initialize(options: WebSocketOptions): WebSocketService {
    if (WebSocketService.instance) {
      WebSocketService.instance.disconnect();
    }
    WebSocketService.instance = new WebSocketService(options);
    return WebSocketService.instance;
  }
  
  /**
   * Connects to the WebSocket server
   */
  public connect(): Promise<void> {
    if (this.socket && (this.socket.readyState === WebSocket.CONNECTING || this.socket.readyState === WebSocket.OPEN)) {
      return Promise.resolve();
    }
    
    this.updateConnectionState(ConnectionState.CONNECTING);
    
    return new Promise((resolve, reject) => {
      try {
        // Build URL with auth token if provided
        let url = this.options.url;
        if (this.options.authToken) {
          url += url.includes('?') ? '&' : '?';
          url += `token=${encodeURIComponent(this.options.authToken)}`;
        }
        
        // Create new WebSocket
        this.socket = new WebSocket(url);
        
        // Set up event listeners
        this.socket.onopen = () => {
          this.onConnected();
          resolve();
        };
        
        this.socket.onmessage = (event) => {
          this.onMessage(event);
        };
        
        this.socket.onclose = (event) => {
          this.onDisconnected(event);
          
          if (!event.wasClean && this.connectionState === ConnectionState.CONNECTING) {
            reject(new Error(`Failed to connect to WebSocket server: ${event.reason || 'Connection closed'}`));
          }
        };
        
        this.socket.onerror = (error) => {
          if (this.connectionState === ConnectionState.CONNECTING) {
            reject(new Error('Failed to connect to WebSocket server'));
          }
          console.error('WebSocket error:', error);
        };
      } catch (error) {
        this.updateConnectionState(ConnectionState.DISCONNECTED);
        reject(error);
      }
    });
  }
  
  /**
   * Disconnects from the WebSocket server
   */
  public disconnect(): void {
    this.clearTimers();
    
    if (this.socket) {
      // Remove event listeners to prevent reconnection
      this.socket.onclose = null;
      this.socket.onopen = null;
      this.socket.onerror = null;
      this.socket.onmessage = null;
      
      // Close the connection
      if (this.socket.readyState === WebSocket.CONNECTING || this.socket.readyState === WebSocket.OPEN) {
        this.socket.close();
      }
      
      this.socket = null;
      this.updateConnectionState(ConnectionState.DISCONNECTED);
    }
  }
  
  /**
   * Sends an event to the WebSocket server
   */
  public sendEvent<T>(eventType: string, data: T): boolean {
    if (!this.isConnected()) {
      return false;
    }
    
    const event: WebSocketEvent<T> = {
      type: eventType,
      data,
      timestamp: Date.now(),
    };
    
    try {
      this.socket!.send(JSON.stringify(event));
      return true;
    } catch (error) {
      console.error('Error sending WebSocket event:', error);
      return false;
    }
  }
  
  /**
   * Subscribes to events of a specific type
   */
  public subscribe<T>(eventType: string, handler: (data: T) => void): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
      
      // If connected, send subscription request to server
      if (this.isConnected()) {
        this.sendEvent('subscribe', { eventType });
      }
    }
    
    // Add handler
    this.eventHandlers.get(eventType)!.add(handler as any);
    
    // Return unsubscribe function
    return () => {
      this.unsubscribe(eventType, handler);
    };
  }
  
  /**
   * Unsubscribes from events of a specific type
   */
  public unsubscribe<T>(eventType: string, handler: (data: T) => void): void {
    const handlers = this.eventHandlers.get(eventType);
    if (!handlers) {
      return;
    }
    
    // Remove the handler
    handlers.delete(handler as any);
    
    // If no more handlers for this event type, unsubscribe from server
    if (handlers.size === 0) {
      this.eventHandlers.delete(eventType);
      
      // If connected, send unsubscription request
      if (this.isConnected()) {
        this.sendEvent('unsubscribe', { eventType });
      }
    }
  }
  
  /**
   * Subscribes to connection state changes
   */
  public onConnectionStateChange(handler: (state: ConnectionState) => void): () => void {
    this.connectionStateHandlers.add(handler);
    
    // Call handler immediately with current state
    handler(this.connectionState);
    
    // Return unsubscribe function
    return () => {
      this.connectionStateHandlers.delete(handler);
    };
  }
  
  /**
   * Gets the current connection state
   */
  public getConnectionState(): ConnectionState {
    return this.connectionState;
  }
  
  /**
   * Checks if the WebSocket is currently connected
   */
  public isConnected(): boolean {
    return this.socket !== null && this.socket.readyState === WebSocket.OPEN;
  }
  
  /**
   * Handles WebSocket connection established
   */
  private onConnected(): void {
    this.updateConnectionState(ConnectionState.CONNECTED);
    this.reconnectAttempts = 0;
    
    // Subscribe to all events
    for (const eventType of this.eventHandlers.keys()) {
      this.sendEvent('subscribe', { eventType });
    }
    
    // Start ping interval
    this.startPingInterval();
  }
  
  /**
   * Handles WebSocket disconnection
   */
  private onDisconnected(event: CloseEvent): void {
    this.updateConnectionState(ConnectionState.DISCONNECTED);
    this.clearTimers();
    
    // Attempt reconnection if auto-reconnect is enabled
    if (this.options.autoReconnect && this.reconnectAttempts < this.options.maxReconnectAttempts) {
      this.scheduleReconnect();
    }
  }
  
  /**
   * Handles incoming WebSocket messages
   */
  private onMessage(event: MessageEvent): void {
    try {
      // Reset pong timeout on any message
      if (this.pongTimeout) {
        clearTimeout(this.pongTimeout);
        this.pongTimeout = null;
      }
      
      // Parse message
      const message = JSON.parse(event.data);
      
      // Handle ping/pong messages
      if (message.type === 'ping') {
        this.sendEvent('pong', {});
        return;
      } else if (message.type === 'pong') {
        return;
      }
      
      // Handle events
      if (message.type) {
        this.handleEvent(message);
      }
    } catch (error) {
      console.error('Error processing WebSocket message:', error);
    }
  }
  
  /**
   * Handles an event received from the server
   */
  private handleEvent(event: WebSocketEvent): void {
    // Get handlers for this event type
    const handlers = this.eventHandlers.get(event.type);
    if (!handlers) {
      return;
    }
    
    // Call all handlers
    for (const handler of handlers) {
      try {
        handler(event.data);
      } catch (error) {
        console.error(`Error in WebSocket event handler for ${event.type}:`, error);
      }
    }
    
    // Handle cache invalidation for resource updates
    if (['created', 'updated', 'deleted'].includes(event.type) && event.data && event.data.resourceType) {
      const { resourceType, id } = event.data;
      
      if (id) {
        // Invalidate specific resource
        cacheService.delete({
          resourceType,
          id,
        });
      } else {
        // Invalidate all resources of this type
        cacheService.invalidateResourceType(resourceType);
      }
    }
  }
  
  /**
   * Schedules a reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    
    this.updateConnectionState(ConnectionState.RECONNECTING);
    this.reconnectAttempts++;
    
    // Calculate reconnect delay with exponential backoff
    let delay = this.options.reconnectDelay;
    if (this.options.useExponentialBackoff) {
      delay = Math.min(
        delay * Math.pow(2, this.reconnectAttempts - 1),
        this.options.maxReconnectDelay
      );
    }
    
    // Add jitter (0-20%)
    const jitter = delay * 0.2 * Math.random();
    delay += jitter;
    
    // Schedule reconnect
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect().catch(() => {
        // If reconnection fails, schedule another attempt
        if (this.reconnectAttempts < this.options.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      });
    }, delay);
  }
  
  /**
   * Starts the ping interval to keep the connection alive
   */
  private startPingInterval(): void {
    this.clearTimers();
    
    // Set up ping interval
    this.pingTimer = setInterval(() => {
      if (this.isConnected()) {
        // Send ping
        this.sendEvent('ping', {});
        
        // Set timeout for pong response
        this.pongTimeout = setTimeout(() => {
          console.warn('WebSocket ping timed out, reconnecting...');
          this.disconnect();
          this.connect().catch(() => {
            if (this.options.autoReconnect) {
              this.scheduleReconnect();
            }
          });
        }, this.options.pingTimeout);
      }
    }, this.options.pingInterval);
  }
  
  /**
   * Clears all timers
   */
  private clearTimers(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
    
    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = null;
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
  
  /**
   * Updates the connection state and notifies listeners
   */
  private updateConnectionState(state: ConnectionState): void {
    this.connectionState = state;
    
    // Notify all connection state handlers
    for (const handler of this.connectionStateHandlers) {
      try {
        handler(state);
      } catch (error) {
        console.error('Error in connection state handler:', error);
      }
    }
  }
}

// Create a default instance
let websocketService: WebSocketService;

// Initialize with config from environment if available
if (typeof window !== 'undefined') {
  const wsUrl = (window as any).__NEXT_DATA__?.runtimeConfig?.WEBSOCKET_URL || 
                'wss://api.example.com/ws';
  
  websocketService = WebSocketService.initialize({
    url: wsUrl,
  });
}

export { websocketService }; 