import { 
  ISyncService, 
  ISyncEntity, 
  ISyncOperation, 
  IRealTimeSync,
  IOfflineQueue
} from './sync-interfaces';
import { IApiClient } from '../api/api-client';
import { OfflineQueue } from './offline-queue';
import { createRealTimeSync } from './real-time-sync';
import { createConflictResolver, IConflictResolver } from './conflict-resolver';
import { createDiffCalculator, DiffCalculator } from './diff-calculator';

// Main Sync Service implementation (SRP)
export class SyncService implements ISyncService {
  private apiClient: IApiClient;
  private offlineQueue: IOfflineQueue;
  private realTimeSync: IRealTimeSync | null = null;
  private isNetworkOnline: boolean = true;
  private syncInProgress: boolean = false;
  private clientId: string;
  private entityStore: Map<string, Map<string, ISyncEntity>> = new Map();
  private conflictResolvers: Map<string, IConflictResolver<any>> = new Map();
  private diffCalculators: Map<string, DiffCalculator<any>> = new Map();
  
  constructor(
    apiClient: IApiClient,
    offlineQueue?: IOfflineQueue,
    realTimeSyncUrl?: string
  ) {
    this.apiClient = apiClient;
    this.offlineQueue = offlineQueue || new OfflineQueue();
    this.clientId = this.generateClientId();
    
    // Set up network status listeners
    if (typeof window !== 'undefined') {
      window.addEventListener('online', this.handleOnline.bind(this));
      window.addEventListener('offline', this.handleOffline.bind(this));
      this.isNetworkOnline = navigator.onLine;
      
      // Set up real-time sync if URL is provided
      if (realTimeSyncUrl) {
        this.enableRealTime(realTimeSyncUrl);
      }
    }
  }
  
