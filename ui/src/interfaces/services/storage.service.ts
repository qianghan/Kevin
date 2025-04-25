/**
 * Storage Service Interface
 * 
 * Defines the contract for storage-related operations.
 * This follows the Interface Segregation Principle by including
 * only methods related to data storage.
 */

export interface StorageItem {
  key: string;
  value: any;
  expiresAt?: number;
}

export interface StorageOptions {
  /**
   * Time-to-live in seconds
   */
  ttl?: number;
  /**
   * Storage type - local (persists between sessions) or session (cleared on session end)
   */
  storageType?: 'local' | 'session';
}

export interface IStorageService {
  /**
   * Set an item in storage
   * @param key Item key
   * @param value Item value
   * @param options Storage options
   * @returns Promise that resolves when the item is stored
   */
  setItem<T>(key: string, value: T, options?: StorageOptions): Promise<void>;
  
  /**
   * Get an item from storage
   * @param key Item key
   * @returns Promise resolving to the item value or null if not found
   */
  getItem<T>(key: string): Promise<T | null>;
  
  /**
   * Remove an item from storage
   * @param key Item key
   * @returns Promise that resolves when the item is removed
   */
  removeItem(key: string): Promise<void>;
  
  /**
   * Clear all items from storage
   * @param storageType Storage type to clear
   * @returns Promise that resolves when storage is cleared
   */
  clear(storageType?: 'local' | 'session' | 'all'): Promise<void>;
  
  /**
   * Get all keys in storage
   * @param storageType Storage type to get keys from
   * @returns Promise resolving to array of keys
   */
  keys(storageType?: 'local' | 'session'): Promise<string[]>;
  
  /**
   * Check if storage has an item
   * @param key Item key
   * @returns Promise resolving to boolean indicating if the item exists
   */
  hasItem(key: string): Promise<boolean>;
  
  /**
   * Get storage usage information
   * @param storageType Storage type to get usage for
   * @returns Promise resolving to storage usage in bytes
   */
  getUsage(storageType?: 'local' | 'session'): Promise<number>;
} 