/**
 * usePullToRefresh Hook
 * 
 * A React hook for implementing pull-to-refresh functionality in scrollable containers.
 * Follows single responsibility principle by focusing only on pull-to-refresh detection.
 */

import { useRef, useState, useCallback, useEffect } from 'react';
import { useAnimationPresets } from '../../theme/useAnimations';

interface PullToRefreshOptions {
  /** Callback function to execute when refresh is triggered */
  onRefresh: () => Promise<any> | void;
  /** Distance in pixels required to trigger refresh (default: 80) */
  threshold?: number;
  /** Maximum pull distance in pixels (default: 120) */
  maxPullDistance?: number;
  /** Resistance factor to make pulling feel natural (default: 0.5) */
  resistance?: number;
  /** Whether to show a visual indicator (default: true) */
  showIndicator?: boolean;
  /** Whether the pull-to-refresh functionality is disabled */
  disabled?: boolean;
}

interface PullToRefreshState {
  /** Whether the user is currently pulling */
  isPulling: boolean;
  /** Whether a refresh is in progress */
  isRefreshing: boolean;
  /** Current pull distance in pixels */
  pullDistance: number;
  /** Progress ratio (0 to 1) of the pull distance relative to threshold */
  progress: number;
}

interface PullToRefreshResult {
  /** Current state of the pull-to-refresh interaction */
  state: PullToRefreshState;
  /** Ref to attach to the scrollable container */
  containerRef: React.RefObject<HTMLElement>;
  /** Ref to attach to the content wrapper */
  contentRef: React.RefObject<HTMLElement>;
  /** Style props to apply to the indicator element */
  indicatorStyle: React.CSSProperties;
  /** Style props to apply to the content wrapper */
  contentStyle: React.CSSProperties;
  /** Manually trigger a refresh */
  triggerRefresh: () => Promise<void>;
  /** Reset the state after a refresh */
  resetState: () => void;
}

/**
 * Hook for implementing pull-to-refresh functionality
 * 
 * @param options Configuration options
 * @returns Object containing refs, state, and style props
 * 
 * @example
 * ```tsx
 * const { containerRef, contentRef, state, indicatorStyle, contentStyle } = usePullToRefresh({
 *   onRefresh: async () => {
 *     await fetchNewData();
 *   },
 *   threshold: 80,
 * });
 * 
 * return (
 *   <div ref={containerRef} className="scroll-container">
 *     <div ref={contentRef} style={contentStyle}>
 *       {state.isPulling && (
 *         <div className="refresh-indicator" style={indicatorStyle}>
 *           {state.isRefreshing ? 'Refreshing...' : 'Pull to refresh'}
 *         </div>
 *       )}
 *       <div className="content">
 *         {items.map(item => <Item key={item.id} data={item} />)}
 *       </div>
 *     </div>
 *   </div>
 * );
 * ```
 */
