# KAI Responsive Design System

This document outlines the responsive design system used throughout the KAI application. The system follows a mobile-first approach and ensures consistent behavior across all device sizes.

## Overall Architecture

The responsive design system follows a layered approach:

1. **Breakpoint System**: Defines standard screen sizes and breakpoints
2. **Container Components**: Responsive layout containers that adapt to viewport size
3. **Typography System**: Text scaling based on device size
4. **Spacing System**: Consistent spacing that adjusts for different viewports
5. **Interaction Targets**: Touch-friendly sizes for interactive elements
6. **Content Prioritization**: Rules for showing/hiding content based on viewport
7. **Image Handling**: Responsive image loading and sizing

```
┌─────────────────────────────────────────────────────────────┐
│                    Responsive Design System                  │
├─────────────┬─────────────┬─────────────┬──────────────────┤
│ Breakpoints │  Containers │ Typography  │     Spacing      │
├─────────────┼─────────────┼─────────────┼──────────────────┤
│ xs: 0px     │ Fluid       │ Base Size   │ Space Scale      │
│ sm: 640px   │ Fixed       │ Type Scale  │ Responsive Gaps  │
│ md: 768px   │ Responsive  │ Line Height │ Content Padding  │
│ lg: 1024px  │ Max-Width   │ Font Weight │ Element Margins  │
│ xl: 1280px  │ Container   │ Font Family │ Container Gutter │
│ xxl: 1536px │ Box         │ Headings    │ Inline Spacing   │
└─────────────┴─────────────┴─────────────┴──────────────────┘
```

## Breakpoint System

The breakpoint system defines standard screen sizes for responsive design decisions.

```typescript
/**
 * Breakpoint definitions (in pixels)
 */
export const breakpoints = {
  xs: 0,    // Extra small devices (portrait phones)
  sm: 640,  // Small devices (landscape phones)
  md: 768,  // Medium devices (tablets)
  lg: 1024, // Large devices (desktops)
  xl: 1280, // Extra large devices (large desktops)
  xxl: 1536  // Extra extra large devices (large monitors)
};

/**
 * Media query helpers
 */
export const mediaQuery = {
  xs: `@media (min-width: ${breakpoints.xs}px)`,
  sm: `@media (min-width: ${breakpoints.sm}px)`,
  md: `@media (min-width: ${breakpoints.md}px)`,
  lg: `@media (min-width: ${breakpoints.lg}px)`,
  xl: `@media (min-width: ${breakpoints.xl}px)`,
  xxl: `@media (min-width: ${breakpoints.xxl}px)`,
};

/**
 * Tailwind-compatible breakpoint classes for conditional rendering
 */
export const breakpointClasses = {
  xs: 'xs:',
  sm: 'sm:',
  md: 'md:',
  lg: 'lg:',
  xl: 'xl:',
  xxl: '2xl:'
};

/**
 * Helper hook for responsive logic
 */
export const useBreakpoint = () => {
  const [breakpoint, setBreakpoint] = useState<keyof typeof breakpoints>('xs');

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      if (width >= breakpoints.xxl) setBreakpoint('xxl');
      else if (width >= breakpoints.xl) setBreakpoint('xl');
      else if (width >= breakpoints.lg) setBreakpoint('lg');
      else if (width >= breakpoints.md) setBreakpoint('md');
      else if (width >= breakpoints.sm) setBreakpoint('sm');
      else setBreakpoint('xs');
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return {
    breakpoint,
    isXs: breakpoint === 'xs',
    isSm: breakpoint === 'sm' || breakpoint === 'md' || breakpoint === 'lg' || breakpoint === 'xl' || breakpoint === 'xxl',
    isMd: breakpoint === 'md' || breakpoint === 'lg' || breakpoint === 'xl' || breakpoint === 'xxl',
    isLg: breakpoint === 'lg' || breakpoint === 'xl' || breakpoint === 'xxl',
    isXl: breakpoint === 'xl' || breakpoint === 'xxl',
    isXxl: breakpoint === 'xxl',
  };
};
```

