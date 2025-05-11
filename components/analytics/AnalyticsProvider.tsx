'use client';

import { ReactNode } from 'react';
import { AnalyticsContext, useAnalyticsState } from '@/hooks/useAnalytics';

interface AnalyticsProviderProps {
  children: ReactNode;
}

/**
 * Provider component for analytics context
 * Makes analytics functionality available throughout the component tree
 */
export function AnalyticsProvider({ children }: AnalyticsProviderProps) {
  const analyticsState = useAnalyticsState();
  
  return (
    <AnalyticsContext.Provider value={analyticsState}>
      {children}
    </AnalyticsContext.Provider>
  );
} 