/**
 * Design Tokens
 * 
 * Core design tokens for the KAI UI Design System.
 * Includes colors, spacing, typography, and other base values.
 */

/**
 * Color Tokens
 */
export const colors = {
  kai: {
    50: '#e5f6ff',
    100: '#ccedff',
    200: '#99dbff',
    300: '#66c9ff',
    400: '#33b7ff',
    500: '#00a5ff',
    600: '#0084cc',
    700: '#006399',
    800: '#004266',
    900: '#002133',
  },
  background: {
    dark: '#1A1A1A',
    darkHover: '#2A2A2A',
    darkActive: '#3A3A3A',
    light: '#FFFFFF',
    lightHover: '#F5F5F5',
    lightActive: '#EBEBEB',
  },
  text: {
    primary: '#202020',
    secondary: '#585858',
    tertiary: '#888888',
    light: '#FFFFFF',
    disabled: '#BBBBBB',
  },
  status: {
    success: '#00C853',
    warning: '#FFB300',
    error: '#F44336',
    info: '#0288D1',
  },
  border: {
    light: '#E0E0E0',
    medium: '#BBBBBB',
    dark: '#757575',
  },
  black: '#000000',
  white: '#FFFFFF',
};

/**
 * Spacing Tokens
 */
export const spacing = {
  xxs: '0.25rem', // 4px
  xs: '0.5rem',   // 8px
  sm: '0.75rem',  // 12px
  md: '1rem',     // 16px
  lg: '1.5rem',   // 24px
  xl: '2rem',     // 32px
  xxl: '3rem',    // 48px
  xxxl: '4rem',   // 64px
};

/**
 * Typography Tokens
 */
export const typography = {
  fontFamily: {
    heading: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    body: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: 'SFMono-Regular, Menlo, Monaco, Consolas, monospace',
  },
  fontSize: {
    xs: '0.75rem',   // 12px
    sm: '0.875rem',  // 14px
    md: '1rem',      // 16px
    lg: '1.125rem',  // 18px
    xl: '1.25rem',   // 20px
    xxl: '1.5rem',   // 24px
    xxxl: '2rem',    // 32px
    display: '3rem', // 48px
  },
  fontWeight: {
    light: 300,
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.2,
    normal: 1.5,
    loose: 1.8,
  },
};

/**
 * Borders Tokens
 */
export const borders = {
  radius: {
    none: '0',
    sm: '0.125rem', // 2px
    md: '0.25rem',  // 4px
    lg: '0.5rem',   // 8px
    xl: '1rem',     // 16px
    circle: '50%',
  },
  width: {
    thin: '1px',
    medium: '2px',
    thick: '4px',
  },
};

/**
 * Shadows Tokens
 */
export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  none: 'none',
};

/**
 * Z-index Tokens
 */
export const zIndices = {
  hide: -1,
  base: 0,
  dropdown: 1000,
  sticky: 1100,
  overlay: 1200,
  modal: 1300,
  popover: 1400,
  toast: 1500,
  tooltip: 1600,
}; 