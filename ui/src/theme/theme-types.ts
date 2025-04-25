/**
 * Theme Types
 * 
 * Type definitions for the theme system.
 * Centralizes all theme-related types to avoid circular dependencies.
 */

import * as tokens from './tokens';
import * as animations from './animations';

/**
 * Type definitions for theme objects and variants
 */
export type ThemeTokens = typeof tokens;
export type ThemeAnimations = typeof animations;

/**
 * Theme interface representing a complete theme configuration
 */
export interface Theme {
  name: string;
  tokens: ThemeTokens;
  animations: ThemeAnimations;
}

/**
 * Theme mode types (light or dark)
 */
export type ThemeMode = 'light' | 'dark';

/**
 * Theme variant names
 */
export type ThemeVariant = 'default' | 'high-contrast' | 'custom';

/**
 * Theme configuration options
 */
export interface ThemeConfig {
  mode: ThemeMode;
  variant: ThemeVariant;
  customTokens?: Partial<ThemeTokens>;
  customAnimations?: Partial<ThemeAnimations>;
} 