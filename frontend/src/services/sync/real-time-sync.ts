import { IRealTimeSync } from './sync-interfaces';

// Implementation of real-time sync service using Websockets (SRP)
export class WebSocketRealTimeSync implements IRealTimeSync {
  private socket: WebSocket | null = null;
  private subscribers: Map<string, Array<(data: any) => void>> = new Map();
  private isConnected: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectInterval: number = 3000; // 3 seconds
  private reconnectTimer: NodeJS.Timeout | null = null;
  private clientId: string;
  
  constructor(url: string) {
    this.clientId = this.generateClientId();
    this.connect(url);
  }
  
  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }
  
  private connect(url: string): void {
    try {
      this.socket = new WebSocket(url);
      
      this.socket.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        console.log('WebSocket connection established');
        
        // Send authentication message if needed
        this.socket?.send(JSON.stringify({
          type: 'connect',
          clientId: this.clientId
        }));
      };
      
      this.socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          // Process the message
          if (message.type === 'update' && message.entityType) {
            this.notifySubscribers(message.entityType, message.data);
          }
        } catch (error) {
          console.error('Error processing websocket message', error);
        }
      };
      
      this.socket.onclose = () => {
        this.isConnected = false;
        this.handleDisconnect();
      };
      
      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnected = false;
        this.handleDisconnect();
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection', error);
      this.handleDisconnect();
    }
  }
  
  private handleDisconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      
      // Clear any existing reconnect timer
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer);
      }
      
      // Attempt to reconnect after specified interval
      this.reconnectTimer = setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        this.connect(`wss://${window.location.host}/api/ws`);
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnect attempts reached. Giving up.');
    }
  }
  
  public subscribe(entityType: string, callback: (data: any) => void): () => void {
    if (!this.subscribers.has(entityType)) {
      this.subscribers.set(entityType, []);
    }
    
    const callbacks = this.subscribers.get(entityType)!;
    callbacks.push(callback);
    
    // Return unsubscribe function
    return () => {
      const index = callbacks.indexOf(callback);
      if (index !== -1) {
        callbacks.splice(index, 1);
      }
    };
  }
  
  public unsubscribe(entityType: string): void {
    this.subscribers.delete(entityType);
  }
  
  public publish(entityType: string, data: any): void {
    if (this.isConnected && this.socket) {
      try {
        this.socket.send(JSON.stringify({
          type: 'update',
          entityType,
          data,
          clientId: this.clientId
        }));
      } catch (error) {
        console.error('Error publishing message', error);
      }
    } else {
      console.warn('Cannot publish message: WebSocket not connected');
    }
  }
  
  private notifySubscribers(entityType: string, data: any): void {
    const callbacks = this.subscribers.get(entityType);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in subscriber callback', error);
        }
      });
    }
  }
  
  public disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    this.isConnected = false;
    this.subscribers.clear();
  }
}

// Factory for creating real-time sync service
export const createRealTimeSync = (url: string = `wss://${window.location.host}/api/ws`): IRealTimeSync => {
  return new WebSocketRealTimeSync(url);
}; 