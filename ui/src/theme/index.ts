/**
 * Theme System
 * 
 * Central export point for all theme-related tokens, utilities and functions.
 * Combines all theme elements into a cohesive system following the Open/Closed Principle
 * to allow for extensions without modifying the core theme definitions.
 */

import * as tokens from './tokens';
import * as animations from './animations';
import { createTheme } from './theme-provider.js';

// Re-export types
export type { 
  Theme,
  ThemeTokens, 
  ThemeAnimations, 
  ThemeMode, 
  ThemeVariant, 
  ThemeConfig 
} from './theme-types';

export {
  tokens,
  animations,
  createTheme,
};

/**
 * Default theme using standard KAI UI design tokens
 */
export const defaultTheme = createTheme({
  name: 'default',
  tokens: tokens,
  animations: animations,
}); 