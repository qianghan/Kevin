# KAI UI Design System Documentation

## Introduction

The KAI UI Design System provides a comprehensive set of design tokens, components, and patterns to create consistent, accessible, and user-friendly interfaces. This document serves as the primary reference for designers and developers working with the KAI UI Design System.

## Design Tokens

Design tokens are the fundamental building blocks of our design system, providing a single source of truth for values used throughout the application.

### Colors

```typescript
colors = {
  kai: {
    50: '#e5f6ff',
    100: '#ccedff',
    200: '#99dbff',
    300: '#66c9ff',
    400: '#33b7ff',
    500: '#00a5ff', // Primary brand color
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
}
```

#### Color Usage Guidelines

- **Primary Brand (kai.500)**: Use for primary actions, key UI elements, and brand identification
- **Text Colors**: Use appropriate text colors to maintain readability and hierarchy
- **Status Colors**: Use consistently for feedback, alerts, and status indicators
- **Background Colors**: Use to create depth and separation between UI elements

### Spacing

```typescript
spacing = {
  xxs: '0.25rem', // 4px
  xs: '0.5rem',   // 8px
  sm: '0.75rem',  // 12px
  md: '1rem',     // 16px
  lg: '1.5rem',   // 24px
  xl: '2rem',     // 32px
  xxl: '3rem',    // 48px
  xxxl: '4rem',   // 64px
}
```

#### Spacing Guidelines

- Use consistent spacing to create rhythm and relationships between elements
- Apply spacing consistently within component types
- Use smaller spacing values (xxs, xs, sm) for related elements
- Use larger spacing values (lg, xl, xxl) for separating sections or groups

### Typography

```typescript
typography = {
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
}
```

#### Typography Guidelines

- Use consistent font families for all text elements
- Apply appropriate font sizes to maintain hierarchy
- Ensure proper line heights for readability
- Maintain a consistent type scale throughout the application

### Borders

```typescript
borders = {
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
}
```

#### Border Guidelines

- Use consistent border radii to maintain visual harmony
- Apply appropriate border widths based on element emphasis
- Use borders to create visual separation and focus

### Shadows

```typescript
shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  none: 'none',
}
```

#### Shadow Guidelines

- Use shadows to create elevation and depth
- Apply consistent shadow values based on element hierarchy
- Use shadows purposefully to direct attention and create focus

### Z-Index

```typescript
zIndices = {
  hide: -1,
  base: 0,
  dropdown: 1000,
  sticky: 1100,
  overlay: 1200,
  modal: 1300,
  popover: 1400,
  toast: 1500,
  tooltip: 1600,
}
```

#### Z-Index Guidelines

- Use z-index values consistently to maintain proper stacking order
- Follow the defined z-index scale for different UI elements
- Avoid custom z-index values outside the defined scale

## Animation Tokens

Animation tokens provide consistent motion patterns throughout the application.

### Transitions

```typescript
transitions = {
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
}
```

#### Animation Guidelines

- Use consistent easing functions for similar types of animations
- Apply appropriate durations based on the type and size of animation
- Consider reduced motion preferences for accessibility
- Use animations purposefully to enhance user experience

## Component Hierarchy

The KAI UI Design System follows the atomic design methodology, organizing components into a clear hierarchy:

```
                    [Application]
                        /    \
                       /      \
                      /        \
                 [Pages]    [Templates]
                    |            |
                    v            v
                [Organisms] <- [Layouts]
                    |
                    v
                [Molecules]
                    |
                    v
                 [Atoms]
                    |
                    v
              [Design Tokens]
```

### Atoms
Basic building blocks that cannot be broken down further:
- Button
- Input
- Checkbox
- Radio
- Icon
- Text

### Molecules
Combinations of atoms that form simple components:
- Form Field (Label + Input + Error)
- Search Bar (Input + Button)
- Card Header (Title + Subtitle + Icon)
- Navigation Item (Icon + Text)

### Organisms
Complex UI components composed of molecules and atoms:
- Form
- Card
- Navigation Bar
- Modal
- Table

### Templates
Page layouts that organize organisms, molecules, and atoms:
- Dashboard Layout
- Settings Page
- Detail View
- List View

### Pages
Specific instances of templates with real content:
- User Dashboard
- User Settings
- Product Detail
- Product List

## Component Composition Guidelines

### Composition Principles

1. **Single Responsibility**: Each component should have a single responsibility
2. **Composability**: Components should be designed to work well together
3. **Encapsulation**: Components should encapsulate their complexity
4. **Reusability**: Components should be reusable in different contexts
5. **Configurability**: Components should be configurable through props

