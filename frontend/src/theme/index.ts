import { extendTheme, type ThemeConfig } from '@chakra-ui/react'
import { colors } from './colors'
import { KAITheme } from './theme.types'

// Base configuration for the theme
const config: ThemeConfig = {
  initialColorMode: 'system',
  useSystemColorMode: true,
}

// Font configuration
const fonts = {
  heading: 'Inter, system-ui, sans-serif',
  body: 'Inter, system-ui, sans-serif',
  mono: 'JetBrains Mono, monospace',
}

// Brand-specific extensions
const brandExtensions = {
  brandRing: {
    default: '0 0 0 2px var(--chakra-colors-kai-400)',
    dark: '0 0 0 2px var(--chakra-colors-kai-300)',
  },
  elevation: {
    low: {
      light: '0 1px 3px rgba(0, 0, 0, 0.1)',
      dark: '0 1px 3px rgba(0, 0, 0, 0.3)',
    },
    medium: {
      light: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      dark: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
    },
    high: {
      light: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
      dark: '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
    },
  },
}

// Component-specific styles
const components = {
  Button: {
    baseStyle: {
      fontWeight: 'semibold',
      borderRadius: 'md',
    },
    variants: {
      primary: (props: { colorMode: string }) => ({
        bg: props.colorMode === 'dark' ? 'kai.400' : 'kai.500',
        color: props.colorMode === 'dark' ? 'background.dark' : 'white',
        _hover: {
          bg: props.colorMode === 'dark' ? 'kai.300' : 'kai.600',
          _disabled: {
            bg: props.colorMode === 'dark' ? 'kai.400' : 'kai.500',
          },
        },
        _active: {
          bg: props.colorMode === 'dark' ? 'kai.200' : 'kai.700',
        },
      }),
      secondary: (props: { colorMode: string }) => ({
        bg: 'transparent',
        border: '1px solid',
        borderColor: props.colorMode === 'dark' ? 'kai.400' : 'kai.500',
        color: props.colorMode === 'dark' ? 'kai.400' : 'kai.500',
        _hover: {
          bg: props.colorMode === 'dark' ? 'whiteAlpha.100' : 'blackAlpha.50',
        },
        _active: {
          bg: props.colorMode === 'dark' ? 'whiteAlpha.200' : 'blackAlpha.100',
        },
      }),
    },
    defaultProps: {
      variant: 'primary',
    },
  },
  // Additional components can be customized here
}

// Create the theme by extending Chakra's base theme
export const kaiTheme = extendTheme({
  config,
  colors,
  fonts,
  components,
  brandExtensions,
}) as KAITheme

export default kaiTheme 