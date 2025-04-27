/**
 * API version migration strategies.
 * 
 * This module provides utilities for handling API schema migrations
 * when the API version changes.
 */

import { dataStore } from '../data';
import { cacheService } from '../cache/cache_service';

/**
 * Interface for an API migration strategy
 */
export interface MigrationStrategy<T> {
  /** Source API version */
  fromVersion: string;
  /** Target API version */
  toVersion: string;
  /** Resource type affected by this migration */
  resourceType: string;
  /** Function to migrate data from source to target version */
  migrate: (data: any) => T;
}

/**
 * Interface for migration options
 */
export interface MigrationOptions {
  /** Whether to automatically apply migrations (default: true) */
  autoMigrate?: boolean;
  /** Whether to clear cache after migration (default: true) */
  clearCache?: boolean;
  /** Function to call before migration starts */
  onBeforeMigration?: (fromVersion: string, toVersion: string) => void;
  /** Function to call after migration completes */
  onAfterMigration?: (fromVersion: string, toVersion: string) => void;
}

/**
 * Default migration options
 */
const DEFAULT_MIGRATION_OPTIONS: Required<MigrationOptions> = {
  autoMigrate: true,
  clearCache: true,
  onBeforeMigration: () => {},
  onAfterMigration: () => {},
};

/**
 * Service for managing API version migrations
 */
export class ApiVersionMigrationService {
  private static instance: ApiVersionMigrationService;
  private migrationStrategies: Map<string, MigrationStrategy<any>[]> = new Map();
  private currentVersion: string = '1.0.0';
  private options: Required<MigrationOptions>;
  
  /**
   * Private constructor for singleton pattern
   */
  private constructor(options: MigrationOptions = {}) {
    this.options = { ...DEFAULT_MIGRATION_OPTIONS, ...options };
    
    // Try to load the last known API version
    if (typeof localStorage !== 'undefined') {
      const storedVersion = localStorage.getItem('api-version');
      if (storedVersion) {
        this.currentVersion = storedVersion;
      }
    }
  }
  
  /**
   * Gets the singleton instance of the migration service
   */
  public static getInstance(options?: MigrationOptions): ApiVersionMigrationService {
    if (!ApiVersionMigrationService.instance) {
      ApiVersionMigrationService.instance = new ApiVersionMigrationService(options);
    }
    return ApiVersionMigrationService.instance;
  }
  
  /**
   * Registers a migration strategy
   */
  public registerMigration<T>(strategy: MigrationStrategy<T>): void {
    const { resourceType } = strategy;
    
    if (!this.migrationStrategies.has(resourceType)) {
      this.migrationStrategies.set(resourceType, []);
    }
    
    this.migrationStrategies.get(resourceType)!.push(strategy);
    
    // Sort strategies by fromVersion to ensure correct order
    this.migrationStrategies.get(resourceType)!.sort((a, b) => {
      return this.compareVersions(a.fromVersion, b.fromVersion);
    });
  }
  
  /**
   * Sets the current API version and triggers migrations if needed
   */
  public async setApiVersion(newVersion: string): Promise<void> {
    const oldVersion = this.currentVersion;
    
    // Skip if version hasn't changed
    if (newVersion === oldVersion) {
      return;
    }
    
    // Call before migration hook
    this.options.onBeforeMigration(oldVersion, newVersion);
    
    // Perform automatic migrations if enabled
    if (this.options.autoMigrate) {
      await this.migrateAllResources(oldVersion, newVersion);
    }
    
    // Update stored version
    this.currentVersion = newVersion;
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('api-version', newVersion);
    }
    
    // Clear cache if configured
    if (this.options.clearCache) {
      cacheService.clear();
    }
    
    // Call after migration hook
    this.options.onAfterMigration(oldVersion, newVersion);
  }
  
  /**
   * Gets the current API version
   */
  public getApiVersion(): string {
    return this.currentVersion;
  }
  
  /**
   * Migrates data for a specific resource type
   */
  public async migrateResourceData<T>(
    resourceType: string,
    data: any,
    fromVersion: string = this.currentVersion,
    toVersion?: string
  ): Promise<T> {
    // If no target version specified, use the current version
    const targetVersion = toVersion || this.currentVersion;
    
    // Skip if versions are the same
    if (fromVersion === targetVersion) {
      return data as T;
    }
    
    // Get migration strategies for this resource
    const strategies = this.migrationStrategies.get(resourceType) || [];
    
    // Find applicable migrations
    const applicableMigrations = strategies.filter(strategy => 
      this.compareVersions(strategy.fromVersion, fromVersion) >= 0 && 
      this.compareVersions(strategy.toVersion, targetVersion) <= 0
    );
    
    // Apply migrations in sequence
    let migratedData = data;
    for (const migration of applicableMigrations) {
      migratedData = migration.migrate(migratedData);
    }
    
    return migratedData as T;
  }
  
  /**
   * Migrates all resources from one version to another
   */
  private async migrateAllResources(fromVersion: string, toVersion: string): Promise<void> {
    // Process each resource type with registered migrations
    for (const [resourceType, strategies] of this.migrationStrategies.entries()) {
      // Find applicable migrations for this version transition
      const applicableMigrations = strategies.filter(strategy => 
        this.compareVersions(strategy.fromVersion, fromVersion) >= 0 && 
        this.compareVersions(strategy.toVersion, toVersion) <= 0
      );
      
      if (applicableMigrations.length === 0) {
        continue; // No migrations needed for this resource type
      }
      
      // Get the repository for this resource (if available)
      try {
        // This assumes a naming convention where resource types map to repositories
        // For example, "users" -> getUserRepository()
        const repositoryMethodName = `get${this.capitalizeFirstLetter(resourceType)}Repository`;
        
        // @ts-ignore - Dynamic method access
        if (typeof dataStore[repositoryMethodName] === 'function') {
          // @ts-ignore - Dynamic method access
          const repository = dataStore[repositoryMethodName]();
          
          // Fetch all resources of this type
          const resources = await repository.findAll();
          
          // Apply migrations to each resource
          for (const resource of resources) {
            let migratedResource = resource;
            
            for (const migration of applicableMigrations) {
              migratedResource = migration.migrate(migratedResource);
            }
            
            // Update the resource with the migrated version
            await repository.update(migratedResource.id, migratedResource);
          }
        }
      } catch (error) {
        console.error(`Error migrating resource type ${resourceType}:`, error);
      }
    }
  }
  
  /**
   * Compares two semantic version strings
   * @returns -1 if v1 < v2, 0 if v1 === v2, 1 if v1 > v2
   */
  private compareVersions(v1: string, v2: string): number {
    const parts1 = v1.split('.').map(Number);
    const parts2 = v2.split('.').map(Number);
    
    for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
      const part1 = i < parts1.length ? parts1[i] : 0;
      const part2 = i < parts2.length ? parts2[i] : 0;
      
      if (part1 < part2) return -1;
      if (part1 > part2) return 1;
    }
    
    return 0; // Versions are equal
  }
  
  /**
   * Capitalizes the first letter of a string
   */
  private capitalizeFirstLetter(str: string): string {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }
}

/**
 * Helper to create a migration strategy
 */
export function createMigration<T>(
  fromVersion: string,
  toVersion: string,
  resourceType: string,
  migrateFn: (data: any) => T
): MigrationStrategy<T> {
  return {
    fromVersion,
    toVersion,
    resourceType,
    migrate: migrateFn,
  };
}

// Export singleton instance
export const apiVersionMigration = ApiVersionMigrationService.getInstance(); 