### Composition Patterns

#### Compound Components
For complex components with multiple related parts:

```jsx
<Card>
  <Card.Header title="Card Title" />
  <Card.Body>Content goes here</Card.Body>
  <Card.Footer>
    <Button>Action</Button>
  </Card.Footer>
</Card>
```

#### Render Props
For components that need to share state or behavior:

```jsx
<Dropdown>
  {({ isOpen, toggle }) => (
    <>
      <Button onClick={toggle}>Toggle</Button>
      {isOpen && <DropdownMenu />}
    </>
  )}
</Dropdown>
```

#### Component Props
For components that need to be customized:

```jsx
<Button 
  variant="primary" 
  size="lg" 
  isFullWidth={false} 
  isDisabled={false}
  leftIcon={<Icon name="check" />}
>
  Submit
</Button>
```

## Theming and Customization

The KAI UI Design System supports theming and customization through the theme provider:

```jsx
import { createTheme, ThemeProvider } from '@kai/ui';

const customTheme = createTheme({
  name: 'custom-theme',
  tokens: {
    colors: {
      kai: {
        500: '#FF0000', // Custom primary color
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={customTheme}>
      <YourApplication />
    </ThemeProvider>
  );
}
```

### Theme Extension

You can extend the default theme for minor customizations:

```jsx
import { defaultTheme, extendTheme } from '@kai/ui';

const extendedTheme = extendTheme(defaultTheme, {
  tokens: {
    colors: {
      kai: {
        500: '#FF0000', // Override primary color
      },
    },
  },
});
```

### Dark Mode

The KAI UI Design System supports dark mode through theme switching:

```jsx
import { defaultTheme, createDarkTheme, ThemeProvider } from '@kai/ui';
import { useState, useEffect } from 'react';

function App() {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const theme = isDarkMode ? createDarkTheme(defaultTheme) : defaultTheme;
  
  return (
    <ThemeProvider theme={theme}>
      <YourApplication />
      <button onClick={() => setIsDarkMode(!isDarkMode)}>
        Toggle Dark Mode
      </button>
    </ThemeProvider>
  );
}
```

## Accessibility Guidelines

### Color Contrast

- All text must meet WCAG 2.1 AA contrast requirements (4.5:1 for normal text, 3:1 for large text)
- UI controls must have a 3:1 contrast ratio against adjacent colors
- Do not rely solely on color to convey information

### Keyboard Navigation

- All interactive elements must be keyboard accessible
- Focus states must be visible and meet contrast requirements
- Tab order should follow a logical flow

### Screen Readers

- All images must have appropriate alt text
- Form fields must have associated labels
- ARIA attributes should be used appropriately
- Dynamic content changes should be announced to screen readers

### Motion and Animation

- Respect user preferences for reduced motion
- Provide alternatives for motion-based interactions
- Avoid animations that could trigger vestibular disorders

## Best Practices

### Component Usage

- Use the appropriate component for each use case
- Follow component composition guidelines
- Maintain consistent props and patterns
- Avoid unnecessary customization that breaks design consistency

### Performance Considerations

- Use code splitting for large components
- Optimize render performance for complex components
- Follow React best practices for memoization and rendering

### Responsive Design

- Follow mobile-first approach
- Use responsive props for adapting to different screen sizes
- Test components across all supported breakpoints

### Browser Support

- Support modern browsers (latest 2 versions of Chrome, Firefox, Safari, Edge)
- Implement graceful degradation for older browsers
- Test components across supported browsers

## Getting Started

### Installation

```bash
npm install @kai/ui
# or
yarn add @kai/ui
```

### Basic Usage

```jsx
import { ThemeProvider, Button, Card, Text } from '@kai/ui';

function App() {
  return (
    <ThemeProvider>
      <Card>
        <Card.Header title="Getting Started" />
        <Card.Body>
          <Text>Welcome to the KAI UI Design System!</Text>
        </Card.Body>
        <Card.Footer>
          <Button variant="primary">Get Started</Button>
        </Card.Footer>
      </Card>
    </ThemeProvider>
  );
}
```

## Resources

- **Storybook**: Run `npm run storybook` to view component documentation
- **Figma Library**: [link to Figma library]
- **GitHub Repository**: [link to GitHub repository]
- **Issue Tracker**: [link to issue tracker]

---

*This documentation is a living document and will be updated as the design system evolves.* 