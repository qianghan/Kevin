/**
 * Theme Provider
 * 
 * Utility for creating and managing theme configurations.
 * Provides functionality to create, extend, and customize themes.
 */

import * as tokens from './tokens';
import * as animations from './animations';
import { Theme, ThemeTokens, ThemeAnimations } from './theme-types.js';

/**
 * Creates a new theme with the specified configuration
 * 
 * @param config Theme configuration options
 * @returns A complete theme object
 */
export const createTheme = (config: {
  name: string;
  tokens: ThemeTokens | Partial<ThemeTokens>;
  animations: ThemeAnimations | Partial<ThemeAnimations>;
}): Theme => {
  return {
    name: config.name,
    tokens: {
      ...tokens,
      ...config.tokens
    },
    animations: {
      ...animations,
      ...config.animations
    }
  };
};

/**
 * Extends an existing theme with custom tokens and animations
 * 
 * @param baseTheme The base theme to extend
 * @param overrides The custom tokens and animations to apply
 * @returns A new theme with the applied overrides
 */
export const extendTheme = (
  baseTheme: Theme,
  overrides: {
    name?: string;
    tokens?: Partial<ThemeTokens>;
    animations?: Partial<ThemeAnimations>;
  }
): Theme => {
  return {
    name: overrides.name || `${baseTheme.name}-extended`,
    tokens: {
      ...baseTheme.tokens,
      ...(overrides.tokens || {})
    },
    animations: {
      ...baseTheme.animations,
      ...(overrides.animations || {})
    }
  };
};

/**
 * Creates a dark mode version of a theme
 * 
 * @param lightTheme The light theme to convert to dark mode
 * @returns A dark mode version of the theme
 */
export const createDarkTheme = (lightTheme: Theme): Theme => {
  // This is a simplified implementation
  // In a real application, you would transform color tokens to dark mode equivalents
  return {
    name: `${lightTheme.name}-dark`,
    tokens: {
      ...lightTheme.tokens,
      colors: {
        ...lightTheme.tokens.colors,
        // Invert key colors for dark mode
        background: {
          ...lightTheme.tokens.colors.background,
          light: lightTheme.tokens.colors.background.dark,
          dark: lightTheme.tokens.colors.background.light
        },
        // Additional dark mode transformations would be added here
      }
    },
    animations: lightTheme.animations
  };
}; 