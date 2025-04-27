# KAI Brand Identity Implementation

This document outlines the implementation of the KAI brand identity in the frontend codebase, including brand assets, typography, colors, and components.

## Brand Assets

### Logo

The KAI logo is implemented as a React component with SVG graphics. This approach ensures the logo scales properly at any size and maintains clarity across different devices and resolutions.

#### Logo Variants

The `Logo` component supports three variants:

1. **Full (default)**: Shows both the logo mark and text
2. **Mark**: Shows only the logo symbol/icon
3. **Text**: Shows only the text portion of the logo

#### Logo Sizes

The logo component supports multiple predefined sizes:

- `xs`: Extra small (20px height)
- `sm`: Small (24px height)
- `md`: Medium (32px height)
- `lg`: Large (48px height)
- `xl`: Extra large (64px height)

#### Usage Examples

```tsx
// Default logo (full, medium size)
<Logo />

// Logo mark only, large size
<Logo variant="mark" size="lg" />

// Text only, extra small
<Logo variant="text" size="xs" />

// Full logo with tagline
<Logo showTagline={true} />
```

### Logo Colors

The logo automatically adjusts its colors based on the color mode:

- **Light Mode**:
  - Logo mark: `#33C495` (kai.500)
  - Text: `#0A1723` (dark navy)

- **Dark Mode**:
  - Logo mark: `#4FDBA9` (kai.400)
  - Text: `white`

## Loading Screens

The `LoadingScreen` component provides a branded loading experience with animated elements.

### Features

- Responsive design that works in both full-screen and contained contexts
- Animated concentric circles with brand colors
- Pulsing logo animation
- Customizable loading message
- Animated loading dots

### Usage

```tsx
// Default loading screen
<LoadingScreen />

// Full-screen loading with custom message
<LoadingScreen fullScreen message="Preparing your workspace..." />
```

## Typography System

The KAI typography system is based on the Inter font family, providing a clean, modern look that scales well across different devices.

### Font Family

```typescript
const fonts = {
  heading: 'Inter, system-ui, sans-serif',
  body: 'Inter, system-ui, sans-serif',
  mono: 'JetBrains Mono, monospace',
}
```

### Font Weights

The typography system utilizes various font weights for different purposes:

- Light (300): For subtle, secondary text
- Regular (400): For body text
- Medium (500): For emphasis
- Semibold (600): For subheadings
- Bold (700): For headings and important UI elements

## Brand Colors

The KAI brand colors are defined in `src/theme/colors.ts` and are accessible through the Chakra UI theme system.

### Primary Brand Colors (KAI)

The mint/teal gradient is the primary brand color, with `kai.400` (`#4FDBA9`) as the main brand color:

```typescript
kai: {
  50: '#E6F7F1',   // Lightest tint
  100: '#C4EADD',
  200: '#9ADEC9',
  300: '#70D2B4',
  400: '#4FDBA9',  // Primary brand color
  500: '#33C495',  // Darker/hover state
  600: '#29A07A',  // Active state
  700: '#1F7C5F',
  800: '#155844',
  900: '#0B3429',  // Darkest shade
},
```

### Background Colors

The dark navy (`#0A1723`) serves as the primary dark mode background:

```typescript
background: {
  dark: '#0A1723',      // Dark mode background
  darkHover: '#12202D', // Dark mode hover state
  darkActive: '#1A2836',// Dark mode active state
  light: '#FFFFFF',     // Light mode background
  lightHover: '#F7FAFC',// Light mode hover state
  lightActive: '#EDF2F7',// Light mode active state
},
```

### Semantic Colors

Additional semantic colors are included for various states and feedback:

- Success: Green tones for positive actions and success states
- Error: Red tones for errors and destructive actions
- Warning: Yellow/amber tones for warnings and cautions
- Info: Blue tones for informational content

## Brand Extensions

The theme includes custom extension properties for brand-specific styling:

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
```

## Component Styling

KAI brand styles are applied to all components through the Chakra UI theme system. Key components with brand-specific styling include:

### Buttons

```typescript
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
      },
      // ...additional styles
    }),
    secondary: (props: { colorMode: string }) => ({
      bg: 'transparent',
      border: '1px solid',
      borderColor: props.colorMode === 'dark' ? 'kai.400' : 'kai.500',
      color: props.colorMode === 'dark' ? 'kai.400' : 'kai.500',
      // ...additional styles
    }),
  },
  defaultProps: {
    variant: 'primary',
  },
}
```

## Accessibility Considerations

The brand implementation follows accessibility best practices:

1. **Color Contrast**: All text colors maintain at least 4.5:1 contrast ratio against their backgrounds
2. **Color Independence**: Information is never conveyed by color alone
3. **Focus Indicators**: Clear focus indicators using the brand ring
4. **Responsive Sizing**: All elements scale appropriately for different viewport sizes

## Animation Guidelines

Brand animations follow these principles:

1. **Subtlety**: Animations are subtle and non-disruptive
2. **Purpose**: Animations serve a functional purpose (feedback, transitions, loading)
3. **Performance**: Animations are optimized for performance (using transforms and opacity)
4. **Consistency**: Similar elements use consistent animation patterns

## Implementation Notes

- The brand assets are implemented using SVG for maximum scalability
- Custom animations use CSS keyframes for better performance
- The theme is implemented using the Chakra UI theming system
- All brand elements are responsive and adapt to different screen sizes 