# KAI Main Content Area Documentation

This document outlines the architecture and components of the main content area in the KAI application. The content area follows SOLID principles and implements responsive layouts that adapt to different screen sizes and content types.

## Overall Architecture

The main content area follows a composable, flexible architecture:

1. **Content Container**: The parent component that manages overall layout and spacing
2. **Section Headers**: Standardized headers for content sections
3. **Breadcrumb Navigation**: Context-aware navigation system
4. **Grid Layout System**: Responsive grid for arranging content elements
5. **Content Components**: Specialized components that adapt to the layout system

```
┌────────────────────────────────────────────────────────────────┐
│                       Content Container                         │
│ ┌──────────────────────────────────────────────────────────────┐
│ │                     Breadcrumb Navigation                     │
│ └──────────────────────────────────────────────────────────────┘
│ ┌──────────────────────────────────────────────────────────────┐
│ │                        Section Header                         │
│ └──────────────────────────────────────────────────────────────┘
│ ┌──────────────────────────────────────────────────────────────┐
│ │                         Grid Layout                           │
│ │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────┐│
│ │ │              │ │              │ │              │ │        ││
│ │ │  Content     │ │  Content     │ │  Content     │ │Content ││
│ │ │  Component   │ │  Component   │ │  Component   │ │Compo.  ││
│ │ │              │ │              │ │              │ │        ││
│ │ └──────────────┘ └──────────────┘ └──────────────┘ └────────┘│
│ └──────────────────────────────────────────────────────────────┘
└────────────────────────────────────────────────────────────────┘
```

## Content Interfaces

The content area uses interfaces to enforce consistency and support the Interface Segregation Principle (ISP).

### Content Container Interface

```typescript
export interface IContentContainer {
  /**
   * Controls padding size around content
   */
  padding?: 'none' | 'small' | 'medium' | 'large';
  
  /**
   * Controls maximum width of the content
   */
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  
  /**
   * Background color theme for the content
   */
  background?: 'default' | 'light' | 'dark' | 'primary' | 'secondary';
  
  /**
   * Children to render within the container
   */
  children: React.ReactNode;
  
  /**
   * Whether to center the content horizontally
   */
  centerContent?: boolean;
  
  /**
   * CSS class name to apply to the container
   */
  className?: string;
  
  /**
   * Optional ID for the container element
   */
  id?: string;
  
  /**
   * Accessibility label
   */
  ariaLabel?: string;
  
  /**
   * Callback when the container is rendered
   */
  onRender?: () => void;
}
```

### Section Header Interface

```typescript
export interface ISectionHeader {
  /**
   * Main title text
   */
  title: string;
  
  /**
   * Optional subtitle or description
   */
  subtitle?: string;
  
  /**
   * Actions to display in the header (buttons, links, etc.)
   */
  actions?: React.ReactNode;
  
  /**
   * Visual size variant
   */
  size?: 'small' | 'medium' | 'large';
  
  /**
   * Divider style beneath the header
   */
  divider?: 'none' | 'thin' | 'thick';
  
  /**
   * Icon to display with the title
   */
  icon?: React.ReactNode;
  
  /**
   * CSS class name
   */
  className?: string;
}
```

### Breadcrumb Interface

```typescript
export interface IBreadcrumbItem {
  /**
   * Display label
   */
  label: string;
  
  /**
   * Navigation link
   */
  href?: string;
  
  /**
   * Whether this is the current active item
   */
  isCurrentPage?: boolean;
  
  /**
   * Custom icon for this breadcrumb item
   */
  icon?: React.ReactNode;
  
  /**
   * Click handler
   */
  onClick?: (event: React.MouseEvent) => void;
}

export interface IBreadcrumbNav {
  /**
   * Array of breadcrumb items
   */
  items: IBreadcrumbItem[];
  
  /**
   * Visual separator between items
   */
  separator?: string | React.ReactNode;
  
  /**
   * Whether to show the root item
   */
  showRoot?: boolean;
  
  /**
   * CSS class name
   */
  className?: string;
}
```

### Grid Layout Interface

```typescript
export interface IGridLayout {
  /**
   * Configuration for different screen sizes
   */
  columns?: {
    base?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  
  /**
   * Gap between grid items
   */
  spacing?: 'none' | 'small' | 'medium' | 'large';
  
  /**
   * Children to render in the grid
   */
  children: React.ReactNode;
  
  /**
   * Sets equal-height rows
   */
  equalHeight?: boolean;
  
  /**
   * Auto-fit or auto-fill behavior
   */
  autoFlow?: 'auto-fit' | 'auto-fill';
  
  /**
   * Minimum column size when using autoFlow
   */
  minColumnSize?: string;
  
  /**
   * CSS class name
   */
  className?: string;
}
```

