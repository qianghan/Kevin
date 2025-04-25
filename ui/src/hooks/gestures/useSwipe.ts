/**
 * useSwipe Hook
 * 
 * A React hook for detecting swipe gestures in different directions.
 * Follows single responsibility principle by focusing only on swipe detection.
 */

import { useRef, useState, useCallback } from 'react';

type SwipeDirection = 'left' | 'right' | 'up' | 'down';

interface SwipeHandlers {
  onTouchStart: (e: React.TouchEvent) => void;
  onTouchMove: (e: React.TouchEvent) => void;
  onTouchEnd: (e: React.TouchEvent) => void;
  onMouseDown: (e: React.MouseEvent) => void;
  onMouseMove: (e: React.MouseEvent) => void;
  onMouseUp: (e: React.MouseEvent) => void;
  onMouseLeave: (e: React.MouseEvent) => void;
}

interface SwipeState {
  swiping: boolean;
  direction: SwipeDirection | null;
  deltaX: number;
  deltaY: number;
  absX: number;
  absY: number;
}

interface UseSwipeOptions {
  /** Minimum distance in pixels to trigger a swipe */
  threshold?: number;
  /** Whether to prevent default events during swipe */
  preventDefault?: boolean;
  /** Callback when swipe left is detected */
  onSwipeLeft?: (e: MouseEvent | TouchEvent, state: SwipeState) => void;
  /** Callback when swipe right is detected */
  onSwipeRight?: (e: MouseEvent | TouchEvent, state: SwipeState) => void;
  /** Callback when swipe up is detected */
  onSwipeUp?: (e: MouseEvent | TouchEvent, state: SwipeState) => void;
  /** Callback when swipe down is detected */
  onSwipeDown?: (e: MouseEvent | TouchEvent, state: SwipeState) => void;
  /** Callback when swipe starts */
  onSwipeStart?: (e: MouseEvent | TouchEvent, state: SwipeState) => void;
  /** Callback when swipe moves (for each touchmove/mousemove event) */
  onSwipeMove?: (e: MouseEvent | TouchEvent, state: SwipeState) => void;
  /** Callback when swipe ends */
  onSwipeEnd?: (e: MouseEvent | TouchEvent, state: SwipeState) => void;
  /** Whether to disable mouse support (touch only) */
  disableMouse?: boolean;
}

/**
 * Hook to detect swipe gestures on an element
 * 
 * @param options Configuration options
 * @returns Object containing swipe state and event handlers
 * 
 * @example
 * ```tsx
 * const { state, handlers } = useSwipe({
 *   onSwipeLeft: () => console.log('Swiped left!'),
 *   onSwipeRight: () => console.log('Swiped right!'),
 *   threshold: 50,
 * });
 * 
 * return (
 *   <div {...handlers} style={{ touchAction: 'none' }}>
 *     Swipe me left or right
 *     {state.swiping && <div>Swiping: {state.direction}</div>}
 *   </div>
 * );
 * ```
 */
