import { IDiffCalculator, ISyncEntity } from './sync-interfaces';

// Implementation of diff calculator (SRP - Single Responsibility Principle)
export class DiffCalculator<T extends ISyncEntity> implements IDiffCalculator<T> {
  // Calculate differences between old and new versions
  public calculateDiff(oldVersion: T, newVersion: T): Partial<T> {
    const diff: Partial<T> = {};
    
    // Get all keys from both objects
    const allKeys = new Set([...Object.keys(oldVersion), ...Object.keys(newVersion)]);
    
    // Compare each key and add to diff if different
    allKeys.forEach(key => {
      // Skip the id field
      if (key === 'id') return;
      
      const oldValue = oldVersion[key as keyof T];
      const newValue = newVersion[key as keyof T];
      
      // Handle objects recursively
      if (
        typeof oldValue === 'object' && oldValue !== null && 
        typeof newValue === 'object' && newValue !== null &&
        !Array.isArray(oldValue) && !Array.isArray(newValue)
      ) {
        const nestedDiff = this.calculateObjectDiff(oldValue, newValue);
        if (Object.keys(nestedDiff).length > 0) {
          diff[key as keyof T] = nestedDiff as any;
        }
      } 
      // For arrays and primitives, direct comparison
      else if (JSON.stringify(oldValue) !== JSON.stringify(newValue)) {
        diff[key as keyof T] = newValue as any;
      }
    });
    
    return diff;
  }
  
  // Apply a diff to a base version
  public applyDiff(baseVersion: T, diff: Partial<T>): T {
    // Create a deep copy of the base version
    const result = JSON.parse(JSON.stringify(baseVersion)) as T;
    
    // Apply each field in the diff
    Object.keys(diff).forEach(key => {
      const diffValue = diff[key as keyof T];
      const baseValue = result[key as keyof T];
      
      // If both are objects (not arrays), merge them
      if (
        typeof diffValue === 'object' && diffValue !== null && 
        typeof baseValue === 'object' && baseValue !== null &&
        !Array.isArray(diffValue) && !Array.isArray(baseValue)
      ) {
        result[key as keyof T] = { ...baseValue, ...diffValue } as any;
      } 
      // Otherwise replace the value
      else {
        result[key as keyof T] = diffValue as any;
      }
    });
    
    // Update the updatedAt timestamp
    result.updatedAt = new Date().toISOString();
    
    return result;
  }
  
  // Helper method to calculate differences between two objects
  private calculateObjectDiff(oldObj: Record<string, any>, newObj: Record<string, any>): Record<string, any> {
    const diff: Record<string, any> = {};
    
    // Compare old keys with new ones
    Object.keys(newObj).forEach(key => {
      // If key doesn't exist in old object, or values are different
      if (!(key in oldObj) || JSON.stringify(oldObj[key]) !== JSON.stringify(newObj[key])) {
        diff[key] = newObj[key];
      }
    });
    
    return diff;
  }
}

// Factory function to create diff calculator
export const createDiffCalculator = <T extends ISyncEntity>(): IDiffCalculator<T> => {
  return new DiffCalculator<T>();
}; 