## Content Container Implementation

The main content container provides the foundation for consistent spacing, width control, and background styling.

```tsx
export const ContentContainer: React.FC<IContentContainer> = ({
  padding = 'medium',
  maxWidth = 'lg',
  background = 'default',
  children,
  centerContent = false,
  className,
  id,
  ariaLabel,
  onRender,
}) => {
  // Map sizes to actual pixel values
  const maxWidthMap = {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    full: '100%',
  };

  // Map padding sizes to spacing values
  const paddingMap = {
    none: '0',
    small: '1rem',
    medium: '2rem',
    large: '3rem',
  };

  // Map background types to CSS classes
  const backgroundClassMap = {
    default: 'bg-white dark:bg-gray-800',
    light: 'bg-gray-50 dark:bg-gray-700',
    dark: 'bg-gray-900 dark:bg-gray-900',
    primary: 'bg-primary-50 dark:bg-primary-900',
    secondary: 'bg-secondary-50 dark:bg-secondary-900',
  };

  React.useEffect(() => {
    if (onRender) {
      onRender();
    }
  }, [onRender]);

  return (
    <div
      id={id}
      className={`kai-content-container ${backgroundClassMap[background]} ${className || ''}`}
      aria-label={ariaLabel}
      style={{
        padding: paddingMap[padding],
        maxWidth: maxWidthMap[maxWidth],
        margin: centerContent ? '0 auto' : undefined,
        width: '100%',
      }}
    >
      {children}
    </div>
  );
};
```

## Section Header Implementation

The section header provides a consistent way to introduce content sections with title, subtitle, and action elements.