export function useSwipe({
  threshold = 50,
  preventDefault = true,
  onSwipeLeft,
  onSwipeRight,
  onSwipeUp,
  onSwipeDown,
  onSwipeStart,
  onSwipeMove,
  onSwipeEnd,
  disableMouse = false,
}: UseSwipeOptions = {}): { state: SwipeState; handlers: SwipeHandlers } {
  // Track swipe state
  const [state, setState] = useState<SwipeState>({
    swiping: false,
    direction: null,
    deltaX: 0,
    deltaY: 0,
    absX: 0,
    absY: 0,
  });

  // Store initial touch position
  const startXRef = useRef<number | null>(null);
  const startYRef = useRef<number | null>(null);
  const isSwiping = useRef(false);

  // Track whether this is a mouse or touch event
  const isMouseEvent = useRef(false);

  // Helper to get event coordinates consistently for both mouse and touch
  const getEventCoordinates = useCallback((e: MouseEvent | TouchEvent) => {
    if ('touches' in e) {
      if (e.touches.length > 0) {
        return { x: e.touches[0].clientX, y: e.touches[0].clientY };
      }
      return null;
    }
    return { x: e.clientX, y: e.clientY };
  }, []);

  // Handle the start of a swipe
  const handleSwipeStart = useCallback(
    (e: MouseEvent | TouchEvent) => {
      // Only store values for primary button clicks or touch events
      if ('button' in e && e.button !== 0) return;

      isMouseEvent.current = 'clientX' in e;

      // Get coordinates from either mouse or touch event
      const coords = getEventCoordinates(e);
      if (!coords) return;

      // Store starting position
      startXRef.current = coords.x;
      startYRef.current = coords.y;
      isSwiping.current = true;

      // Reset state at the start of a new swipe
      setState({
        swiping: true,
        direction: null,
        deltaX: 0,
        deltaY: 0,
        absX: 0,
        absY: 0,
      });

      // Notify of swipe start
      onSwipeStart?.(e, state);
    },
    [getEventCoordinates, onSwipeStart, state]
  );

  // Handle swipe movement
  const handleSwipeMove = useCallback(
    (e: MouseEvent | TouchEvent) => {
      // Skip if not currently tracking a swipe
      if (!isSwiping.current || startXRef.current === null || startYRef.current === null) {
        return;
      }

      // Prevent default behaviors like scrolling
      if (preventDefault) {
        e.preventDefault();
      }

      // Get current position
      const coords = getEventCoordinates(e);
      if (!coords) return;

      // Calculate deltas from start position
      const deltaX = coords.x - startXRef.current;
      const deltaY = coords.y - startYRef.current;
      const absX = Math.abs(deltaX);
      const absY = Math.abs(deltaY);

      // Determine swipe direction
      let direction: SwipeDirection | null = null;
      if (absX > absY && absX > threshold) {
        direction = deltaX > 0 ? 'right' : 'left';
      } else if (absY > absX && absY > threshold) {
        direction = deltaY > 0 ? 'down' : 'up';
      }

      // Update state
      setState({
        swiping: true,
        direction,
        deltaX,
        deltaY,
        absX,
        absY,
      });

      // Notify of swipe movement
      onSwipeMove?.(e, {
        swiping: true,
        direction,
        deltaX,
        deltaY,
        absX,
        absY,
      });
    },
    [getEventCoordinates, preventDefault, threshold, onSwipeMove]
  );

  // Handle the end of a swipe
  const handleSwipeEnd = useCallback(
    (e: MouseEvent | TouchEvent) => {
      if (!isSwiping.current) return;

      // Get final state for callback
      const finalState = {
        ...state,
        swiping: false,
      };

      // Reset tracking
      isSwiping.current = false;
      isMouseEvent.current = false;

      // Calculate final direction and trigger appropriate callback
      if (finalState.direction) {
        switch (finalState.direction) {
          case 'left':
            onSwipeLeft?.(e, finalState);
            break;
          case 'right':
            onSwipeRight?.(e, finalState);
            break;
          case 'up':
            onSwipeUp?.(e, finalState);
            break;
          case 'down':
            onSwipeDown?.(e, finalState);
            break;
        }
      }

      // Notify of swipe end
      onSwipeEnd?.(e, finalState);

      // Reset state
      setState({
        swiping: false,
        direction: null,
        deltaX: 0,
        deltaY: 0,
        absX: 0,
        absY: 0,
      });
    },
    [state, onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown, onSwipeEnd]
  );

  // Create React event handlers
  const handlers: SwipeHandlers = {
    onTouchStart: (e) => handleSwipeStart(e.nativeEvent),
    onTouchMove: (e) => handleSwipeMove(e.nativeEvent),
    onTouchEnd: (e) => handleSwipeEnd(e.nativeEvent),
    
    // Mouse event handlers (can be disabled)
    onMouseDown: !disableMouse ? (e) => handleSwipeStart(e.nativeEvent) : () => {},
    onMouseMove: !disableMouse ? (e) => handleSwipeMove(e.nativeEvent) : () => {},
    onMouseUp: !disableMouse ? (e) => handleSwipeEnd(e.nativeEvent) : () => {},
    onMouseLeave: !disableMouse ? (e) => handleSwipeEnd(e.nativeEvent) : () => {},
  };

  return { state, handlers };
} 