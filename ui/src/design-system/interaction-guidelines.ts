/**
 * Interaction Guidelines
 * 
 * Comprehensive UI/UX guidelines for interactions in the KAI UI Design System.
 * Defines standards for user interactions to create consistent, intuitive experiences.
 */

import { transitions } from '../theme/animations';
import { colors } from '../theme/tokens';

/**
 * Interactive States
 * 
 * Standard definitions for interactive element states.
 */
export const interactiveStates = {
  /**
   * Button States
   */
  button: {
    default: {
      background: colors.kai[500],
      color: colors.white,
      border: 'none',
      boxShadow: 'none',
    },
    hover: {
      background: colors.kai[600],
      transform: 'translateY(-1px)',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
      transition: `all ${transitions.duration.fast} ${transitions.easing.easeOut}`,
    },
    active: {
      background: colors.kai[700],
      transform: 'translateY(0)',
      boxShadow: 'none',
      transition: `all ${transitions.duration.fast} ${transitions.easing.easeIn}`,
    },
    focus: {
      outline: `2px solid ${colors.kai[300]}`,
      outlineOffset: '2px',
    },
    disabled: {
      background: colors.border.light,
      color: colors.text.disabled,
      cursor: 'not-allowed',
      opacity: 0.7,
      transform: 'none',
      boxShadow: 'none',
    },
    loading: {
      opacity: 0.8,
      cursor: 'wait',
    },
  },

  /**
   * Input States
   */
  input: {
    default: {
      border: `1px solid ${colors.border.medium}`,
      background: colors.white,
      color: colors.text.primary,
    },
    hover: {
      border: `1px solid ${colors.kai[300]}`,
      transition: `all ${transitions.duration.fast} ${transitions.easing.easeOut}`,
    },
    focus: {
      border: `1px solid ${colors.kai[500]}`,
      boxShadow: `0 0 0 1px ${colors.kai[300]}`,
      outline: 'none',
    },
    error: {
      border: `1px solid ${colors.status.error}`,
      background: `rgba(244, 67, 54, 0.05)`,
    },
    success: {
      border: `1px solid ${colors.status.success}`,
      background: `rgba(0, 200, 83, 0.05)`,
    },
    disabled: {
      background: colors.background.lightHover,
      color: colors.text.disabled,
      cursor: 'not-allowed',
      border: `1px solid ${colors.border.light}`,
    },
  },

  /**
   * Card States
   */
  card: {
    default: {
      background: colors.white,
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    },
    hover: {
      boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
      transform: 'translateY(-2px)',
      transition: `all ${transitions.duration.normal} ${transitions.easing.easeOut}`,
    },
    active: {
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
      transform: 'translateY(-1px)',
    },
    focus: {
      outline: `2px solid ${colors.kai[300]}`,
      outlineOffset: '2px',
    },
    selected: {
      background: `rgba(0, 165, 255, 0.05)`,
      border: `1px solid ${colors.kai[300]}`,
    },
  },

  /**
   * Link States
   */
  link: {
    default: {
      color: colors.kai[500],
      textDecoration: 'none',
    },
    hover: {
      color: colors.kai[700],
      textDecoration: 'underline',
      transition: `all ${transitions.duration.fast} ${transitions.easing.easeOut}`,
    },
    active: {
      color: colors.kai[800],
    },
    focus: {
      outline: `2px solid ${colors.kai[300]}`,
      outlineOffset: '2px',
    },
    visited: {
      color: colors.kai[600],
    },
    disabled: {
      color: colors.text.disabled,
      textDecoration: 'none',
      cursor: 'not-allowed',
    },
  },

  /**
   * Toggle States (Checkbox, Radio, Switch)
   */
  toggle: {
    default: {
      background: colors.white,
      border: `1px solid ${colors.border.medium}`,
    },
    hover: {
      borderColor: colors.kai[400],
      transition: `all ${transitions.duration.fast} ${transitions.easing.easeOut}`,
    },
    focus: {
      boxShadow: `0 0 0 2px ${colors.kai[200]}`,
    },
    checked: {
      background: colors.kai[500],
      borderColor: colors.kai[500],
      color: colors.white,
    },
    disabled: {
      background: colors.background.lightHover,
      borderColor: colors.border.light,
      opacity: 0.6,
      cursor: 'not-allowed',
    },
  },

  /**
   * Menu Item States
   */
  menuItem: {
    default: {
      background: 'transparent',
      color: colors.text.primary,
    },
    hover: {
      background: colors.background.lightHover,
      transition: `all ${transitions.duration.fast} ${transitions.easing.easeOut}`,
    },
    active: {
      background: colors.background.lightActive,
    },
    focus: {
      outline: 'none',
      background: colors.background.lightHover,
    },
    selected: {
      background: `rgba(0, 165, 255, 0.1)`,
      color: colors.kai[700],
      fontWeight: 500,
    },
    disabled: {
      color: colors.text.disabled,
      cursor: 'not-allowed',
    },
  },
};

