'use client';

import { ReactNode } from 'react';
import { RelationshipContext, useRelationshipState } from '@/hooks/useRelationships';

interface RelationshipProviderProps {
  children: ReactNode;
}

/**
 * Provider component for relationship context
 * Makes relationship functionality available throughout the component tree
 */
export function RelationshipProvider({ children }: RelationshipProviderProps) {
  const relationshipState = useRelationshipState();
  
  return (
    <RelationshipContext.Provider value={relationshipState}>
      {children}
    </RelationshipContext.Provider>
  );
} 