```tsx
export const SectionHeader: React.FC<ISectionHeader> = ({
  title,
  subtitle,
  actions,
  size = 'medium',
  divider = 'thin',
  icon,
  className,
}) => {
  // Define size variations
  const sizeClasses = {
    small: {
      title: 'text-lg font-semibold',
      subtitle: 'text-sm',
      container: 'py-2',
    },
    medium: {
      title: 'text-xl font-semibold',
      subtitle: 'text-base',
      container: 'py-3',
    },
    large: {
      title: 'text-2xl font-semibold',
      subtitle: 'text-lg',
      container: 'py-4',
    },
  };

  // Define divider styles
  const dividerClasses = {
    none: '',
    thin: 'border-b border-gray-200 dark:border-gray-700',
    thick: 'border-b-2 border-gray-300 dark:border-gray-600',
  };

  return (
    <div className={`kai-section-header ${sizeClasses[size].container} ${dividerClasses[divider]} ${className || ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          {icon && <div className="mr-2">{icon}</div>}
          <div>
            <h2 className={sizeClasses[size].title}>{title}</h2>
            {subtitle && <p className={`${sizeClasses[size].subtitle} text-gray-600 dark:text-gray-400`}>{subtitle}</p>}
          </div>
        </div>
        {actions && <div className="flex items-center ml-4">{actions}</div>}
      </div>
    </div>
  );
};
```

## Breadcrumb Navigation Implementation

The breadcrumb navigation provides context and allows users to navigate back to parent sections.

```tsx
export const BreadcrumbNav: React.FC<IBreadcrumbNav> = ({
  items,
  separator = '/',
  showRoot = true,
  className,
}) => {
  // Filter items if not showing root
  const displayItems = showRoot ? items : items.slice(1);

  return (
    <nav aria-label="Breadcrumb" className={`kai-breadcrumb mb-4 ${className || ''}`}>
      <ol className="flex flex-wrap items-center space-x-2">
        {displayItems.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && (
              <span className="mx-2 text-gray-400 dark:text-gray-600">
                {typeof separator === 'string' ? separator : separator}
              </span>
            )}
            
            {item.href && !item.isCurrentPage ? (
              <a
                href={item.href}
                className="flex items-center text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                onClick={item.onClick}
              >
                {item.icon && <span className="mr-1">{item.icon}</span>}
                {item.label}
              </a>
            ) : (
              <span
                className={`flex items-center ${
                  item.isCurrentPage
                    ? 'text-gray-700 dark:text-gray-300 font-medium'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
                aria-current={item.isCurrentPage ? 'page' : undefined}
              >
                {item.icon && <span className="mr-1">{item.icon}</span>}
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
};
```

## Grid Layout Implementation

The grid layout system provides a responsive way to arrange content elements in a grid.

```tsx
export const GridLayout: React.FC<IGridLayout> = ({
  columns = { base: 1, sm: 2, md: 3, lg: 4, xl: 4 },
  spacing = 'medium',
  children,
  equalHeight = false,
  autoFlow,
  minColumnSize,
  className,
}) => {
  // Map spacing to pixel values
  const spacingMap = {
    none: '0',
    small: '0.5rem',
    medium: '1rem',
    large: '2rem',
  };

  // Determine grid style based on whether we're using autoFlow or explicit columns
  const gridStyle = autoFlow
    ? {
        display: 'grid',
        gridTemplateColumns: `repeat(${autoFlow}, minmax(${minColumnSize || '250px'}, 1fr))`,
        gap: spacingMap[spacing],
      }
    : {
        display: 'grid',
        gridTemplateColumns: `repeat(${columns.base}, 1fr)`,
        gap: spacingMap[spacing],
      };

  // Responsive styles for when not using autoFlow
  const responsiveStyle = !autoFlow
    ? {
        '@media (min-width: 640px)': {
          gridTemplateColumns: `repeat(${columns.sm || columns.base}, 1fr)`,
        },
        '@media (min-width: 768px)': {
          gridTemplateColumns: `repeat(${columns.md || columns.sm || columns.base}, 1fr)`,
        },
        '@media (min-width: 1024px)': {
          gridTemplateColumns: `repeat(${columns.lg || columns.md || columns.sm || columns.base}, 1fr)`,
        },
        '@media (min-width: 1280px)': {
          gridTemplateColumns: `repeat(${columns.xl || columns.lg || columns.md || columns.sm || columns.base}, 1fr)`,
        },
      }
    : {};

  return (
    <div
      className={`kai-grid-layout ${className || ''}`}
      style={{
        ...gridStyle,
        ...responsiveStyle,
        ...(equalHeight ? { gridAutoRows: '1fr' } : {}),
      }}
    >
      {children}
    </div>
  );
};
```

## Responsive Behavior

The main content area implements responsive behavior at multiple levels:

1. **Container Adaption**: The content container adjusts padding and max-width based on screen size
2. **Grid Responsiveness**: The grid layout adjusts columns based on breakpoints
3. **Component Response**: Individual components adapt to their container size

### Breakpoint System

The content area uses a standardized breakpoint system:

```typescript
// Breakpoint definitions (in pixels)
export const breakpoints = {
  xs: 0,    // Extra small devices
  sm: 640,  // Small devices (phones)
  md: 768,  // Medium devices (tablets)
  lg: 1024, // Large devices (desktops)
  xl: 1280, // Extra large devices (large desktops)
  xxl: 1536 // Extra extra large devices
};

// Media query helper
export const mediaQuery = {
  xs: `@media (min-width: ${breakpoints.xs}px)`,
  sm: `@media (min-width: ${breakpoints.sm}px)`,
  md: `@media (min-width: ${breakpoints.md}px)`,
  lg: `@media (min-width: ${breakpoints.lg}px)`,
  xl: `@media (min-width: ${breakpoints.xl}px)`,
  xxl: `@media (min-width: ${breakpoints.xxl}px)`,
};
```

## Layout Strategies

The content area supports different layout strategies to handle various content types:

### 1. Standard Content Layout

For regular content pages with a header, breadcrumbs, and body content.

```tsx
<ContentContainer padding="medium" maxWidth="lg">
  <BreadcrumbNav items={breadcrumbItems} />
  <SectionHeader title="Dashboard" subtitle="Welcome to your personalized dashboard" />
  <div className="mt-6">
    {/* Content goes here */}
  </div>
</ContentContainer>
```

### 2. Dashboard Layout

For data-rich dashboard displays with multiple sections and cards.

```tsx
<ContentContainer padding="medium" maxWidth="xl">
  <SectionHeader title="Analytics Dashboard" actions={dashboardActions} />
  <GridLayout 
    columns={{ base: 1, sm: 2, lg: 3 }} 
    spacing="medium"
  >
    <DashboardCard title="Users" value="1,234" trend="+12%" />
    <DashboardCard title="Revenue" value="$45,678" trend="+5%" />
    <DashboardCard title="Engagement" value="87%" trend="-2%" />
    <DashboardCard title="Conversion" value="3.2%" trend="+0.5%" />
    <DashboardCard title="Active Users" value="892" trend="+7%" />
    <DashboardCard title="Bounce Rate" value="24%" trend="-1%" />
  </GridLayout>
</ContentContainer>
```

### 3. Split Content Layout

For side-by-side content like forms with preview or configuration panels.

```tsx
<ContentContainer padding="medium" maxWidth="xl">
  <SectionHeader title="Profile Editor" />
  <div className="flex flex-col md:flex-row gap-4">
    <div className="flex-1">
      <ProfileForm data={profileData} onChange={handleProfileChange} />
    </div>
    <div className="flex-1">
      <ProfilePreview data={profileData} />
    </div>
  </div>
</ContentContainer>
```

### 4. List/Detail Layout

For master-detail interfaces with a list on one side and details on the other.

```tsx
<ContentContainer padding="none" maxWidth="full">
  <div className="flex h-[calc(100vh-64px)]">
    <div className="w-1/3 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
      <div className="p-4">
        <SectionHeader title="Items" size="small" />
        <ItemList items={items} onSelectItem={handleSelectItem} />
      </div>
    </div>
    <div className="w-2/3 overflow-y-auto">
      <div className="p-6">
        {selectedItem ? (
          <ItemDetail item={selectedItem} />
        ) : (
          <EmptyState message="Select an item to view details" />
        )}
      </div>
    </div>
  </div>
</ContentContainer>
```

## Accessibility Features

The content area components implement accessibility features to ensure usability for all users:

1. **Semantic HTML**: Using appropriate HTML elements like `<nav>`, `<section>`, and ARIA roles
2. **Keyboard Navigation**: Ensuring all interactive elements are accessible via keyboard
3. **Focus Management**: Proper focus handling for interactive components
4. **ARIA Attributes**: Using `aria-current`, `aria-label`, and other attributes for screen readers
5. **Color Contrast**: Ensuring sufficient contrast in all color themes
6. **Responsive Text**: Text sizes that scale appropriately across devices
7. **Reduced Motion**: Respecting user preferences for reduced motion

## Testing Approach

The content area implements thorough testing at multiple levels:

### 1. BDD Tests

Behavior Driven Development tests ensure components meet functional requirements:

```typescript
describe('ContentContainer', () => {
  it('should adapt to different padding sizes', () => {
    // Given I have a content container with small padding
    // When I render the container
    // Then it should apply the correct padding
  });
  
  it('should respect max-width settings', () => {
    // Given I have a content container with lg max-width
    // When I render the container
    // Then it should have the correct maximum width
  });
});
```

### 2. Responsive Testing

Tests that verify components adapt correctly to different screen sizes:

```typescript
describe('GridLayout Responsiveness', () => {
  it('should display correct columns on mobile', () => {
    // Given I have a grid layout with responsive column configuration
    // When I view it on a mobile-sized screen
    // Then it should display a single column
  });
  
  it('should display correct columns on desktop', () => {
    // Given I have a grid layout with responsive column configuration
    // When I view it on a desktop-sized screen
    // Then it should display four columns
  });
});
```

### 3. LSP Testing

Tests that verify the Liskov Substitution Principle is followed:

```typescript
describe('Layout Strategy Substitution', () => {
  it('should allow different content types in the grid layout', () => {
    // Given I have a grid layout
    // When I place different content components inside
    // Then all components should render properly without errors
  });
  
  it('should allow different header configurations', () => {
    // Given I have a section header
    // When I provide different combinations of title, subtitle, and actions
    // Then it should render all configurations properly
  });
});
```

## Best Practices

When using the content area components, follow these best practices:

1. **Consistency**: Use the same layout patterns across similar pages
2. **Progressive Enhancement**: Design for mobile first, then enhance for larger screens
3. **Component Composition**: Compose complex layouts from simple components
4. **Performance**: Minimize unnecessary nesting and optimize rendering
5. **Accessibility**: Ensure all content is accessible to all users
6. **Theme Consistency**: Follow the application's color theme guidelines

## Example Usage

Here's a complete example of a profile page using the content area components:

```tsx
function ProfilePage() {
  const breadcrumbItems = [
    { label: 'Home', href: '/' },
    { label: 'User', href: '/user' },
    { label: 'Profile', isCurrentPage: true }
  ];

  const profileActions = (
    <Button variant="primary" size="sm">Edit Profile</Button>
  );

  return (
    <ContentContainer maxWidth="lg" padding="medium">
      <BreadcrumbNav items={breadcrumbItems} />
      
      <SectionHeader 
        title="User Profile" 
        subtitle="View and manage your profile information"
        actions={profileActions}
        size="large"
        divider="thin"
      />
      
      <div className="mt-8">
        <GridLayout columns={{ base: 1, md: 2 }} spacing="large">
          <div>
            <SectionHeader title="Personal Information" size="medium" />
            <ProfileInfoCard user={currentUser} />
          </div>
          
          <div>
            <SectionHeader title="Account Statistics" size="medium" />
            <StatsCard stats={userStats} />
          </div>
          
          <div className="md:col-span-2">
            <SectionHeader title="Recent Activity" size="medium" />
            <ActivityFeed activities={recentActivities} />
          </div>
        </GridLayout>
      </div>
    </ContentContainer>
  );
}
```

## Conclusion

The main content area provides a flexible, accessible, and responsive foundation for building consistent user interfaces in the KAI application. By following SOLID principles and implementing a component-based architecture, it enables rapid development of new features while maintaining consistency across the application. 