## Responsive Container Components

The container components provide consistent layout containers that adapt to different viewport sizes.

### Container Interface

```typescript
export interface IResponsiveContainer {
  /**
   * Controls maximum width behavior at different breakpoints
   */
  maxWidth?: {
    xs?: string;
    sm?: string;
    md?: string;
    lg?: string;
    xl?: string;
    xxl?: string;
  };
  
  /**
   * Controls padding at different breakpoints
   */
  padding?: {
    xs?: string;
    sm?: string;
    md?: string;
    lg?: string;
    xl?: string;
    xxl?: string;
  };
  
  /**
   * Children to render within the container
   */
  children: React.ReactNode;
  
  /**
   * Controls whether container should be centered
   */
  centered?: boolean;
  
  /**
   * CSS class name to apply
   */
  className?: string;
  
  /**
   * Background color or styling
   */
  background?: string;
  
  /**
   * Additional styling props
   */
  style?: React.CSSProperties;
}
```

### Container Implementation

```tsx
export const ResponsiveContainer: React.FC<IResponsiveContainer> = ({
  maxWidth = {
    xs: '100%', 
    sm: '100%', 
    md: '720px', 
    lg: '960px', 
    xl: '1140px', 
    xxl: '1320px'
  },
  padding = {
    xs: '1rem',
    sm: '1rem',
    md: '1.5rem',
    lg: '2rem',
    xl: '2rem',
    xxl: '2rem'
  },
  children,
  centered = true,
  className,
  background,
  style
}) => {
  // Dynamic styles based on breakpoints
  const dynamicStyles = {
    width: '100%',
    margin: centered ? '0 auto' : undefined,
    background,
    ...style
  };

  return (
    <div 
      className={`kai-responsive-container ${className || ''}`}
      style={{
        ...dynamicStyles,
        padding: padding.xs
      }}
    >
      <style jsx>{`
        .kai-responsive-container {
          max-width: ${maxWidth.xs};
        }
        
        @media (min-width: ${breakpoints.sm}px) {
          .kai-responsive-container {
            max-width: ${maxWidth.sm};
            padding: ${padding.sm};
          }
        }
        
        @media (min-width: ${breakpoints.md}px) {
          .kai-responsive-container {
            max-width: ${maxWidth.md};
            padding: ${padding.md};
          }
        }
        
        @media (min-width: ${breakpoints.lg}px) {
          .kai-responsive-container {
            max-width: ${maxWidth.lg};
            padding: ${padding.lg};
          }
        }
        
        @media (min-width: ${breakpoints.xl}px) {
          .kai-responsive-container {
            max-width: ${maxWidth.xl};
            padding: ${padding.xl};
          }
        }
        
        @media (min-width: ${breakpoints.xxl}px) {
          .kai-responsive-container {
            max-width: ${maxWidth.xxl};
            padding: ${padding.xxl};
          }
        }
      `}</style>
      {children}
    </div>
  );
};
```

## Adaptive Typography System

The typography system ensures text is legible and properly sized across all device sizes.

### Typography Interfaces

```typescript
export interface ITypographyScale {
  base: string;
  xs: string;
  sm: string;
  md: string;
  lg: string;
  xl: string;
  xxl: string;
}

export interface ITypographyProps {
  /**
   * Content to display
   */
  children: React.ReactNode;
  
  /**
   * Variant of typography (heading, body, caption)
   */
  variant?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'body1' | 'body2' | 'caption' | 'overline';
  
  /**
   * Color of the text
   */
  color?: string;
  
  /**
   * Whether text should wrap
   */
  noWrap?: boolean;
  
  /**
   * Text alignment
   */
  align?: 'left' | 'center' | 'right';
  
  /**
   * Font weight
   */
  weight?: 'light' | 'regular' | 'medium' | 'semibold' | 'bold';
  
  /**
   * Responsive font size configuration
   */
  responsive?: boolean;
  
  /**
   * Custom font size at different breakpoints
   */
  fontSize?: {
    xs?: string;
    sm?: string;
    md?: string;
    lg?: string;
    xl?: string;
    xxl?: string;
  };
  
  /**
   * CSS class name
   */
  className?: string;
}
```

