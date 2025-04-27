// Define synchronization interfaces (ISP - Interface Segregation Principle)

// Interface for entity type
export interface ISyncEntity {
  id: string;
  updatedAt: string;
  [key: string]: any;
}

// Interface for a synchronization operation
export interface ISyncOperation<T extends ISyncEntity> {
  type: 'create' | 'update' | 'delete';
  entityType: string; // e.g., 'user', 'project', 'task'
  entity: T;
  timestamp: number;
  clientId: string;
}

// Interface for conflict resolution
export interface IConflictResolution<T extends ISyncEntity> {
  clientVersion: T;
  serverVersion: T;
  resolvedVersion: T;
}

// Interface for offline queue
export interface IOfflineQueue {
  enqueue(operation: ISyncOperation<any>): void;
  dequeue(): ISyncOperation<any> | undefined;
  getAll(): Array<ISyncOperation<any>>;
  clear(): void;
  size(): number;
}

// Interface for data difference calculation
export interface IDiffCalculator<T extends ISyncEntity> {
  calculateDiff(oldVersion: T, newVersion: T): Partial<T>;
  applyDiff(baseVersion: T, diff: Partial<T>): T;
}

// Interface for real-time updates
export interface IRealTimeSync {
  subscribe(entityType: string, callback: (data: any) => void): () => void;
  unsubscribe(entityType: string): void;
  publish(entityType: string, data: any): void;
}

// Base sync service interface
export interface ISyncService {
  // Core sync methods
  sync(): Promise<void>;
  syncEntity<T extends ISyncEntity>(entityType: string, entity: T): Promise<T>;
  
  // Real-time functionality
  enableRealTime(): void;
  disableRealTime(): void;
  
  // Offline handling
  goOffline(): void;
  goOnline(): Promise<void>;
  isOnline(): boolean;
  
  // Conflict resolution
  resolveConflict<T extends ISyncEntity>(clientVersion: T, serverVersion: T): Promise<T>;
} 