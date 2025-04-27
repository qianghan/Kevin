# KAI Theme Documentation

The KAI theme extends Chakra UI's base theme with custom brand styling and components. This document outlines the theme structure, customization options, and usage patterns.

## Color System

The KAI color system is based on the brand's mint/teal green (`#4FDBA9`) and dark navy (`#0A1723`).

### Primary Colors

| Token | Hex | Usage |
| ----- | --- | ----- |
| kai.400 | #4FDBA9 | Primary brand color |
| kai.500 | #33C495 | Primary brand hover |
| kai.600 | #29A07A | Primary brand active |
| background.dark | #0A1723 | Dark mode background |
| background.light | #FFFFFF | Light mode background |

### Semantic Colors

The theme includes a full range of semantic colors for success, error, warning, and info states, each with multiple shades.

```typescript
// Example usage
<Box bg="kai.400">KAI Brand</Box>
<Box bg="success.500">Success</Box>
<Box bg="error.500">Error</Box>
```

## Typography

KAI uses Inter as the primary font family:

```typescript
const fonts = {
  heading: 'Inter, system-ui, sans-serif',
  body: 'Inter, system-ui, sans-serif',
  mono: 'JetBrains Mono, monospace',
}
```

## Brand Extensions

The theme includes custom extensions for brand-specific styling:

```typescript
brandExtensions: {
  brandRing: {
    default: '0 0 0 2px var(--chakra-colors-kai-400)',
    dark: '0 0 0 2px var(--chakra-colors-kai-300)',
  },
  elevation: {
    low: {
      light: '0 1px 3px rgba(0, 0, 0, 0.1)',
      dark: '0 1px 3px rgba(0, 0, 0, 0.3)',
    },
    // ... additional elevation levels
  },
}
```

## Component Customization

All components follow the KAI design language. Here's how to customize components:

```typescript
// Button component with KAI styling
const Button = {
  baseStyle: {
    fontWeight: 'semibold',
    borderRadius: 'md',
  },
  variants: {
    primary: (props) => ({
      bg: props.colorMode === 'dark' ? 'kai.400' : 'kai.500',
      color: props.colorMode === 'dark' ? 'background.dark' : 'white',
      _hover: {
        bg: props.colorMode === 'dark' ? 'kai.300' : 'kai.600',
      },
    }),
    secondary: (props) => ({
      bg: 'transparent',
      border: '1px solid',
      borderColor: props.colorMode === 'dark' ? 'kai.400' : 'kai.500',
      color: props.colorMode === 'dark' ? 'kai.400' : 'kai.500',
    }),
  },
  defaultProps: {
    variant: 'primary',
  },
}
```

## Color Mode

The theme supports light, dark, and system color modes:

```typescript
// Access and control color mode
import { useKAIColorMode } from '@/theme/useKAIColorMode';

function MyComponent() {
  const { colorMode, toggleColorMode, setColorMode, prefersSystem } = useKAIColorMode();
  
  return (
    <div>
      <p>Current mode: {colorMode}</p>
      <button onClick={toggleColorMode}>Toggle</button>
      <button onClick={() => setColorMode('system')}>Use system</button>
    </div>
  );
}
```

## Usage with Chakra Hooks

The theme can be accessed with Chakra UI's hooks:

```typescript
import { useTheme, useColorModeValue } from '@chakra-ui/react';

function ThemedComponent() {
  const theme = useTheme();
  const bgColor = useColorModeValue('background.light', 'background.dark');
  const textColor = useColorModeValue('gray.800', 'white');
  
  return (
    <div style={{ 
      backgroundColor: theme.colors[bgColor.split('.')[0]][bgColor.split('.')[1]],
      color: theme.colors[textColor.split('.')[0]][textColor.split('.')[1]],
      boxShadow: theme.brandExtensions.elevation.medium[theme.colorMode],
    }}>
      Themed content
    </div>
  );
}
```

## Extending the Theme

To extend the theme with additional components or styles:

```typescript
import { extendTheme } from '@chakra-ui/react';
import { kaiTheme } from '@/theme';

const extendedTheme = extendTheme({
  components: {
    // Add or override component styles
    Card: {
      baseStyle: {
        // ...
      },
    },
  },
}, kaiTheme);
``` 