### Typography Scale Definition

```typescript
export const typographyScale: Record<string, ITypographyScale> = {
  h1: {
    base: 'text-4xl',
    xs: 'text-3xl',
    sm: 'text-4xl',
    md: 'text-5xl',
    lg: 'text-5xl',
    xl: 'text-6xl',
    xxl: 'text-6xl'
  },
  h2: {
    base: 'text-3xl',
    xs: 'text-2xl',
    sm: 'text-3xl',
    md: 'text-4xl',
    lg: 'text-4xl',
    xl: 'text-5xl',
    xxl: 'text-5xl'
  },
  h3: {
    base: 'text-2xl',
    xs: 'text-xl',
    sm: 'text-2xl',
    md: 'text-3xl',
    lg: 'text-3xl',
    xl: 'text-4xl',
    xxl: 'text-4xl'
  },
  h4: {
    base: 'text-xl',
    xs: 'text-lg',
    sm: 'text-xl',
    md: 'text-2xl',
    lg: 'text-2xl',
    xl: 'text-3xl',
    xxl: 'text-3xl'
  },
  h5: {
    base: 'text-lg',
    xs: 'text-base',
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-xl',
    xl: 'text-2xl',
    xxl: 'text-2xl'
  },
  h6: {
    base: 'text-base',
    xs: 'text-sm',
    sm: 'text-base',
    md: 'text-lg',
    lg: 'text-lg',
    xl: 'text-xl',
    xxl: 'text-xl'
  },
  body1: {
    base: 'text-base',
    xs: 'text-sm',
    sm: 'text-base',
    md: 'text-base',
    lg: 'text-base',
    xl: 'text-base',
    xxl: 'text-lg'
  },
  body2: {
    base: 'text-sm',
    xs: 'text-xs',
    sm: 'text-sm',
    md: 'text-sm',
    lg: 'text-sm',
    xl: 'text-base',
    xxl: 'text-base'
  },
  caption: {
    base: 'text-xs',
    xs: 'text-xs',
    sm: 'text-xs',
    md: 'text-xs',
    lg: 'text-sm',
    xl: 'text-sm',
    xxl: 'text-sm'
  },
  overline: {
    base: 'text-xs',
    xs: 'text-xs',
    sm: 'text-xs',
    md: 'text-xs',
    lg: 'text-xs',
    xl: 'text-xs',
    xxl: 'text-sm'
  }
};
```

### Typography Component Implementation

```tsx
export const Typography: React.FC<ITypographyProps> = ({
  children,
  variant = 'body1',
  color,
  noWrap = false,
  align = 'left',
  weight = 'regular',
  responsive = true,
  fontSize,
  className
}) => {
  const { breakpoint } = useBreakpoint();
  
  // Map variant to HTML element
  const variantToElement: Record<string, string> = {
    h1: 'h1',
    h2: 'h2',
    h3: 'h3',
    h4: 'h4',
    h5: 'h5',
    h6: 'h6',
    body1: 'p',
    body2: 'p',
    caption: 'span',
    overline: 'span'
  };
  
  // Map font weight to classes
  const weightClasses: Record<string, string> = {
    light: 'font-light',
    regular: 'font-normal',
    medium: 'font-medium',
    semibold: 'font-semibold',
    bold: 'font-bold'
  };
  
  // Map text alignment to classes
  const alignClasses: Record<string, string> = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right'
  };
  
  // Determine responsive class based on breakpoint
  const responsiveClass = responsive 
    ? typographyScale[variant][breakpoint] 
    : typographyScale[variant].base;
  
  // Custom font size at current breakpoint
  const customFontSize = fontSize?.[breakpoint as keyof typeof fontSize];
  
  // Combine all classes
  const classes = [
    'kai-typography',
    responsiveClass,
    weightClasses[weight],
    alignClasses[align],
    noWrap ? 'whitespace-nowrap overflow-hidden text-ellipsis' : '',
    className
  ].filter(Boolean).join(' ');
  
  // Inline styles for color and custom font size
  const style: React.CSSProperties = {
    color: color || undefined,
    fontSize: customFontSize
  };
  
  // Dynamically create the component based on variant
  const Component = variantToElement[variant] as any;
  
  return (
    <Component className={classes} style={style}>
      {children}
    </Component>
  );
};
```

