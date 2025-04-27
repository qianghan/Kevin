import { IOfflineQueue, ISyncOperation, ISyncEntity } from './sync-interfaces';

// Implementation of offline queue (SRP - Single Responsibility Principle)
export class OfflineQueue implements IOfflineQueue {
  private queue: ISyncOperation<any>[] = [];
  private storageKey = 'offline_sync_queue';
  
  constructor() {
    this.loadFromStorage();
    
    // Handle beforeunload to ensure data is saved
    if (typeof window !== 'undefined') {
      window.addEventListener('beforeunload', () => {
        this.saveToStorage();
      });
    }
  }
  
  private loadFromStorage(): void {
    if (typeof window !== 'undefined') {
      const storedQueue = localStorage.getItem(this.storageKey);
      if (storedQueue) {
        try {
          this.queue = JSON.parse(storedQueue);
        } catch (e) {
          console.error('Failed to parse offline queue from storage', e);
          this.queue = [];
        }
      }
    }
  }
  
  private saveToStorage(): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem(this.storageKey, JSON.stringify(this.queue));
    }
  }
  
  public enqueue(operation: ISyncOperation<any>): void {
    this.queue.push(operation);
    this.saveToStorage();
  }
  
  public dequeue(): ISyncOperation<any> | undefined {
    const operation = this.queue.shift();
    this.saveToStorage();
    return operation;
  }
  
  public getAll(): Array<ISyncOperation<any>> {
    return [...this.queue];
  }
  
  public clear(): void {
    this.queue = [];
    this.saveToStorage();
  }
  
  public size(): number {
    return this.queue.length;
  }
}

// Factory for creating offline queue
export const createOfflineQueue = (): IOfflineQueue => {
  return new OfflineQueue();
}; 