/**
 * Focus Management
 * 
 * Guidelines for keyboard focus management.
 */
export const focusManagement = {
  /**
   * Key principles for focus management
   */
  principles: [
    'Ensure all interactive elements are keyboard accessible',
    'Maintain a logical tab order that follows visual layout',
    'Provide visible focus indicators for all interactive elements',
    'Trap focus within modal dialogs and other overlay components',
    'Return focus to trigger elements when overlays are closed',
  ],

  /**
   * Focus order priorities
   */
  focusOrder: {
    primary: 'Main actions and navigation elements',
    secondary: 'Form inputs and interactive content',
    tertiary: 'Less common actions and supplementary controls',
  },

  /**
   * Focus indicator styles
   */
  indicators: {
    standard: {
      outline: `2px solid ${colors.kai[500]}`,
      outlineOffset: '2px',
    },
    highContrast: {
      outline: `3px solid ${colors.kai[700]}`,
      outlineOffset: '3px',
    },
  },
};

/**
 * Timing and Feedback
 * 
 * Guidelines for timing and user feedback.
 */
export const timingAndFeedback = {
  /**
   * Response time thresholds
   */
  responseTime: {
    immediate: {
      threshold: '100ms',
      description: 'For instant feedback (button clicks, toggles)',
      examples: ['Button state changes', 'Toggle switches', 'Keyboard input'],
    },
    quick: {
      threshold: '300ms',
      description: 'For micro-interactions',
      examples: ['Tooltips', 'Dropdown menus', 'Simple animations'],
    },
    noticeable: {
      threshold: '1000ms',
      description: 'User notices delay but feels system is responsive',
      examples: ['Loading small data sets', 'Simple calculations', 'Navigation transitions'],
    },
    extended: {
      threshold: '> 1000ms',
      description: 'Requires progress indication',
      examples: ['Data processing', 'File uploads', 'Complex calculations'],
    },
  },

  /**
   * User progress feedback
   */
  progressFeedback: {
    minimal: {
      threshold: '< 1000ms',
      type: 'Subtle indicator',
      examples: ['Button loading state', 'Micro-loaders'],
    },
    standard: {
      threshold: '1-3 seconds',
      type: 'Spinner or progress bar',
      examples: ['Page loading', 'Form submission'],
    },
    detailed: {
      threshold: '> 3 seconds',
      type: 'Progress bar with percentage/steps',
      examples: ['File uploads', 'Multi-step processes'],
    },
    extended: {
      threshold: '> 10 seconds',
      type: 'Progress bar with time estimate and cancellation option',
      examples: ['Large file uploads', 'Complex data processing'],
    },
  },
};

/**
 * Motion Guidelines
 * 
 * Guidelines for animation and motion.
 */
export const motionGuidelines = {
  /**
   * When to use animations
   */
  purposes: {
    orientation: 'Help users understand spatial relationships and navigation',
    feedback: 'Confirm actions and provide system status',
    attention: 'Direct user attention to important changes',
    personality: 'Express brand personality in subtle, meaningful ways',
  },

  /**
   * Motion duration guidelines
   */
  duration: {
    entrance: transitions.duration.normal,
    exit: transitions.duration.fast,
    emphasis: transitions.duration.slow,
    microInteraction: transitions.duration.fast,
  },

  /**
   * Motion principles
   */
  principles: [
    'Animations should have purpose and meaning',
    'Motion should feel natural and expected',
    'Shorter is generally better for common interactions',
    'Be consistent with timing and easing across similar elements',
    'Always provide reduced motion alternatives',
  ],

  /**
   * Easing functions for different purposes
   */
  easing: {
    standard: {
      value: transitions.easing.standard,
      usage: 'Most UI transitions',
    },
    decelerate: {
      value: transitions.easing.decelerate,
      usage: 'Elements entering the screen',
    },
    accelerate: {
      value: transitions.easing.accelerate,
      usage: 'Elements exiting the screen',
    },
    sharp: {
      value: transitions.easing.sharp,
      usage: 'Quick UI feedback with abrupt changes',
    },
  },
};

