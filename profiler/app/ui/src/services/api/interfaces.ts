/**
 * API Client interfaces for communication with the backend.
 * These interfaces define the contract between the frontend and backend.
 */

// Common types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: 'success' | 'error';
}

export interface WebSocketConfig {
  userId: string;
  apiKey?: string;
  baseUrl?: string;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  error?: string;
  timestamp?: string;
}

export interface WebSocketHandler {
  (data: any): void;
}

export interface WebSocketErrorHandler {
  (error: WebSocketError): void;
}

export interface WebSocketError {
  type: 'connection' | 'message';
  message: string;
  timestamp: string;
  error?: any;
}

export interface ConnectionHandler {
  (): void;
}

// API Client interfaces
export interface IApiClient {
  initialize(): Promise<void>;
  shutdown(): void;
}

export interface IWebSocketClient extends IApiClient {
  connect(): void;
  disconnect(): void;
  sendMessage(type: string, data: any): void;
  onMessage(type: string, handler: WebSocketHandler): void;
  onConnect(handler: ConnectionHandler): void;
  onDisconnect(handler: ConnectionHandler): void;
  onError(handler: WebSocketErrorHandler): void;
  isConnected(): boolean;
}

export interface IProfileClient extends IApiClient {
  getProfile(userId: string): Promise<ApiResponse<any>>;
  updateProfile(userId: string, data: any): Promise<ApiResponse<any>>;
  onProfileUpdate(handler: (profile: any) => void): void;
  connect(): void;
  disconnect(): void;
  sendMessage(type: string, data: any): void;
}

export interface IDocumentClient extends IApiClient {
  uploadDocument(file: File, metadata: any): Promise<ApiResponse<any>>;
  getDocuments(userId: string): Promise<ApiResponse<any[]>>;
  analyzeDocument(documentId: string): Promise<ApiResponse<any>>;
  deleteDocument(documentId: string): Promise<ApiResponse<void>>;
}

export interface IRecommendationClient extends IApiClient {
  getRecommendations(userId: string, context?: any): Promise<ApiResponse<any[]>>;
  refreshRecommendations(userId: string): Promise<ApiResponse<any[]>>;
} 