## Responsive Spacing System

The spacing system ensures consistent spacing that adapts to different viewport sizes.

### Spacing Interfaces and Scale

```typescript
/**
 * Spacing scale values
 */
export const spacingScale = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
  20: '5rem',     // 80px
  24: '6rem',     // 96px
  32: '8rem',     // 128px
  40: '10rem',    // 160px
  48: '12rem',    // 192px
  56: '14rem',    // 224px
  64: '16rem'     // 256px
};

/**
 * Responsive spacing at different breakpoints
 */
export const responsiveSpacing = {
  xs: {
    1: spacingScale[1],
    2: spacingScale[1],
    3: spacingScale[2],
    4: spacingScale[2],
    5: spacingScale[3],
    6: spacingScale[4],
    8: spacingScale[5],
    10: spacingScale[6],
    12: spacingScale[8],
    16: spacingScale[10],
    20: spacingScale[12],
    24: spacingScale[16]
  },
  sm: {
    1: spacingScale[1],
    2: spacingScale[2],
    3: spacingScale[2],
    4: spacingScale[3],
    5: spacingScale[4],
    6: spacingScale[4],
    8: spacingScale[6],
    10: spacingScale[8],
    12: spacingScale[8],
    16: spacingScale[12],
    20: spacingScale[16],
    24: spacingScale[20]
  },
  md: {
    1: spacingScale[1],
    2: spacingScale[2],
    3: spacingScale[3],
    4: spacingScale[4],
    5: spacingScale[5],
    6: spacingScale[6],
    8: spacingScale[8],
    10: spacingScale[10],
    12: spacingScale[12],
    16: spacingScale[16],
    20: spacingScale[20],
    24: spacingScale[24]
  },
  lg: spacingScale,
  xl: spacingScale,
  xxl: spacingScale
};

/**
 * Spacing component props
 */
export interface ISpacingProps {
  /**
   * Spacing size (corresponds to spacing scale)
   */
  size: keyof typeof spacingScale;
  
  /**
   * Direction of spacing
   */
  direction: 'horizontal' | 'vertical';
  
  /**
   * Whether spacing should be responsive
   */
  responsive?: boolean;
  
  /**
   * Custom spacing at different breakpoints
   */
  customSpacing?: {
    xs?: keyof typeof spacingScale;
    sm?: keyof typeof spacingScale;
    md?: keyof typeof spacingScale;
    lg?: keyof typeof spacingScale;
    xl?: keyof typeof spacingScale;
    xxl?: keyof typeof spacingScale;
  };
}
```

### Spacing Component Implementation

```tsx
export const Spacing: React.FC<ISpacingProps> = ({
  size,
  direction,
  responsive = true,
  customSpacing
}) => {
  const { breakpoint } = useBreakpoint();
  
  // Determine spacing size based on breakpoint
  const getSpacingSize = () => {
    if (customSpacing && customSpacing[breakpoint as keyof typeof customSpacing]) {
      const customSize = customSpacing[breakpoint as keyof typeof customSpacing] as keyof typeof spacingScale;
      return spacingScale[customSize];
    }
    
    if (responsive) {
      const currentScale = responsiveSpacing[breakpoint as keyof typeof responsiveSpacing];
      return (currentScale as any)[size] || spacingScale[size];
    }
    
    return spacingScale[size];
  };
  
  // Get the correct spacing size
  const spacingSize = getSpacingSize();
  
  // Apply spacing as margin or height/width
  const style = direction === 'horizontal'
    ? { display: 'inline-block', width: spacingSize, height: '1px' }
    : { display: 'block', height: spacingSize, width: '100%' };
  
  return <div style={style} aria-hidden="true" />;
};
```

