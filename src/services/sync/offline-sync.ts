/**
 * Offline data synchronization service.
 * 
 * This module provides functionality for caching API responses,
 * handling offline operations, and synchronizing changes when
 * connection is restored.
 */

import { cacheService } from '../cache/cache_service';
import { apiClient } from '../api/error-handling';

/**
 * Pending operation types that can be performed offline
 */
export enum OperationType {
  CREATE = 'create',
  UPDATE = 'update',
  DELETE = 'delete',
}

/**
 * Interface for pending operation
 */
export interface PendingOperation {
  /** Unique identifier for the operation */
  id: string;
  /** Resource endpoint (e.g., "/users") */
  endpoint: string;
  /** HTTP method (e.g., "POST") */
  method: string;
  /** Request body */
  body?: any;
  /** Request headers */
  headers?: Record<string, string>;
  /** Operation type */
  type: OperationType;
  /** When the operation was created */
  timestamp: number;
  /** Number of failed sync attempts */
  failedAttempts: number;
}

/**
 * Interface for the synchronization status
 */
export interface SyncStatus {
  /** Whether we're currently online */
  isOnline: boolean;
  /** Whether sync is currently in progress */
  isSyncing: boolean;
  /** Number of pending operations */
  pendingCount: number;
  /** Last time sync completed successfully */
  lastSyncTime: number | null;
  /** Last error encountered during sync */
  lastError: Error | null;
}

/**
 * Options for the offline sync service
 */
export interface OfflineSyncOptions {
  /** Storage key for pending operations */
  storageKey?: string;
  /** Auto sync interval in milliseconds (0 to disable) */
  autoSyncInterval?: number;
  /** Maximum number of sync retries per operation */
  maxRetries?: number;
  /** Whether to sync immediately when online */
  syncOnReconnect?: boolean;
}

/**
 * Default options for the offline sync service
 */
const DEFAULT_SYNC_OPTIONS: OfflineSyncOptions = {
  storageKey: 'offline-operations',
  autoSyncInterval: 60000, // 1 minute
  maxRetries: 5,
  syncOnReconnect: true,
};

/**
 * Offline synchronization service for handling offline operations
 * and syncing data when connection is restored.
 */
export class OfflineSyncService {
  private static instance: OfflineSyncService;
  private pendingOperations: PendingOperation[] = [];
  private syncStatus: SyncStatus = {
    isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
    isSyncing: false,
    pendingCount: 0,
    lastSyncTime: null,
    lastError: null,
  };
  private options: Required<OfflineSyncOptions>;
  private syncInterval: ReturnType<typeof setInterval> | null = null;
  private listeners: Array<(status: SyncStatus) => void> = [];
  
  /**
   * Private constructor for singleton pattern
   */
  private constructor(options: OfflineSyncOptions = {}) {
    this.options = { ...DEFAULT_SYNC_OPTIONS, ...options } as Required<OfflineSyncOptions>;
    
    // Load pending operations from storage
    this.loadFromStorage();
    
    // Set initial pending count
    this.syncStatus.pendingCount = this.pendingOperations.length;
    
    // Set up online/offline event listeners
    if (typeof window !== 'undefined') {
      window.addEventListener('online', this.handleOnline);
      window.addEventListener('offline', this.handleOffline);
      
      // Start auto sync if enabled
      if (this.options.autoSyncInterval > 0) {
        this.startAutoSync();
      }
    }
  }
  
  /**
   * Gets the singleton instance of the offline sync service
   */
  public static getInstance(options?: OfflineSyncOptions): OfflineSyncService {
    if (!OfflineSyncService.instance) {
      OfflineSyncService.instance = new OfflineSyncService(options);
    }
    return OfflineSyncService.instance;
  }
  