/**
 * Touch and Gesture Guidelines
 * 
 * Guidelines for touch interactions and gestures.
 */
export const touchGuidelines = {
  /**
   * Touch target sizes
   */
  touchTargets: {
    minimum: {
      size: '44px × 44px',
      description: 'Absolute minimum for any interactive element',
    },
    small: {
      size: '48px × 48px',
      description: 'Small controls like checkboxes and radio buttons',
    },
    standard: {
      size: '56px × 56px',
      description: 'Standard buttons and most touch targets',
    },
    large: {
      size: '64px × 64px',
      description: 'Primary actions and important controls',
    },
  },

  /**
   * Touch target spacing
   */
  spacing: {
    minimum: '8px',
    recommended: '12px',
  },

  /**
   * Standard gestures and their uses
   */
  gestures: {
    tap: {
      description: 'Primary interaction for buttons and controls',
      feedback: 'Visual change in the element, often with slight animation',
    },
    doubleTap: {
      description: 'Used sparingly for secondary actions like zoom',
      feedback: 'Clear visual change in content or viewport',
    },
    longPress: {
      description: 'Access to contextual actions or secondary features',
      feedback: 'Visual and possibly haptic feedback, followed by menu appearance',
    },
    swipe: {
      description: 'Scrolling content or navigating between views',
      feedback: 'Content follows finger with appropriate momentum',
    },
    pinchSpread: {
      description: 'Zoom in/out of content',
      feedback: 'Content scales smoothly with the gesture',
    },
  },
};

/**
 * Form Interaction Guidelines
 * 
 * Guidelines for form interactions and behaviors.
 */
export const formGuidelines = {
  /**
   * Input behavior guidelines
   */
  inputBehavior: {
    autofocus: 'Use for the primary input in simple forms, avoid in complex forms',
    validation: 'Validate on blur for most fields, provide immediate feedback for critical errors',
    autoComplete: 'Enable where appropriate and specify correct autoComplete attributes',
    maskInput: 'Use for formatted inputs like phone numbers, credit cards, dates',
  },

  /**
   * Error handling
   */
  errorHandling: {
    timing: {
      onBlur: 'Validate when user leaves field (most cases)',
      onChange: 'Real-time validation for critical fields or password strength',
      onSubmit: 'Final check before form submission',
    },
    presentation: {
      inline: 'Show errors directly below the relevant input',
      summary: 'Provide error summary at top of form for multiple errors',
      persistent: 'Keep errors visible until resolved',
    },
  },

  /**
   * Keyboard interaction
   */
  keyboardInteraction: {
    tabOrder: 'Logical flow from top to bottom, left to right',
    shortcuts: 'Provide keyboard shortcuts for common actions (Ctrl+S for save)',
    enterKey: 'Submit form when Enter is pressed in a field (except in textareas)',
    escapeKey: 'Clear focused field or close modals/overlays',
  },
};

/**
 * Affordance Guidelines
 * 
 * Guidelines for making interaction affordances clear to users.
 */
export const affordanceGuidelines = {
  /**
   * Visual cues for interactive elements
   */
  visualCues: {
    buttons: 'Use consistent styling with visible boundaries or fill',
    links: 'Underline or distinctive color, consistent across the application',
    inputs: 'Clear boundaries with labels, use placeholders as supplementary guidance',
    selectables: 'Visually distinct from static content, with clear hover states',
  },

  /**
   * Discoverability patterns
   */
  discoverability: {
    primaryActions: 'Highly visible, using size, color, and position',
    secondaryActions: 'Visible but less prominent than primary actions',
    tertiaryActions: 'May be partially hidden but with clear access patterns',
    gestureHints: 'Provide visual hints for available gestures (swipe indicators)',
  },
}; 