## Touch-Friendly Interaction Targets

Guidelines and components for ensuring touch-friendly interaction across devices.

### Touch Target Interface

```typescript
export interface ITouchTarget {
  /**
   * Children to wrap with touch-friendly sizing
   */
  children: React.ReactNode;
  
  /**
   * Minimum size for the touch target
   */
  minSize?: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  
  /**
   * Whether to add padding to reach minimum size
   */
  addPadding?: boolean;
  
  /**
   * CSS class name
   */
  className?: string;
}
```

### Touch Target Implementation

```tsx
export const TouchTarget: React.FC<ITouchTarget> = ({
  children,
  minSize = {
    xs: '44px', // Minimum recommended by WCAG
    sm: '44px',
    md: '40px',
    lg: '36px',
    xl: '36px',
    xxl: '36px'
  },
  addPadding = true,
  className
}) => {
  const { breakpoint } = useBreakpoint();
  
  // Determine current minimum size
  const currentMinSize = minSize[breakpoint as keyof typeof minSize];
  
  // Styles to enforce minimum touch target size
  const style: React.CSSProperties = {
    minWidth: currentMinSize,
    minHeight: currentMinSize,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center'
  };
  
  // Add padding if needed
  if (addPadding) {
    style.padding = '8px';
  }
  
  return (
    <div className={`kai-touch-target ${className || ''}`} style={style}>
      {children}
    </div>
  );
};
```

## Content Prioritization System

Components and utilities for showing or hiding content based on viewport size.

### Visibility Interface

```typescript
export interface IVisibility {
  /**
   * Content to control visibility of
   */
  children: React.ReactNode;
  
  /**
   * Show on these breakpoints (empty means show on all)
   */
  showOn?: Array<keyof typeof breakpoints>;
  
  /**
   * Hide on these breakpoints (takes precedence over showOn)
   */
  hideOn?: Array<keyof typeof breakpoints>;
  
  /**
   * Whether to remove from DOM (true) or just hide with CSS (false)
   */
  removeFromDOM?: boolean;
}
```

### Visibility Component Implementation

```tsx
export const Visibility: React.FC<IVisibility> = ({
  children,
  showOn = [],
  hideOn = [],
  removeFromDOM = false
}) => {
  const { breakpoint } = useBreakpoint();
  
  // Determine if content should be visible
  const isVisible = () => {
    // If hideOn includes current breakpoint, hide content
    if (hideOn.includes(breakpoint)) {
      return false;
    }
    
    // If showOn is empty, show on all breakpoints
    if (showOn.length === 0) {
      return true;
    }
    
    // Show only on specified breakpoints
    return showOn.includes(breakpoint);
  };
  
  // Get visibility state
  const visible = isVisible();
  
  // Remove from DOM if specified and not visible
  if (!visible && removeFromDOM) {
    return null;
  }
  
  // Otherwise hide with CSS
  const style = {
    display: visible ? undefined : 'none'
  };
  
  return (
    <div className="kai-visibility" style={style}>
      {children}
    </div>
  );
};
```

## Responsive Image Handling

Components for handling responsive images with appropriate sizing and loading.

### Responsive Image Interface

```typescript
export interface IResponsiveImage {
  /**
   * Image source
   */
  src: string;
  
  /**
   * Alternative text for accessibility
   */
  alt: string;
  
  /**
   * Image width
   */
  width?: number;
  
  /**
   * Image height
   */
  height?: number;
  
  /**
   * Sources for different resolutions
   */
  srcSet?: string;
  
  /**
   * Image sizes for different viewports
   */
  sizes?: string;
  
  /**
   * Loading strategy
   */
  loading?: 'lazy' | 'eager';
  
  /**
   * Whether image should fill container
   */
  fill?: boolean;
  
  /**
   * Object fit property
   */
  objectFit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down';
  
  /**
   * CSS class name
   */
  className?: string;
  
  /**
   * Placeholder to show while loading
   */
  placeholder?: 'blur' | 'empty' | React.ReactNode;
  
  /**
   * Blur data URL for placeholder
   */
  blurDataURL?: string;
}
```

