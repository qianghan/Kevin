/**
 * useLongPress Hook
 * 
 * A React hook for detecting long press gestures on elements.
 * Follows single responsibility principle by focusing only on long press detection.
 */

import { useCallback, useRef, useState } from 'react';

interface UseLongPressOptions {
  /** Time in milliseconds before long press is triggered */
  duration?: number;
  /** Callback fired when long press is detected */
  onLongPress: () => void;
  /** Callback fired when press starts */
  onStart?: () => void;
  /** Callback fired when press ends without triggering long press */
  onCancel?: () => void;
  /** Whether the long press should be disabled */
  isDisabled?: boolean;
}

interface UseLongPressResult {
  /** Whether element is currently being pressed */
  isPressed: boolean;
  /** Event handlers to attach to the element */
  handlerProps: {
    onMouseDown: (e: React.MouseEvent) => void;
    onMouseUp: (e: React.MouseEvent) => void;
    onMouseLeave: (e: React.MouseEvent) => void;
    onTouchStart: (e: React.TouchEvent) => void;
    onTouchEnd: (e: React.TouchEvent) => void;
  };
}

/**
 * Hook to detect long press gestures on an element
 * 
 * @param options Configuration options
 * @returns Object containing press state and event handlers
 * 
 * @example
 * ```tsx
 * const { isPressed, handlerProps } = useLongPress({
 *   onLongPress: () => console.log('Long press detected!'),
 *   duration: 500,
 * });
 * 
 * return (
 *   <button 
 *     {...handlerProps}
 *     style={{ background: isPressed ? 'darkblue' : 'blue' }}
 *   >
 *     Press and hold me
 *   </button>
 * );
 * ```
 */
export function useLongPress({
  duration = 500,
  onLongPress,
  onStart,
  onCancel,
  isDisabled = false,
}: UseLongPressOptions): UseLongPressResult {
  const [isPressed, setIsPressed] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isLongPressTriggeredRef = useRef(false);
  
  // Clear any existing timer and reset state
  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    isLongPressTriggeredRef.current = false;
  }, []);
  
  // Handle the start of a press
  const onPressStart = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    // Prevent default actions, especially important for touch events
    if (e.target instanceof Element) {
      // Only prevent default for non-input elements to maintain input functionality
      const tagName = e.target.tagName.toLowerCase();
      if (tagName !== 'input' && tagName !== 'textarea' && tagName !== 'select') {
        e.preventDefault();
      }
    }
    
    if (isDisabled) return;
    
    clearTimer();
    setIsPressed(true);
    onStart?.();
    
    timerRef.current = setTimeout(() => {
      isLongPressTriggeredRef.current = true;
      onLongPress();
    }, duration);
  }, [onLongPress, onStart, duration, isDisabled, clearTimer]);
  
  // Handle the end of a press
  const onPressEnd = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    if (e.target instanceof Element) {
      const tagName = e.target.tagName.toLowerCase();
      if (tagName !== 'input' && tagName !== 'textarea' && tagName !== 'select') {
        e.preventDefault();
      }
    }
    
    if (isDisabled) return;
    
    setIsPressed(false);
    
    if (!isLongPressTriggeredRef.current) {
      onCancel?.();
    }
    
    clearTimer();
  }, [onCancel, isDisabled, clearTimer]);
  
  // Compile all event handlers into a single props object
  const handlerProps = {
    onMouseDown: onPressStart,
    onMouseUp: onPressEnd,
    onMouseLeave: onPressEnd,
    onTouchStart: onPressStart,
    onTouchEnd: onPressEnd,
  };
  
  return { isPressed, handlerProps };
} 