  /**
   * Adds an operation to the pending queue
   */
  public addOperation(operation: Omit<PendingOperation, 'id' | 'timestamp' | 'failedAttempts'>): string {
    const id = `op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const timestamp = Date.now();
    
    const pendingOperation: PendingOperation = {
      ...operation,
      id,
      timestamp,
      failedAttempts: 0,
    };
    
    this.pendingOperations.push(pendingOperation);
    this.syncStatus.pendingCount = this.pendingOperations.length;
    
    // Save to storage
    this.saveToStorage();
    
    // Notify listeners
    this.notifyListeners();
    
    // Try to sync if we're online
    if (this.syncStatus.isOnline && !this.syncStatus.isSyncing) {
      this.sync();
    }
    
    return id;
  }
  
  /**
   * Removes an operation from the pending queue
   */
  public removeOperation(id: string): boolean {
    const initialLength = this.pendingOperations.length;
    this.pendingOperations = this.pendingOperations.filter(op => op.id !== id);
    
    const removed = initialLength !== this.pendingOperations.length;
    
    if (removed) {
      this.syncStatus.pendingCount = this.pendingOperations.length;
      this.saveToStorage();
      this.notifyListeners();
    }
    
    return removed;
  }
  
  /**
   * Gets the current sync status
   */
  public getStatus(): SyncStatus {
    return { ...this.syncStatus };
  }
  
  /**
   * Subscribes to sync status changes
   */
  public subscribe(listener: (status: SyncStatus) => void): () => void {
    this.listeners.push(listener);
    
    // Call with current status
    listener({ ...this.syncStatus });
    
    // Return unsubscribe function
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }
  
  /**
   * Manually triggers synchronization
   */
  public async sync(): Promise<boolean> {
    // Don't sync if we're offline or already syncing
    if (!this.syncStatus.isOnline || this.syncStatus.isSyncing) {
      return false;
    }
    
    try {
      this.syncStatus.isSyncing = true;
      this.notifyListeners();
      
      // Process operations in order (oldest first)
      const sortedOperations = [...this.pendingOperations].sort((a, b) => a.timestamp - b.timestamp);
      
      let success = true;
      
      for (const operation of sortedOperations) {
        try {
          // Attempt to process the operation
          await this.processOperation(operation);
          
          // Remove from pending if successful
          this.removeOperation(operation.id);
        } catch (error) {
          success = false;
          
          // Increment failed attempts
          operation.failedAttempts++;
          
          // Remove if exceeded max retries
          if (operation.failedAttempts > this.options.maxRetries) {
            this.removeOperation(operation.id);
          } else {
            // Update operation in storage
            this.saveToStorage();
          }
          
          // Store last error
          this.syncStatus.lastError = error instanceof Error ? error : new Error(String(error));
        }
      }
      
      // Update status
      this.syncStatus.lastSyncTime = Date.now();
      
      return success;
    } catch (error) {
      this.syncStatus.lastError = error instanceof Error ? error : new Error(String(error));
      return false;
    } finally {
      this.syncStatus.isSyncing = false;
      this.syncStatus.pendingCount = this.pendingOperations.length;
      this.notifyListeners();
    }
  }
  
  /**
   * Initializes or invalidates cached data for the given resource
   */
  public async initializeCache<T>(
    resourceEndpoint: string,
    fetchFn: () => Promise<T>,
    options?: { ttl?: number }
  ): Promise<T> {
    try {
      // Try to fetch fresh data
      const data = await fetchFn();
      
      // Cache the data
      cacheService.set({
        resourceType: resourceEndpoint,
        ttl: options?.ttl,
      }, data);
      
      return data;
    } catch (error) {
      // If offline, try to get from cache
      if (!this.syncStatus.isOnline) {
        const cachedData = await cacheService.get<T>({
          resourceType: resourceEndpoint,
        }, async () => {
          throw new Error(`No cached data available for ${resourceEndpoint}`);
        });
        
        return cachedData;
      }
      
      // Otherwise rethrow the error
      throw error;
    }
  }
  
  /**
   * Registers fetcher functions for resources to enable offline fetching
   */
  public registerResource<T>(
    resourceEndpoint: string,
    fetchResource: (id?: string) => Promise<T>,
    options?: { ttl?: number }
  ): {
    fetch: (id?: string) => Promise<T>,
    fetchWithCache: (id?: string, force?: boolean) => Promise<T>,
    create: <D>(data: D) => Promise<T>,
    update: <D>(id: string, data: D) => Promise<T>,
    remove: (id: string) => Promise<boolean>
  } {
    // Wrapper for fetch that handles offline
    const fetch = async (id?: string): Promise<T> => {
      try {
        return await fetchResource(id);
      } catch (error) {
        if (!this.syncStatus.isOnline) {
          // Try to get from cache when offline
          const cacheKey = {
            resourceType: resourceEndpoint,
            id: id,
          };
          
          return await cacheService.get<T>(cacheKey, async () => {
            throw new Error(`No cached data available for ${resourceEndpoint}${id ? `/${id}` : ''}`);
          });
        }
        
        throw error;
      }
    };
    
    // Fetch with cache first approach
    const fetchWithCache = async (id?: string, force = false): Promise<T> => {
      const cacheKey = {
        resourceType: resourceEndpoint,
        id: id,
        ttl: options?.ttl,
      };
      
      if (force) {
        try {
          const data = await fetchResource(id);
          cacheService.set(cacheKey, data);
          return data;
        } catch (error) {
          if (!this.syncStatus.isOnline) {
            return await cacheService.get<T>(cacheKey, async () => {
              throw new Error(`No cached data available for ${resourceEndpoint}${id ? `/${id}` : ''}`);
            });
          }
          throw error;
        }
      }
      
      return await cacheService.get<T>(cacheKey, async () => {
        return await fetchResource(id);
      });
    };
    
    // Create with offline support
    const create = async <D>(data: D): Promise<T> => {
      try {
        // Try online first
        const response = await apiClient<T>(`${resourceEndpoint}`, {
          method: 'POST',
          body: JSON.stringify(data),
        });
        
        return response;
      } catch (error) {
        if (!this.syncStatus.isOnline) {
          // Queue the operation for later
          this.addOperation({
            endpoint: resourceEndpoint,
            method: 'POST',
            body: data,
            type: OperationType.CREATE,
            headers: {
              'Content-Type': 'application/json',
            },
          });
          
          // Return a fake result
          return {
            _id: `temp_${Date.now()}`,
            _offline: true,
            ...data,
          } as unknown as T;
        }
        
        throw error;
      }
    };
    
    // Update with offline support
    const update = async <D>(id: string, data: D): Promise<T> => {
      try {
        // Try online first
        const response = await apiClient<T>(`${resourceEndpoint}/${id}`, {
          method: 'PUT',
          body: JSON.stringify(data),
        });
        
        // Invalidate cache
        cacheService.delete({
          resourceType: resourceEndpoint,
          id: id,
        });
        
        return response;
      } catch (error) {
        if (!this.syncStatus.isOnline) {
          // Queue the operation for later
          this.addOperation({
            endpoint: `${resourceEndpoint}/${id}`,
            method: 'PUT',
            body: data,
            type: OperationType.UPDATE,
            headers: {
              'Content-Type': 'application/json',
            },
          });
          
          // Optimistically update cache
          try {
            const currentData = await fetchWithCache(id);
            const updatedData = {
              ...currentData,
              ...data,
              _offline: true,
            };
            
            cacheService.set({
              resourceType: resourceEndpoint,
              id: id,
            }, updatedData);
            
            return updatedData;
          } catch {
            // If we can't get current data, just return the update
            return {
              _id: id,
              _offline: true,
              ...data,
            } as unknown as T;
          }
        }
        
        throw error;
      }
    };
    
    // Delete with offline support
    const remove = async (id: string): Promise<boolean> => {
      try {
        // Try online first
        await apiClient(`${resourceEndpoint}/${id}`, {
          method: 'DELETE',
        });
        
        // Invalidate cache
        cacheService.delete({
          resourceType: resourceEndpoint,
          id: id,
        });
        
        return true;
      } catch (error) {
        if (!this.syncStatus.isOnline) {
          // Queue the operation for later
          this.addOperation({
            endpoint: `${resourceEndpoint}/${id}`,
            method: 'DELETE',
            type: OperationType.DELETE,
          });
          
          // Invalidate cache
          cacheService.delete({
            resourceType: resourceEndpoint,
            id: id,
          });
          
          return true;
        }
        
        throw error;
      }
    };
    
    return {
      fetch,
      fetchWithCache,
      create,
      update,
      remove,
    };
  }
  
  /**
   * Clears all pending operations
   */
  public clearPendingOperations(): void {
    this.pendingOperations = [];
    this.syncStatus.pendingCount = 0;
    this.saveToStorage();
    this.notifyListeners();
  }
  
  /**
   * Processes a single operation
   */
  private async processOperation(operation: PendingOperation): Promise<void> {
    const { endpoint, method, body, headers } = operation;
    
    const requestOptions: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    };
    
    if (body) {
      requestOptions.body = JSON.stringify(body);
    }
    
    await apiClient(endpoint, requestOptions);
    
    // Invalidate cache for this resource
    const resourcePath = endpoint.split('/')[1]; // Extract resource from path
    if (resourcePath) {
      cacheService.invalidateResourceType(resourcePath);
    }
  }
  
  /**
   * Handles the online event
   */
  private handleOnline = async (): Promise<void> => {
    this.syncStatus.isOnline = true;
    this.notifyListeners();
    
    // Sync if there are pending operations and we're configured to sync on reconnect
    if (this.options.syncOnReconnect && this.pendingOperations.length > 0) {
      await this.sync();
    }
  };
  
  /**
   * Handles the offline event
   */
  private handleOffline = (): void => {
    this.syncStatus.isOnline = false;
    this.notifyListeners();
  };
  
  /**
   * Starts auto sync interval
   */
  private startAutoSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    
    this.syncInterval = setInterval(() => {
      if (this.syncStatus.isOnline && !this.syncStatus.isSyncing && this.pendingOperations.length > 0) {
        this.sync();
      }
    }, this.options.autoSyncInterval);
  }
  
  /**
   * Stops auto sync interval
   */
  private stopAutoSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }
  
  /**
   * Notifies all listeners of status changes
   */
  private notifyListeners(): void {
    const status = { ...this.syncStatus };
    this.listeners.forEach(listener => listener(status));
  }
  
  /**
   * Saves pending operations to storage
   */
  private saveToStorage(): void {
    if (typeof localStorage !== 'undefined') {
      try {
        localStorage.setItem(
          this.options.storageKey,
          JSON.stringify(this.pendingOperations)
        );
      } catch (error) {
        console.error('Failed to save pending operations to storage:', error);
      }
    }
  }
  
  /**
   * Loads pending operations from storage
   */
  private loadFromStorage(): void {
    if (typeof localStorage !== 'undefined') {
      try {
        const stored = localStorage.getItem(this.options.storageKey);
        if (stored) {
          this.pendingOperations = JSON.parse(stored);
        }
      } catch (error) {
        console.error('Failed to load pending operations from storage:', error);
        this.pendingOperations = [];
      }
    }
  }
  
  /**
   * Cleans up event listeners and intervals
   */
  public dispose(): void {
    if (typeof window !== 'undefined') {
      window.removeEventListener('online', this.handleOnline);
      window.removeEventListener('offline', this.handleOffline);
    }
    
    this.stopAutoSync();
    this.listeners = [];
  }
}

// Export singleton instance
export const offlineSyncService = OfflineSyncService.getInstance(); 