  private generateClientId(): string {
    return `client_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
  }
  
  // Handle going back online
  private async handleOnline(): Promise<void> {
    this.isNetworkOnline = true;
    console.log('Network is online, processing offline queue...');
    await this.goOnline();
  }
  
  // Handle going offline
  private handleOffline(): void {
    this.isNetworkOnline = false;
    console.log('Network is offline, operations will be queued');
    this.goOffline();
  }
  
  // Get conflict resolver for entity type
  private getConflictResolver<T extends ISyncEntity>(entityType: string): IConflictResolver<T> {
    if (!this.conflictResolvers.has(entityType)) {
      this.conflictResolvers.set(entityType, createConflictResolver<T>('merge'));
    }
    return this.conflictResolvers.get(entityType) as IConflictResolver<T>;
  }
  
  // Get diff calculator for entity type
  private getDiffCalculator<T extends ISyncEntity>(entityType: string): DiffCalculator<T> {
    if (!this.diffCalculators.has(entityType)) {
      this.diffCalculators.set(entityType, createDiffCalculator<T>());
    }
    return this.diffCalculators.get(entityType) as DiffCalculator<T>;
  }
  
  // Get entity store for entity type
  private getEntityStore<T extends ISyncEntity>(entityType: string): Map<string, T> {
    if (!this.entityStore.has(entityType)) {
      this.entityStore.set(entityType, new Map<string, T>());
    }
    return this.entityStore.get(entityType) as Map<string, T>;
  }
  
  // Store entity in local cache
  private storeEntity<T extends ISyncEntity>(entityType: string, entity: T): void {
    const store = this.getEntityStore<T>(entityType);
    store.set(entity.id, entity);
  }
  
  // Create a sync operation
  private createSyncOperation<T extends ISyncEntity>(
    type: 'create' | 'update' | 'delete',
    entityType: string,
    entity: T
  ): ISyncOperation<T> {
    return {
      type,
      entityType,
      entity,
      timestamp: Date.now(),
      clientId: this.clientId
    };
  }
  
  // Main sync method
  public async sync(): Promise<void> {
    if (this.syncInProgress || !this.isNetworkOnline) return;
    
    this.syncInProgress = true;
    
    try {
      // Process offline queue first
      await this.processOfflineQueue();
      
      // Sync each entity type
      for (const [entityType, store] of this.entityStore.entries()) {
        await this.syncEntityType(entityType);
      }
    } catch (error) {
      console.error('Error during sync', error);
    } finally {
      this.syncInProgress = false;
    }
  }
  
  // Process offline queue
  private async processOfflineQueue(): Promise<void> {
    const operations = this.offlineQueue.getAll();
    
    if (operations.length === 0) return;
    
    console.log(`Processing ${operations.length} offline operations`);
    
    // Process operations in order
    for (const operation of operations) {
      try {
        switch (operation.type) {
          case 'create':
          case 'update':
            await this.syncEntity(operation.entityType, operation.entity);
            break;
          case 'delete':
            // Handle delete operations
            await this.apiClient.delete(`/${operation.entityType}/${operation.entity.id}`);
            break;
        }
        
        // Remove the processed operation
        this.offlineQueue.dequeue();
      } catch (error) {
        console.error('Error processing offline operation', error);
        break;
      }
    }
  }
  
  // Sync specific entity type
  private async syncEntityType(entityType: string): Promise<void> {
    try {
      // Fetch all entities of this type from server
      const response = await this.apiClient.get<{ data: ISyncEntity[] }>(`/${entityType}`);
      const serverEntities = response.data.data;
      
      // Get local store
      const localStore = this.getEntityStore(entityType);
      
      // Create maps for easy lookup
      const serverEntitiesMap = new Map<string, ISyncEntity>();
      serverEntities.forEach(entity => serverEntitiesMap.set(entity.id, entity));
      
      // Sync each entity
      for (const [id, localEntity] of localStore.entries()) {
        const serverEntity = serverEntitiesMap.get(id);
        
        if (serverEntity) {
          // Entity exists on both sides, resolve conflicts
          await this.resolveConflict(entityType, localEntity, serverEntity);
        } else {
          // Entity exists locally but not on server, create it
          await this.apiClient.post(`/${entityType}`, localEntity);
        }
      }
      
      // Add entities that exist on server but not locally
      for (const [id, serverEntity] of serverEntitiesMap.entries()) {
        if (!localStore.has(id)) {
          this.storeEntity(entityType, serverEntity);
        }
      }
    } catch (error) {
      console.error(`Error syncing entity type: ${entityType}`, error);
    }
  }
  
  // Sync a specific entity
  public async syncEntity<T extends ISyncEntity>(entityType: string, entity: T): Promise<T> {
    if (!this.isNetworkOnline) {
      // Queue operation for later if offline
      this.offlineQueue.enqueue(this.createSyncOperation('update', entityType, entity));
      this.storeEntity(entityType, entity);
      return entity;
    }
    
    try {
      // Get the existing entity from server if it exists
      try {
        const response = await this.apiClient.get<{ data: T }>(`/${entityType}/${entity.id}`);
        const serverEntity = response.data.data;
        
        // Resolve any conflicts
        const resolvedEntity = await this.resolveConflict(entityType, entity, serverEntity);
        
        // Update on server
        await this.apiClient.put(`/${entityType}/${entity.id}`, resolvedEntity);
        
        // Store the updated entity
        this.storeEntity(entityType, resolvedEntity);
        
        // Notify via real-time if enabled
        this.notifyRealTimeUpdate(entityType, resolvedEntity);
        
        return resolvedEntity;
      } catch (error) {
        // Entity probably doesn't exist, create it
        const response = await this.apiClient.post<{ data: T }>(`/${entityType}`, entity);
        const createdEntity = response.data.data;
        
        // Store the created entity
        this.storeEntity(entityType, createdEntity);
        
        // Notify via real-time if enabled
        this.notifyRealTimeUpdate(entityType, createdEntity);
        
        return createdEntity;
      }
    } catch (error) {
      console.error(`Error syncing entity: ${entityType}/${entity.id}`, error);
      
      // Queue for later in case of error
      this.offlineQueue.enqueue(this.createSyncOperation('update', entityType, entity));
      this.storeEntity(entityType, entity);
      
      return entity;
    }
  }
  
  // Resolve conflicts between client and server versions
  public async resolveConflict<T extends ISyncEntity>(
    entityType: string, 
    clientVersion: T, 
    serverVersion: T
  ): Promise<T> {
    // Use conflict resolver for this entity type
    const resolver = this.getConflictResolver<T>(entityType);
    const resolvedEntity = resolver.resolve(clientVersion, serverVersion);
    
    // Store resolved entity
    this.storeEntity(entityType, resolvedEntity);
    
    return resolvedEntity;
  }
  
  // Notify about entity updates via real-time
  private notifyRealTimeUpdate<T extends ISyncEntity>(entityType: string, entity: T): void {
    if (this.realTimeSync) {
      this.realTimeSync.publish(entityType, entity);
    }
  }
  
  // Enable real-time sync
  public enableRealTime(url?: string): void {
    if (!this.realTimeSync && typeof window !== 'undefined') {
      const wsUrl = url || `wss://${window.location.host}/api/ws`;
      this.realTimeSync = createRealTimeSync(wsUrl);
      
      // Set up listeners for each entity type
      for (const entityType of this.entityStore.keys()) {
        this.setupRealTimeListener(entityType);
      }
    }
  }
  
  // Disable real-time sync
  public disableRealTime(): void {
    if (this.realTimeSync) {
      this.realTimeSync = null;
    }
  }
  
  // Setup real-time listener for entity type
  private setupRealTimeListener(entityType: string): void {
    if (!this.realTimeSync) return;
    
    this.realTimeSync.subscribe(entityType, (data) => {
      // Skip updates from this client
      if (data.clientId === this.clientId) return;
      
      // Update local store
      this.storeEntity(entityType, data);
    });
  }
  
  // Handle offline mode
  public goOffline(): void {
    this.isNetworkOnline = false;
  }
  
  // Handle online mode
  public async goOnline(): Promise<void> {
    this.isNetworkOnline = true;
    await this.sync();
  }
  
  // Check if online
  public isOnline(): boolean {
    return this.isNetworkOnline;
  }
}

// Factory for creating the sync service
export const createSyncService = (
  apiClient: IApiClient,
  offlineQueue?: IOfflineQueue,
  realTimeSyncUrl?: string
): ISyncService => {
  return new SyncService(apiClient, offlineQueue, realTimeSyncUrl);
}; 