import { 
  IWebSocketClient,
  WebSocketConfig,
  WebSocketMessage,
  WebSocketHandler,
  WebSocketErrorHandler,
  ConnectionHandler,
  WebSocketError
} from './interfaces';

/**
 * WebSocket client implementation for real-time communication with the backend
 */
export class WebSocketClient implements IWebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts: number;
  private reconnectDelay: number;
  private messageHandlers: Map<string, WebSocketHandler[]> = new Map();
  private connectHandlers: ConnectionHandler[] = [];
  private disconnectHandlers: ConnectionHandler[] = [];
  private errorHandlers: WebSocketErrorHandler[] = [];
  private messageQueue: WebSocketMessage[] = [];
  private userId: string;
  private apiKey: string;
  private baseUrl: string;

  constructor(config: WebSocketConfig) {
    this.userId = config.userId;
    this.apiKey = config.apiKey || process.env.NEXT_PUBLIC_API_KEY || 'test-key-123';
    this.baseUrl = config.baseUrl || process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    this.maxReconnectAttempts = config.reconnectAttempts || 5;
    this.reconnectDelay = config.reconnectDelay || 1000;
  }

  async initialize(): Promise<void> {
    // Nothing to initialize for WebSocket client
    return Promise.resolve();
  }

  shutdown(): void {
    this.disconnect();
    this.clearAllHandlers();
  }

  connect(): void {
    if (this.ws) {
      console.warn('WebSocket already connected');
      return;
    }

    try {
      const encodedApiKey = encodeURIComponent(this.apiKey);
      const wsUrl = `${this.baseUrl}/ws/${this.userId}?x-api-key=${encodedApiKey}`;
      console.log('Connecting to WebSocket:', wsUrl);
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.notifyConnectHandlers();
        
        // Send initial connection message
        this.sendMessage('connection_init', { userId: this.userId });
        
        // Process any queued messages
        this.processMessageQueue();
      };

      this.ws.onmessage = (event: MessageEvent) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('Received WebSocket message:', message);
          this.handleMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          this.notifyErrorHandlers({
            type: 'message',
            message: 'Failed to parse message',
            timestamp: new Date().toISOString(),
            error
          });
        }
      };

      this.ws.onclose = (event: CloseEvent) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.ws = null;
        this.notifyDisconnectHandlers();
        this.reconnect();
      };

      this.ws.onerror = (error: Event) => {
        console.error('WebSocket error:', error);
        this.notifyErrorHandlers({
          type: 'connection',
          message: 'WebSocket connection error',
          timestamp: new Date().toISOString(),
          error
        });
        // Attempt to reconnect on error
        this.reconnect();
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      this.notifyErrorHandlers({
        type: 'connection',
        message: 'Failed to create WebSocket connection',
        timestamp: new Date().toISOString(),
        error
      });
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  sendMessage(type: string, data: any): void {
    const message: WebSocketMessage = {
      type,
      data,
      timestamp: new Date().toISOString()
    };

    if (!this.isConnected()) {
      console.warn('WebSocket not connected, queueing message');
      this.messageQueue.push(message);
      return;
    }

    try {
      this.ws!.send(JSON.stringify(message));
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      this.notifyErrorHandlers({
        type: 'message',
        message: 'Failed to send message',
        timestamp: new Date().toISOString(),
        error
      });
      // Queue the failed message for retry
      this.messageQueue.push(message);
    }
  }

  onMessage(type: string, handler: WebSocketHandler): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, []);
    }
    this.messageHandlers.get(type)?.push(handler);
  }

  onConnect(handler: ConnectionHandler): void {
    this.connectHandlers.push(handler);
  }

  onDisconnect(handler: ConnectionHandler): void {
    this.disconnectHandlers.push(handler);
  }

  onError(handler: WebSocketErrorHandler): void {
    this.errorHandlers.push(handler);
  }

  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message.data);
        } catch (error) {
          console.error(`Error in handler for message type '${message.type}':`, error);
        }
      });
    }
  }

  private reconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1); // Exponential backoff
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (!this.isConnected()) {
        this.connect();
      }
    }, delay);
  }

  private processMessageQueue(): void {
    if (this.messageQueue.length === 0 || !this.isConnected()) {
      return;
    }

    console.log(`Processing ${this.messageQueue.length} queued messages`);
    
    // Clone the queue and clear it
    const queueToProcess = [...this.messageQueue];
    this.messageQueue = [];
    
    // Send all queued messages
    queueToProcess.forEach(message => {
      try {
        this.ws!.send(JSON.stringify(message));
      } catch (error) {
        console.error('Error sending queued message:', error);
        // Requeue failed messages
        this.messageQueue.push(message);
      }
    });
  }

  private notifyConnectHandlers(): void {
    this.connectHandlers.forEach(handler => {
      try {
        handler();
      } catch (error) {
        console.error('Error in connect handler:', error);
      }
    });
  }

  private notifyDisconnectHandlers(): void {
    this.disconnectHandlers.forEach(handler => {
      try {
        handler();
      } catch (error) {
        console.error('Error in disconnect handler:', error);
      }
    });
  }

  private notifyErrorHandlers(error: WebSocketError): void {
    this.errorHandlers.forEach(handler => {
      try {
        handler(error);
      } catch (handlerError) {
        console.error('Error in error handler:', handlerError);
      }
    });
  }

  private clearAllHandlers(): void {
    this.messageHandlers.clear();
    this.connectHandlers = [];
    this.disconnectHandlers = [];
    this.errorHandlers = [];
  }
} 