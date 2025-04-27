/**
 * Hook for optimistic mutations with automatic rollback on failure.
 * 
 * This hook provides optimistic updates for improved UX, with automatic rollback
 * on mutation failure.
 */

import { useState, useCallback } from 'react';

/**
 * Options for optimistic mutations.
 */
export interface OptimisticMutationOptions<T, TVariables> {
  /** Function to get optimistic data from variables */
  optimisticUpdate: (data: T, variables: TVariables) => T;
  /** Called before mutation starts */
  onMutate?: (variables: TVariables) => void;
  /** Called on successful mutation */
  onSuccess?: (data: T, variables: TVariables) => void;
  /** Called on mutation error */
  onError?: (error: Error, variables: TVariables, rollbackData: T) => void;
  /** Called when mutation completes (success or error) */
  onSettled?: (data: T | null, error: Error | null, variables: TVariables) => void;
}

/**
 * Result of the useOptimisticMutation hook.
 */
export interface OptimisticMutationResult<T, TVariables> {
  /** Current data */
  data: T;
  /** Function to trigger the mutation */
  mutate: (variables: TVariables) => Promise<T>;
  /** Whether the mutation is currently loading */
  isLoading: boolean;
  /** Error from the mutation, if any */
  error: Error | null;
  /** Reset the hook to its initial state */
  reset: () => void;
}

/**
 * Hook for optimistic mutations with automatic rollback on failure.
 * 
 * @param initialData Initial data state
 * @param mutationFn Function that performs the actual mutation
 * @param options Optimistic mutation options
 * @returns Mutation result with data and control functions
 */
export function useOptimisticMutation<T, TVariables>(
  initialData: T,
  mutationFn: (variables: TVariables) => Promise<T>,
  options: OptimisticMutationOptions<T, TVariables>
): OptimisticMutationResult<T, TVariables> {
  const [data, setData] = useState<T>(initialData);
  const [previousData, setPreviousData] = useState<T>(initialData);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  
  /**
   * Resets the hook state to initial values.
   */
  const reset = useCallback(() => {
    setData(initialData);
    setPreviousData(initialData);
    setIsLoading(false);
    setError(null);
  }, [initialData]);
  
  /**
   * Performs the mutation with optimistic updates.
   * 
   * @param variables Variables for the mutation
   * @returns Promise that resolves to the mutation result
   */
  const mutate = useCallback(async (variables: TVariables): Promise<T> => {
    // Store previous data for potential rollback
    setPreviousData(data);
    
    // Call onMutate callback
    options.onMutate?.(variables);
    
    // Apply optimistic update
    const optimisticData = options.optimisticUpdate(data, variables);
    setData(optimisticData);
    
    // Set loading state
    setIsLoading(true);
    setError(null);
    
    try {
      // Perform actual mutation
      const result = await mutationFn(variables);
      
      // Update with actual result
      setData(result);
      
      // Call onSuccess callback
      options.onSuccess?.(result, variables);
      
      // Call onSettled callback
      options.onSettled?.(result, null, variables);
      
      return result;
    } catch (err) {
      // Get error
      const error = err instanceof Error ? err : new Error(String(err));
      
      // Roll back to previous data
      setData(previousData);
      
      // Set error state
      setError(error);
      
      // Call onError callback
      options.onError?.(error, variables, previousData);
      
      // Call onSettled callback
      options.onSettled?.(null, error, variables);
      
      // Re-throw the error for catching at the call site
      throw error;
    } finally {
      // Reset loading state
      setIsLoading(false);
    }
  }, [data, previousData, options, mutationFn]);
  
  return {
    data,
    mutate,
    isLoading,
    error,
    reset
  };
}

/**
 * Hook for optimistic mutations with resource-based updates.
 * 
 * This provides a simpler API for common resource update patterns.
 * 
 * @param resourceMutationFn Function that performs the resource mutation
 * @param options Additional options for the optimistic mutation
 * @returns Mutation result with data and control functions
 */
export function useResourceMutation<T extends { id: string }, TUpdate extends Partial<T>>(
  resources: T[],
  resourceMutationFn: (id: string, update: TUpdate) => Promise<T>,
  options?: Omit<OptimisticMutationOptions<T[], { id: string; update: TUpdate }>, 'optimisticUpdate'>
): OptimisticMutationResult<T[], { id: string; update: TUpdate }> {
  // Define the optimistic update function for resources
  const optimisticUpdate = useCallback((data: T[], variables: { id: string; update: TUpdate }) => {
    const { id, update } = variables;
    
    return data.map(item => {
      if (item.id === id) {
        // Apply update to the matching item
        return {
          ...item,
          ...update
        };
      }
      return item;
    });
  }, []);
  
  // Use the base optimistic mutation hook
  return useOptimisticMutation(
    resources,
    async ({ id, update }) => {
      const updatedResource = await resourceMutationFn(id, update);
      
      // Return the updated resources array
      return resources.map(item => 
        item.id === updatedResource.id ? updatedResource : item
      );
    },
    {
      optimisticUpdate,
      ...options
    }
  );
}

/**
 * Hook for optimistic insertions into a resource collection.
 * 
 * @param resources Initial resources collection
 * @param createFn Function that creates the resource
 * @param options Additional options for the optimistic mutation
 * @returns Mutation result with data and control functions
 */
export function useOptimisticInsert<T, TCreate>(
  resources: T[],
  createFn: (data: TCreate) => Promise<T>,
  options?: Omit<OptimisticMutationOptions<T[], TCreate & { tempId?: string }>, 'optimisticUpdate'>
): OptimisticMutationResult<T[], TCreate & { tempId?: string }> {
  // Generate a temporary ID for optimistic inserts
  const generateTempId = () => `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  // Define the optimistic update function for insertions
  const optimisticUpdate = useCallback((data: T[], variables: TCreate & { tempId?: string }) => {
    const tempId = variables.tempId || generateTempId();
    
    // Create an optimistic item
    const optimisticItem = {
      ...variables,
      id: tempId,
      _isOptimistic: true
    } as unknown as T;
    
    // Add the optimistic item to the collection
    return [...data, optimisticItem];
  }, []);
  
  // Use the base optimistic mutation hook
  return useOptimisticMutation(
    resources,
    async (variables) => {
      // Remove tempId from variables before sending to API
      const { tempId, ...createData } = variables;
      
      // Create the actual resource
      const createdResource = await createFn(createData as TCreate);
      
      // Replace the optimistic item with the created one
      return resources
        .filter(item => !(item as any)._isOptimistic || (item as any).id !== variables.tempId)
        .concat(createdResource);
    },
    {
      optimisticUpdate,
      ...options
    }
  );
} 