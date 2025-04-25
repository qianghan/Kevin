/**
 * Animation Hooks
 * 
 * Hooks for accessing animation presets and settings.
 * Follows single responsibility principle by focusing only on animation usage.
 */

import { useContext } from 'react';
import { ThemeContext } from '@chakra-ui/react';
import * as animations from './animations';

/**
 * Access animation presets for consistent motion patterns
 * 
 * @returns Animation settings from theme or fallback defaults
 * 
 * @example
 * ```tsx
 * const { transitions, keyframes, animationPresets } = useAnimationPresets();
 * 
 * return (
 *   <div style={{ transition: `all ${transitions.duration.normal} ${transitions.easing.easeOut}` }}>
 *     Animated content
 *   </div>
 * );
 * ```
 */
export function useAnimationPresets() {
  // Attempt to get animations from Chakra theme
  const theme = useContext(ThemeContext);
  
  // Return theme-based animations if available, otherwise return defaults
  if (theme?.animations) {
    return theme.animations;
  }
  
  return animations;
}

/**
 * Get animation variations based on user preferences
 * 
 * @returns Object with animation settings and motion preferences
 * 
 * @example
 * ```tsx
 * const { shouldReduceMotion, getTransition } = useMotionPreferences();
 * 
 * return (
 *   <div style={{ 
 *     transition: getTransition('transform'),
 *     transform: isActive ? 'scale(1.05)' : 'scale(1)' 
 *   }}>
 *     Motion-respecting content
 *   </div>
 * );
 * ```
 */
export function useMotionPreferences() {
  const { motionPreferences } = useAnimationPresets();
  
  const shouldReduceMotion = motionPreferences?.prefersReducedMotion?.() || false;
  
  const getTransition = (
    property = 'all',
    duration = 'normal',
    easing = 'easeInOut'
  ) => {
    // If function is available in theme, use it
    if (motionPreferences?.getTransition) {
      return motionPreferences.getTransition(property, 
        typeof duration === 'string' ? animations.transitions.duration[duration] : duration, 
        typeof easing === 'string' ? animations.transitions.easing[easing] : easing
      );
    }
    
    // Fallback to simple transition with reduced timing if needed
    const durationValue = typeof duration === 'string' 
      ? animations.transitions.duration[duration] 
      : duration;
      
    const easingValue = typeof easing === 'string'
      ? animations.transitions.easing[easing]
      : easing;
    
    const actualDuration = shouldReduceMotion 
      ? animations.transitions.duration.fast 
      : durationValue;
    
    return `${property} ${actualDuration} ${easingValue}`;
  };
  
  return {
    shouldReduceMotion,
    getTransition,
    getAnimationDuration: motionPreferences?.getAnimationDuration || 
      ((duration = 'normal') => shouldReduceMotion 
        ? animations.transitions.duration.fast 
        : (typeof duration === 'string' ? animations.transitions.duration[duration] : duration)
      ),
  };
} 