### Responsive Image Implementation

```tsx
export const ResponsiveImage: React.FC<IResponsiveImage> = ({
  src,
  alt,
  width,
  height,
  srcSet,
  sizes,
  loading = 'lazy',
  fill = false,
  objectFit = 'cover',
  className,
  placeholder = 'empty',
  blurDataURL
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const { breakpoint } = useBreakpoint();
  
  // Default sizes if not provided
  const defaultSizes = `
    (max-width: ${breakpoints.sm}px) 100vw,
    (max-width: ${breakpoints.md}px) 50vw,
    (max-width: ${breakpoints.lg}px) 33vw,
    25vw
  `;
  
  // Handle image load event
  const handleLoad = () => {
    setIsLoaded(true);
  };
  
  // Render placeholder based on type
  const renderPlaceholder = () => {
    if (isLoaded) return null;
    
    if (placeholder === 'blur' && blurDataURL) {
      return (
        <div
          className="absolute inset-0 blur-lg"
          style={{
            backgroundImage: `url(${blurDataURL})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center'
          }}
        />
      );
    }
    
    if (placeholder === 'empty') {
      return (
        <div
          className="absolute inset-0 bg-gray-200 dark:bg-gray-700 animate-pulse"
          style={{ aspectRatio: width && height ? `${width}/${height}` : undefined }}
        />
      );
    }
    
    if (placeholder !== 'blur' && placeholder !== 'empty') {
      return (
        <div className="absolute inset-0 flex items-center justify-center">
          {placeholder}
        </div>
      );
    }
    
    return null;
  };
  
  return (
    <div className={`kai-responsive-image relative ${className || ''}`} style={{ 
      position: 'relative',
      height: fill ? '100%' : undefined
    }}>
      {renderPlaceholder()}
      <img
        src={src}
        alt={alt}
        width={width}
        height={height}
        srcSet={srcSet}
        sizes={sizes || defaultSizes}
        loading={loading}
        onLoad={handleLoad}
        style={{
          objectFit,
          width: fill ? '100%' : undefined,
          height: fill ? '100%' : undefined,
          position: fill ? 'absolute' : undefined,
          opacity: isLoaded ? 1 : 0,
          transition: 'opacity 0.2s ease-in-out'
        }}
      />
    </div>
  );
};
```

## BDD Testing for Responsive Behavior

Example BDD tests for the responsive design system components.

```typescript
describe('ResponsiveContainer', () => {
  it('should adapt max-width based on screen size', () => {
    // Given I have a responsive container
    // When viewed on a mobile device
    // Then it should have 100% width with appropriate padding
    
    // When viewed on a tablet
    // Then it should have a maximum width of 720px
    
    // When viewed on a desktop
    // Then it should have a maximum width of 960px
  });
  
  it('should apply custom responsive padding', () => {
    // Given I have a responsive container with custom padding
    // When viewed at different breakpoints
    // Then it should apply the specified padding for each breakpoint
  });
});

describe('Typography', () => {
  it('should scale font size based on viewport size', () => {
    // Given I have responsive typography
    // When viewed on different device sizes
    // Then the font size should scale appropriately for each breakpoint
  });
  
  it('should render the correct HTML element for each variant', () => {
    // Given I have typography with different variants
    // When the components are rendered
    // Then each should use the appropriate semantic HTML element
  });
});

describe('Visibility Component', () => {
  it('should show content only on specified breakpoints', () => {
    // Given I have content with visibility only on desktop
    // When viewed on mobile
    // Then the content should be hidden
    
    // When viewed on desktop
    // Then the content should be visible
  });
  
  it('should remove content from DOM when specified', () => {
    // Given I have content with removeFromDOM=true that's hidden on mobile
    // When viewed on mobile
    // Then the content should not be in the DOM
    
    // When viewed on desktop
    // Then the content should be in the DOM
  });
});

