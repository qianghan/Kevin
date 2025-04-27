import { ISyncEntity, IConflictResolution } from './sync-interfaces';
import { DiffCalculator } from './diff-calculator';

// Base conflict resolver interface
export interface IConflictResolver<T extends ISyncEntity> {
  resolve(clientVersion: T, serverVersion: T): T;
}

// Last-write-wins strategy (SRP - Single Responsibility Principle)
export class LastWriteWinsResolver<T extends ISyncEntity> implements IConflictResolver<T> {
  resolve(clientVersion: T, serverVersion: T): T {
    const clientDate = new Date(clientVersion.updatedAt);
    const serverDate = new Date(serverVersion.updatedAt);
    
    return clientDate > serverDate ? clientVersion : serverVersion;
  }
}

// Merge strategy that tries to combine changes (SRP)
export class MergeResolver<T extends ISyncEntity> implements IConflictResolver<T> {
  private diffCalculator: DiffCalculator<T>;
  
  constructor() {
    this.diffCalculator = new DiffCalculator<T>();
  }
  
  resolve(clientVersion: T, serverVersion: T): T {
    // Get base version (the common ancestor if available, or use server version)
    const baseVersion = serverVersion;
    
    // Calculate diffs
    const clientDiff = this.diffCalculator.calculateDiff(baseVersion, clientVersion);
    const serverDiff = this.diffCalculator.calculateDiff(baseVersion, serverVersion);
    
    // Start with the server version as the base
    let resolvedVersion = JSON.parse(JSON.stringify(serverVersion)) as T;
    
    // Apply client changes that don't conflict
    Object.keys(clientDiff).forEach(key => {
      const typedKey = key as keyof T;
      
      // Skip if server also changed this field (conflict)
      if (typedKey in serverDiff) {
        // For object fields, try to merge recursively
        if (
          typeof clientDiff[typedKey] === 'object' && 
          typeof serverDiff[typedKey] === 'object' &&
          !Array.isArray(clientDiff[typedKey]) && 
          !Array.isArray(serverDiff[typedKey])
        ) {
          // Merge objects recursively
          resolvedVersion[typedKey] = {
            ...resolvedVersion[typedKey],
            ...serverDiff[typedKey],
            ...clientDiff[typedKey]
          } as any;
        }
        // For arrays and primitives, prefer the server version
      } else {
        // No conflict, apply client change
        resolvedVersion[typedKey] = clientDiff[typedKey] as any;
      }
    });
    
    // Update the timestamp to now
    resolvedVersion.updatedAt = new Date().toISOString();
    
    return resolvedVersion;
  }
}

// Client-wins strategy (SRP)
export class ClientWinsResolver<T extends ISyncEntity> implements IConflictResolver<T> {
  resolve(clientVersion: T, serverVersion: T): T {
    // Just return the client version with updated timestamp
    const result = { ...clientVersion };
    result.updatedAt = new Date().toISOString();
    return result;
  }
}

// Server-wins strategy (SRP)
export class ServerWinsResolver<T extends ISyncEntity> implements IConflictResolver<T> {
  resolve(clientVersion: T, serverVersion: T): T {
    // Just return the server version
    return serverVersion;
  }
}

// Factory for creating conflict resolvers
export const createConflictResolver = <T extends ISyncEntity>(
  strategy: 'last-write-wins' | 'merge' | 'client-wins' | 'server-wins' = 'merge'
): IConflictResolver<T> => {
  switch (strategy) {
    case 'last-write-wins':
      return new LastWriteWinsResolver<T>();
    case 'merge':
      return new MergeResolver<T>();
    case 'client-wins':
      return new ClientWinsResolver<T>();
    case 'server-wins':
      return new ServerWinsResolver<T>();
    default:
      return new MergeResolver<T>();
  }
}; 