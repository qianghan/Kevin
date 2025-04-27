import { ThemingProps, ChakraTheme } from '@chakra-ui/react';

// Brand-specific extensions to the Chakra theme
interface BrandExtensions {
  brandRing: {
    default: string;
    dark: string;
  };
  elevation: {
    low: {
      light: string;
      dark: string;
    };
    medium: {
      light: string;
      dark: string;
    };
    high: {
      light: string;
      dark: string;
    };
  };
}

// Main theme interface that extends Chakra's Theme
export interface KAITheme extends ChakraTheme {
  brandExtensions: BrandExtensions;
}

// Theme component variant options
export type ComponentVariant = 'primary' | 'secondary' | 'tertiary' | 'ghost' | 'link';

// Color mode types
export type ColorMode = 'light' | 'dark' | 'system';

// Theme override for components
export interface ThemeComponentOverride {
  baseStyle?: Record<string, any>;
  sizes?: Record<string, Record<string, any>>;
  variants?: Record<string, Record<string, any>>;
  defaultProps?: {
    variant?: string;
    size?: string;
  };
} 