describe('TouchTarget', () => {
  it('should ensure minimum touch target size across devices', () => {
    // Given I have a button wrapped in a TouchTarget
    // When viewed on mobile
    // Then the target should be at least 44px x 44px
    
    // When viewed on desktop
    // Then the target should maintain its minimum size of 36px
  });
});

describe('ResponsiveImage', () => {
  it('should load the appropriate image size based on viewport', () => {
    // Given I have a responsive image with srcSet and sizes
    // When viewed on different devices
    // Then it should load the appropriate image resolution
  });
  
  it('should show placeholder while image is loading', () => {
    // Given I have a responsive image with a blur placeholder
    // When the image is loading
    // Then it should display the blur placeholder
    
    // When the image has loaded
    // Then it should display the full image
  });
});
```

## Best Practices

Guidelines for implementing responsive designs in the KAI application:

1. **Mobile-First Approach**: Always design and code for mobile first, then enhance for larger screens
2. **Fluid Layouts**: Use percentage and viewport-based units rather than fixed pixels when possible
3. **Breakpoint Consistency**: Use the standard breakpoints defined in the system
4. **Performance**: Optimize images and assets for different viewport sizes
5. **Testing**: Test all components on various devices and screen sizes
6. **Accessibility**: Ensure tap targets meet minimum size requirements on touch devices
7. **Content Priority**: Determine which content is essential for each viewport size
8. **Responsive Typography**: Use the typography system to ensure readable text at all sizes
9. **Limited Range**: Avoid excessive variations between smallest and largest viewports
10. **Progressive Enhancement**: Add features for larger screens without breaking small screen experiences

## Usage Examples

### Responsive Container with Content

```tsx
<ResponsiveContainer
  maxWidth={{
    xs: '100%',
    md: '720px',
    lg: '960px'
  }}
  padding={{
    xs: '1rem',
    md: '2rem'
  }}
>
  <Typography variant="h1" responsive>Welcome to KAI</Typography>
  <Spacing size={4} direction="vertical" responsive />
  <Typography variant="body1" responsive>
    This content adapts to different screen sizes for optimal viewing.
  </Typography>
</ResponsiveContainer>
```

### Responsive Card Layout

```tsx
<ResponsiveContainer>
  <Typography variant="h2" responsive>Featured Items</Typography>
  <Spacing size={4} direction="vertical" responsive />
  
  <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
    {items.map(item => (
      <div key={item.id} className="bg-white p-4 rounded shadow">
        <ResponsiveImage 
          src={item.image}
          alt={item.name}
          width={300}
          height={200}
          fill
        />
        <Typography variant="h5" responsive>{item.name}</Typography>
        <Visibility hideOn={['xs', 'sm']}>
          <Typography variant="body2">{item.description}</Typography>
        </Visibility>
      </div>
    ))}
  </div>
</ResponsiveContainer>
```

### Responsive Navigation

```tsx
<nav>
  {/* Always visible logo */}
  <div className="logo">
    <ResponsiveImage src="/logo.svg" alt="KAI Logo" width={120} height={40} />
  </div>
  
  {/* Full menu on larger screens */}
  <Visibility hideOn={['xs', 'sm']}>
    <ul className="flex space-x-4">
      <li><a href="/">Home</a></li>
      <li><a href="/features">Features</a></li>
      <li><a href="/pricing">Pricing</a></li>
      <li><a href="/about">About</a></li>
      <li><a href="/contact">Contact</a></li>
    </ul>
  </Visibility>
  
  {/* Mobile menu on small screens */}
  <Visibility showOn={['xs', 'sm']}>
    <TouchTarget>
      <button aria-label="Open menu">
        <MenuIcon />
      </button>
    </TouchTarget>
  </Visibility>
</nav>
```

## Conclusion

The responsive design system provides a comprehensive foundation for creating adaptable user interfaces across all device sizes in the KAI application. By using these components and patterns consistently, the application maintains a cohesive experience from mobile to desktop while optimizing for the unique characteristics of each viewport size. 