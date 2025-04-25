/**
 * useHover Hook
 * 
 * A React hook for detecting mouse hover on elements.
 * Follows single responsibility principle by focusing only on hover state management.
 */

import { useState, useRef, useEffect, RefObject } from 'react';

interface UseHoverOptions {
  /** Delay in milliseconds before hover state is triggered (debounce) */
  delay?: number;
  /** Callback fired when hover state changes */
  onHoverChange?: (isHovering: boolean) => void;
}

interface UseHoverResult<T extends HTMLElement = HTMLElement> {
  /** Current hover state */
  isHovering: boolean;
  /** Ref to attach to the target element */
  hoverRef: RefObject<T>;
  /** Manually set the hover state */
  setIsHovering: (isHovering: boolean) => void;
}

/**
 * Hook to detect hover state on an element
 * 
 * @param options Configuration options
 * @returns Object containing hover state and ref to attach to target element
 * 
 * @example
 * ```tsx
 * const { isHovering, hoverRef } = useHover();
 * 
 * return (
 *   <div 
 *     ref={hoverRef} 
 *     style={{ background: isHovering ? 'blue' : 'gray' }}
 *   >
 *     Hover me
 *   </div>
 * );
 * ```
 */
export function useHover<T extends HTMLElement = HTMLElement>(
  options: UseHoverOptions = {}
): UseHoverResult<T> {
  const { delay = 0, onHoverChange } = options;
  
  const [isHovering, setIsHovering] = useState(false);
  const hoverRef = useRef<T>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const node = hoverRef.current;
    if (!node) return;

    const handleMouseEnter = () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      
      if (delay) {
        timeoutRef.current = setTimeout(() => {
          setIsHovering(true);
          onHoverChange?.(true);
        }, delay);
      } else {
        setIsHovering(true);
        onHoverChange?.(true);
      }
    };

    const handleMouseLeave = () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      
      if (delay) {
        timeoutRef.current = setTimeout(() => {
          setIsHovering(false);
          onHoverChange?.(false);
        }, delay);
      } else {
        setIsHovering(false);
        onHoverChange?.(false);
      }
    };

    node.addEventListener('mouseenter', handleMouseEnter);
    node.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      node.removeEventListener('mouseenter', handleMouseEnter);
      node.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [delay, onHoverChange]);

  return { isHovering, hoverRef, setIsHovering };
} 