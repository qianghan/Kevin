'use client';

import React, { useState, useEffect } from 'react';

/**
 * A custom hook to safely access route params in client components
 * This handles the async params nature in Next.js App Router
 */
export function useRouteParams<T extends Record<string, string>>(params: T | Promise<T>): T {
  // Create a state to hold the unwrapped params
  const [unwrappedParams, setUnwrappedParams] = useState<T>({} as T);
  
  useEffect(() => {
    // Create a flag to track if the component is still mounted
    let isMounted = true;

    const resolveParams = async () => {
      try {
        let resolvedParams: T;
        
        if (params instanceof Promise) {
          // Resolve the promise
          resolvedParams = await params;
        } else {
          // It's already a plain object
          resolvedParams = params;
        }
        
        // Only update state if component is still mounted
        if (isMounted) {
          setUnwrappedParams(resolvedParams);
        }
      } catch (error) {
        console.error('Error resolving route params:', error);
        // Set empty params object if there's an error
        if (isMounted) {
          setUnwrappedParams({} as T);
        }
      }
    };
    
    // Start resolving the params
    resolveParams();
    
    // Cleanup function to prevent state updates on unmounted component
    return () => {
      isMounted = false;
    };
  }, [params]);
  
  return unwrappedParams;
} 