export function usePullToRefresh({
  onRefresh,
  threshold = 80,
  maxPullDistance = 120,
  resistance = 0.5,
  showIndicator = true,
  disabled = false,
}: PullToRefreshOptions): PullToRefreshResult {
  // Animation presets
  const animations = useAnimationPresets?.() || { transitions: { duration: { normal: '200ms' } } };
  
  // Refs for DOM elements
  const containerRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLElement>(null);
  
  // Track touch and pull state
  const touchStartY = useRef<number | null>(null);
  const initialScrollTop = useRef<number>(0);
  
  // State for pull-to-refresh status
  const [state, setState] = useState<PullToRefreshState>({
    isPulling: false,
    isRefreshing: false,
    pullDistance: 0,
    progress: 0,
  });
  
  // Calculate a restricted pull distance with natural resistance
  const calculatePullDistance = useCallback((touchY: number): number => {
    if (touchStartY.current === null) return 0;
    
    const touchDelta = touchY - touchStartY.current;
    
    // Only trigger pull when scrolled to top and pulling down
    if (touchDelta <= 0 || initialScrollTop.current > 0) {
      return 0;
    }
    
    // Apply resistance to make pull feel more natural
    const restrictedDistance = Math.min(touchDelta * resistance, maxPullDistance);
    return restrictedDistance;
  }, [resistance, maxPullDistance]);
  
  // Calculate progress ratio (0-1) based on current pull distance and threshold
  const calculateProgress = useCallback((distance: number): number => {
    return Math.min(distance / threshold, 1);
  }, [threshold]);
  
  // Handle touch start
  const handleTouchStart = useCallback((e: TouchEvent) => {
    if (disabled || state.isRefreshing) return;
    
    // Store initial touch position
    touchStartY.current = e.touches[0].clientY;
    
    // Store initial scroll position
    initialScrollTop.current = containerRef.current?.scrollTop || 0;
  }, [disabled, state.isRefreshing]);
  
  // Handle touch move
  const handleTouchMove = useCallback((e: TouchEvent) => {
    if (disabled || state.isRefreshing || touchStartY.current === null) return;
    
    const touchY = e.touches[0].clientY;
    const distance = calculatePullDistance(touchY);
    
    // Update state if we're actually pulling
    if (distance > 0) {
      const progress = calculateProgress(distance);
      
      setState({
        isPulling: true,
        isRefreshing: false,
        pullDistance: distance,
        progress,
      });
      
      // Prevent default scrolling when pulling
      if (initialScrollTop.current <= 0) {
        e.preventDefault();
      }
    } else if (state.isPulling) {
      // Reset state if we're no longer pulling
      setState({
        isPulling: false,
        isRefreshing: false,
        pullDistance: 0,
        progress: 0,
      });
    }
  }, [disabled, state.isRefreshing, state.isPulling, calculatePullDistance, calculateProgress]);
  
  // Handle touch end
  const handleTouchEnd = useCallback(async () => {
    if (disabled || touchStartY.current === null) return;
    
    // Check if we've pulled enough to trigger refresh
    if (state.progress >= 1) {
      setState(prev => ({ ...prev, isRefreshing: true }));
      
      try {
        // Execute the refresh callback
        await onRefresh();
      } finally {
        // Reset pull state after refreshing
        setState({
          isPulling: false,
          isRefreshing: false,
          pullDistance: 0,
          progress: 0,
        });
      }
    } else {
      // Not pulled enough, reset state
      setState({
        isPulling: false,
        isRefreshing: false,
        pullDistance: 0,
        progress: 0,
      });
    }
    
    // Reset touch tracking
    touchStartY.current = null;
    initialScrollTop.current = 0;
  }, [disabled, state.progress, onRefresh]);
  
  // Manually trigger refresh
  const triggerRefresh = useCallback(async () => {
    if (disabled || state.isRefreshing) return;
    
    setState(prev => ({ ...prev, isRefreshing: true }));
    
    try {
      await onRefresh();
    } finally {
      setState({
        isPulling: false,
        isRefreshing: false,
        pullDistance: 0,
        progress: 0,
      });
    }
  }, [disabled, state.isRefreshing, onRefresh]);
  
  // Reset state
  const resetState = useCallback(() => {
    setState({
      isPulling: false,
      isRefreshing: false,
      pullDistance: 0,
      progress: 0,
    });
    
    touchStartY.current = null;
    initialScrollTop.current = 0;
  }, []);
  
  // Set up event listeners
  useEffect(() => {
    const container = containerRef.current;
    if (!container || disabled) return;
    
    container.addEventListener('touchstart', handleTouchStart, { passive: true });
    container.addEventListener('touchmove', handleTouchMove, { passive: false });
    container.addEventListener('touchend', handleTouchEnd);
    
    return () => {
      container.removeEventListener('touchstart', handleTouchStart);
      container.removeEventListener('touchmove', handleTouchMove);
      container.removeEventListener('touchend', handleTouchEnd);
    };
  }, [disabled, handleTouchStart, handleTouchMove, handleTouchEnd]);
  
  // Calculate styles for content and indicator
  const contentStyle: React.CSSProperties = {
    transform: state.pullDistance > 0 ? `translateY(${state.pullDistance}px)` : 'none',
    transition: state.isPulling ? 'none' : `transform ${animations.transitions.duration.normal} ease-out`,
  };
  
  const indicatorStyle: React.CSSProperties = {
    opacity: showIndicator ? state.progress : 0,
    transform: `translateY(-100%) translateY(${state.pullDistance}px)`,
    transition: state.isPulling ? 'none' : `transform ${animations.transitions.duration.normal} ease-out`,
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    zIndex: 1,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '50px',
    pointerEvents: 'none',
  };
  
  return {
    state,
    containerRef,
    contentRef,
    indicatorStyle,
    contentStyle,
    triggerRefresh,
    resetState,
  };
} 