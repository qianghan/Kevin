/**
 * Animation System
 * 
 * Defines animations, transitions, and motion patterns for the KAI UI Design System.
 * Ensures consistency in motion across the application.
 */

/**
 * Transition Presets
 * 
 * Predefined transition settings for common use cases.
 */
export const transitions = {
  easing: {
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
    standard: 'cubic-bezier(0.2, 0, 0, 1)',
    decelerate: 'cubic-bezier(0, 0, 0.2, 1)',
    accelerate: 'cubic-bezier(0.4, 0, 1, 1)',
  },
  duration: {
    ultraFast: '50ms',
    faster: '100ms',
    fast: '150ms',
    normal: '200ms',
    slow: '300ms',
    slower: '400ms',
    ultraSlow: '500ms',
  },
  default: '200ms cubic-bezier(0.2, 0, 0, 1)',
  defaultEaseOut: '200ms cubic-bezier(0, 0, 0.2, 1)',
};

/**
 * Keyframes
 * 
 * Standard animation sequences for reuse throughout the application.
 */
export const keyframes = {
  fadeIn: {
    from: { opacity: 0 },
    to: { opacity: 1 },
  },
  fadeOut: {
    from: { opacity: 1 },
    to: { opacity: 0 },
  },
  slideInUp: {
    from: { transform: 'translateY(10px)', opacity: 0 },
    to: { transform: 'translateY(0)', opacity: 1 },
  },
  slideInDown: {
    from: { transform: 'translateY(-10px)', opacity: 0 },
    to: { transform: 'translateY(0)', opacity: 1 },
  },
  slideInLeft: {
    from: { transform: 'translateX(-10px)', opacity: 0 },
    to: { transform: 'translateX(0)', opacity: 1 },
  },
  slideInRight: {
    from: { transform: 'translateX(10px)', opacity: 0 },
    to: { transform: 'translateX(0)', opacity: 1 },
  },
  scaleIn: {
    from: { transform: 'scale(0.95)', opacity: 0 },
    to: { transform: 'scale(1)', opacity: 1 },
  },
  scaleOut: {
    from: { transform: 'scale(1)', opacity: 1 },
    to: { transform: 'scale(0.95)', opacity: 0 },
  },
  pulse: {
    '0%': { transform: 'scale(1)' },
    '50%': { transform: 'scale(1.05)' },
    '100%': { transform: 'scale(1)' },
  },
  spin: {
    from: { transform: 'rotate(0deg)' },
    to: { transform: 'rotate(360deg)' },
  },
  shimmer: {
    '0%': { backgroundPosition: '-468px 0' },
    '100%': { backgroundPosition: '468px 0' },
  },
};

/**
 * Animation Presets
 * 
 * Predefined animations that combine keyframes, duration, and easing.
 */
export const animationPresets = {
  fadeIn: {
    animation: `${keyframes.fadeIn} ${transitions.duration.normal} ${transitions.easing.easeOut} forwards`,
  },
  fadeOut: {
    animation: `${keyframes.fadeOut} ${transitions.duration.normal} ${transitions.easing.easeIn} forwards`,
  },
  slideInUp: {
    animation: `${keyframes.slideInUp} ${transitions.duration.normal} ${transitions.easing.easeOut} forwards`,
  },
  slideInDown: {
    animation: `${keyframes.slideInDown} ${transitions.duration.normal} ${transitions.easing.easeOut} forwards`,
  },
  slideInLeft: {
    animation: `${keyframes.slideInLeft} ${transitions.duration.normal} ${transitions.easing.easeOut} forwards`,
  },
  slideInRight: {
    animation: `${keyframes.slideInRight} ${transitions.duration.normal} ${transitions.easing.easeOut} forwards`,
  },
  scaleIn: {
    animation: `${keyframes.scaleIn} ${transitions.duration.normal} ${transitions.easing.easeOut} forwards`,
  },
  scaleOut: {
    animation: `${keyframes.scaleOut} ${transitions.duration.normal} ${transitions.easing.easeIn} forwards`,
  },
  pulse: {
    animation: `${keyframes.pulse} ${transitions.duration.slow} ${transitions.easing.easeInOut} infinite`,
  },
  spin: {
    animation: `${keyframes.spin} 1s ${transitions.easing.easeInOut} infinite`,
  },
  shimmer: {
    animation: `${keyframes.shimmer} 1.5s ${transitions.easing.easeInOut} infinite linear`,
    backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.2) 20%, rgba(255,255,255,0.5) 60%, rgba(255,255,255,0) 100%)',
    backgroundSize: '1000px 100%',
    backgroundRepeat: 'no-repeat',
  },
};

/**
 * Responsive Animations
 * 
 * Controls motion based on user preferences and device capabilities.
 */
export const responsiveAnimations = {
  enabledForAll: true,
  reduceMotion: {
    fadeIn: {
      opacity: 1,
      transition: 'opacity 0ms',
    },
    fadeOut: {
      opacity: 0,
      transition: 'opacity 0ms',
    },
    transform: 'none',
    animation: 'none',
  },
};

/**
 * Motion Variants
 * 
 * Common animation variants for use with Framer Motion.
 */
export const motionVariants = {
  fadeIn: {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { duration: 0.2 } },
    exit: { opacity: 0, transition: { duration: 0.15 } },
  },
  slideUp: {
    hidden: { y: 10, opacity: 0 },
    visible: { y: 0, opacity: 1, transition: { duration: 0.3 } },
    exit: { y: 10, opacity: 0, transition: { duration: 0.2 } },
  },
  scale: {
    hidden: { scale: 0.95, opacity: 0 },
    visible: { scale: 1, opacity: 1, transition: { duration: 0.2 } },
    exit: { scale: 0.95, opacity: 0, transition: { duration: 0.15 } },
  },
  staggerChildren: {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
      },
    },
  },
  staggerItem: {
    hidden: { opacity: 0, y: 5 },
    visible: { opacity: 1, y: 0 },
  },
};

/**
 * Motion preferences
 * 
 * Motion settings that respect user preferences for reduced motion.
 */
export const motionPreferences = {
  /**
   * Check if the user prefers reduced motion
   * @returns boolean indicating if reduced motion is preferred
   */
  prefersReducedMotion(): boolean {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  },
  
  /**
   * Get appropriate animation duration based on motion preferences
   * @param normalDuration The normal duration to use when reduced motion is not preferred
   * @returns The appropriate duration value
   */
  getAnimationDuration(normalDuration: string = transitions.duration.normal): string {
    return this.prefersReducedMotion() ? transitions.duration.fast : normalDuration;
  },
  
  /**
   * Get appropriate transition settings based on motion preferences
   * @param property CSS property to transition
   * @param normalDuration The normal duration to use when reduced motion is not preferred
   * @param easing The easing function to use
   * @returns The appropriate transition value
   */
  getTransition(
    property: string = 'all',
    normalDuration: string = transitions.duration.normal,
    easing: string = transitions.easing.easeInOut
  ): string {
    const duration = this.getAnimationDuration(normalDuration);
    return `${property} ${duration} ${easing}`;
  },
}; 