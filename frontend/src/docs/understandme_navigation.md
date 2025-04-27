# KAI Left Navigation Panel Documentation

This document outlines the structure, components, and behaviors of the left navigation panel in the KAI application. The navigation system follows SOLID principles to provide a flexible, maintainable navigation solution.

## Overall Architecture

The left navigation panel follows a hierarchical architecture:

1. **Navigation Container**: The parent component that manages overall layout and behavior
2. **Navigation Sections**: Groupings of related navigation items
3. **Navigation Items**: Individual clickable navigation links
4. **Navigation Indicators**: Visual elements showing active state and notifications
5. **Navigation Collapse Controls**: Controls to expand/collapse sections and the entire panel

```
┌───────────────────────────────────────────┐
│         Navigation Container              │
│ ┌───────────────────────────────────────┐ │
│ │ Logo & Home                           │ │
│ └───────────────────────────────────────┘ │
│ ┌───────────────────────────────────────┐ │
│ │▼ Navigation Section                   │ │
│ ├───────────────────────────────────────┤ │
│ │  ○ Navigation Item                    │ │
│ │  ● Navigation Item (Active)           │ │
│ │  ○ Navigation Item (with Badge)  (2)  │ │
│ └───────────────────────────────────────┘ │
│ ┌───────────────────────────────────────┐ │
│ │▶ Navigation Section (Collapsed)       │ │
│ └───────────────────────────────────────┘ │
│                                           │
│ ┌───────────────────────────────────────┐ │
│ │         Collapse Control              │ │
│ └───────────────────────────────────────┘ │
└───────────────────────────────────────────┘
```

## Navigation Interfaces

The navigation system uses interfaces to ensure consistency and support the Interface Segregation Principle (ISP) and Open/Closed Principle (OCP).

### Navigation Item Interface

```typescript
export interface INavigationItem {
  /**
   * Unique identifier for the item
   */
  id: string;
  
  /**
   * Display label for the navigation item
   */
  label: string;
  
  /**
   * URL to navigate to
   */
  href: string;
  
  /**
   * Icon to display with the item
   */
  icon?: React.ReactNode;
  
  /**
   * Whether the item is currently active
   */
  isActive?: boolean;
  
  /**
   * Badge or notification count to display
   */
  badge?: number | string;
  
  /**
   * Whether the item is disabled
   */
  disabled?: boolean;
  
  /**
   * Tooltip text
   */
  tooltip?: string;
  
  /**
   * Custom color for the item
   */
  color?: string;
  
  /**
   * Required user roles to view this item
   */
  requiredRoles?: string[];
  
  /**
   * Event handler for item click
   */
  onClick?: (event: React.MouseEvent) => void;
  
  /**
   * CSS class name
   */
  className?: string;
  
  /**
   * Additional data for extension
   */
  meta?: Record<string, any>;
}
```

### Navigation Section Interface

```typescript
export interface INavigationSection {
  /**
   * Unique identifier for the section
   */
  id: string;
  
  /**
   * Display label for the section
   */
  label: string;
  
  /**
   * Icon to display with the section
   */
  icon?: React.ReactNode;
  
  /**
   * Navigation items within this section
   */
  items: INavigationItem[];
  
  /**
   * Whether the section is expanded
   */
  isExpanded?: boolean;
  
  /**
   * Whether the section is collapsible
   */
  collapsible?: boolean;
  
  /**
   * Required user roles to view this section
   */
  requiredRoles?: string[];
  
  /**
   * Event handler for section header click
   */
  onHeaderClick?: (event: React.MouseEvent) => void;
  
  /**
   * CSS class name
   */
  className?: string;
}
```

### Navigation Container Interface

```typescript
export interface INavigationContainer {
  /**
   * Navigation sections to display
   */
  sections: INavigationSection[];
  
  /**
   * Whether the navigation panel is collapsed to icons only
   */
  isCollapsed?: boolean;
  
  /**
   * Logo or brand component to display at the top
   */
  logo?: React.ReactNode;
  
  /**
   * Footer content to display at the bottom
   */
  footer?: React.ReactNode;
  
  /**
   * Whether the panel can be collapsed
   */
  collapsible?: boolean;
  
  /**
   * Event handler for collapse toggle
   */
  onCollapseToggle?: () => void;
  
  /**
   * Width of the expanded navigation panel
   */
  expandedWidth?: string;
  
  /**
   * Width of the collapsed navigation panel
   */
  collapsedWidth?: string;
  
  /**
   * Current user role(s)
   */
  userRoles?: string[];
  
  /**
   * CSS class name
   */
  className?: string;
  
  /**
   * Aria label for accessibility
   */
  ariaLabel?: string;
}
```

## Navigation Item Implementation

```tsx
export const NavigationItem: React.FC<INavigationItem> = ({
  id,
  label,
  href,
  icon,
  isActive = false,
  badge,
  disabled = false,
  tooltip,
  color,
  requiredRoles,
  onClick,
  className,
  meta
}) => {
  // Check if user has required roles (to be implemented elsewhere)
  const userHasAccess = useHasAccess(requiredRoles);
  
  if (!userHasAccess) {
    return null;
  }
  
  const handleClick = (e: React.MouseEvent) => {
    if (disabled) {
      e.preventDefault();
      return;
    }
    
    if (onClick) {
      onClick(e);
    }
  };
  
  // Default colors based on state
  const defaultColors = {
    active: {
      background: 'bg-primary-50 dark:bg-primary-900',
      text: 'text-primary-700 dark:text-primary-300',
      border: 'border-primary-500'
    },
    inactive: {
      background: 'hover:bg-gray-100 dark:hover:bg-gray-800',
      text: 'text-gray-700 dark:text-gray-300',
      border: ''
    },
    disabled: {
      background: '',
      text: 'text-gray-400 dark:text-gray-600',
      border: ''
    }
  };
  
  // Determine colors based on state
  const styleState = disabled ? 'disabled' : isActive ? 'active' : 'inactive';
  const styles = defaultColors[styleState];
  
  return (
    <li>
      <a
        href={disabled ? '#' : href}
        className={`
          kai-nav-item
          group
          flex items-center px-4 py-2 my-1 rounded-md
          ${styles.background}
          ${styles.text}
          ${isActive ? `${styles.border} border-l-4 pl-3` : ''}
          transition-colors duration-150
          ${disabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer'}
          ${className || ''}
        `}
        onClick={handleClick}
        aria-current={isActive ? 'page' : undefined}
        aria-disabled={disabled ? true : undefined}
        title={tooltip}
        style={{ color: color }}
        data-testid={`nav-item-${id}`}
      >
        {icon && <span className="mr-3 text-lg">{icon}</span>}
        <span className="flex-1 truncate">{label}</span>
        
        {badge && (
          <span className="kai-nav-badge ml-2 px-2 py-0.5 text-xs rounded-full bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200">
            {badge}
          </span>
        )}
      </a>
    </li>
  );
};
```

## Navigation Section Implementation

```tsx
export const NavigationSection: React.FC<INavigationSection> = ({
  id,
  label,
  icon,
  items,
  isExpanded = true,
  collapsible = true,
  requiredRoles,
  onHeaderClick,
  className
}) => {
  // Internal expansion state (controlled by parent or internal state)
  const [expanded, setExpanded] = useState(isExpanded);
  
  // Check if user has access to this section
  const userHasAccess = useHasAccess(requiredRoles);
  
  // Check if user has access to any items in the section
  const hasAccessibleItems = items.some(item => useHasAccess(item.requiredRoles));
  
  // Don't render if user has no access to section or any items
  if (!userHasAccess || !hasAccessibleItems) {
    return null;
  }
  
  // Toggle expanded state
  const toggleExpanded = (e: React.MouseEvent) => {
    if (collapsible) {
      setExpanded(!expanded);
      
      if (onHeaderClick) {
        onHeaderClick(e);
      }
    }
  };
  
  return (
    <div 
      className={`kai-nav-section mb-4 ${className || ''}`}
      data-testid={`nav-section-${id}`}
    >
      {/* Section Header */}
      <div
        className={`
          flex items-center px-4 py-2
          ${collapsible ? 'cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800' : ''}
          text-gray-900 dark:text-gray-100 font-medium
          rounded-md transition-colors duration-150
        `}
        onClick={toggleExpanded}
      >
        {icon && <span className="mr-3 text-lg">{icon}</span>}
        <span className="flex-1 truncate">{label}</span>
        
        {collapsible && (
          <span className={`transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}>
            <ChevronDownIcon className="h-5 w-5" />
          </span>
        )}
      </div>
      
      {/* Section Items */}
      {expanded && (
        <ul className="mt-1 ml-3">
          {items.map(item => (
            <NavigationItem
              key={item.id}
              {...item}
            />
          ))}
        </ul>
      )}
    </div>
  );
};
```

## Navigation Container Implementation

```tsx
export const NavigationContainer: React.FC<INavigationContainer> = ({
  sections,
  isCollapsed = false,
  logo,
  footer,
  collapsible = true,
  onCollapseToggle,
  expandedWidth = '240px',
  collapsedWidth = '64px',
  userRoles = [],
  className,
  ariaLabel = 'Main Navigation'
}) => {
  // Internal collapsed state
  const [collapsed, setCollapsed] = useState(isCollapsed);
  
  // Handle screen size changes
  const { breakpoint } = useBreakpoint();
  const isMobile = breakpoint === 'xs' || breakpoint === 'sm';
  
  // Handle collapse toggle
  const toggleCollapse = () => {
    const newCollapsedState = !collapsed;
    setCollapsed(newCollapsedState);
    
    if (onCollapseToggle) {
      onCollapseToggle();
    }
  };
  
  // Set width based on collapsed state
  const width = collapsed ? collapsedWidth : expandedWidth;
  
  // Hide completely on mobile when collapsed
  if (isMobile && collapsed) {
    return null;
  }
  
  return (
    <aside
      className={`
        kai-navigation-container
        h-screen
        flex flex-col
        bg-white dark:bg-gray-900
        border-r border-gray-200 dark:border-gray-800
        transition-all duration-300 ease-in-out
        ${className || ''}
      `}
      style={{ width }}
      aria-label={ariaLabel}
      data-testid="navigation-container"
    >
      {/* Logo Area */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-800">
        {logo}
      </div>
      
      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto p-2">
        <UserRolesContext.Provider value={userRoles}>
          {sections.map(section => (
            <NavigationSection
              key={section.id}
              {...section}
              // Force collapse and hide labels when panel is collapsed
              isExpanded={collapsed ? false : section.isExpanded}
            />
          ))}
        </UserRolesContext.Provider>
      </div>
      
      {/* Footer Area */}
      {footer && (
        <div className="p-4 border-t border-gray-200 dark:border-gray-800">
          {footer}
        </div>
      )}
      
      {/* Collapse Control */}
      {collapsible && !isMobile && (
        <button
          className="
            p-2 m-2
            flex justify-center items-center
            bg-gray-100 dark:bg-gray-800
            hover:bg-gray-200 dark:hover:bg-gray-700
            rounded-full
            transition-colors duration-150
          "
          onClick={toggleCollapse}
          aria-label={collapsed ? 'Expand navigation' : 'Collapse navigation'}
          title={collapsed ? 'Expand navigation' : 'Collapse navigation'}
        >
          {collapsed ? (
            <ChevronRightIcon className="h-5 w-5" />
          ) : (
            <ChevronLeftIcon className="h-5 w-5" />
          )}
        </button>
      )}
    </aside>
  );
};
```

## Role-Based Navigation Visibility

The navigation system implements role-based visibility to conditionally show navigation items based on user permissions.

### User Roles Context

```typescript
interface UserRolesContextValue {
  roles: string[];
  hasRole: (requiredRoles?: string[]) => boolean;
}

export const UserRolesContext = createContext<UserRolesContextValue>({
  roles: [],
  hasRole: () => true
});

export const UserRolesProvider: React.FC<{ roles: string[]; children: React.ReactNode }> = ({
  roles,
  children
}) => {
  const hasRole = useCallback(
    (requiredRoles?: string[]) => {
      // If no roles required, allow access
      if (!requiredRoles || requiredRoles.length === 0) {
        return true;
      }
      
      // Check if user has any of the required roles
      return requiredRoles.some(role => roles.includes(role));
    },
    [roles]
  );
  
  return (
    <UserRolesContext.Provider value={{ roles, hasRole }}>
      {children}
    </UserRolesContext.Provider>
  );
};

// Hook to check if user has access
export const useHasAccess = (requiredRoles?: string[]) => {
  const { hasRole } = useContext(UserRolesContext);
  return hasRole(requiredRoles);
};
```

## Responsive Navigation Behavior

The navigation panel adapts to different screen sizes with the following behaviors:

### Mobile Behavior (xs, sm)

- Navigation is hidden by default
- Opens as a sliding drawer when toggled
- Covers part of the content when open
- Includes a backdrop/overlay that dismisses the navigation when tapped
- Always shows in full width mode, never collapsed icon-only mode

### Tablet Behavior (md)

- Navigation is visible in collapsed (icon-only) mode by default
- Can be expanded to full width
- Pushes content when expanded/collapsed

### Desktop Behavior (lg, xl, xxl)

- Navigation is visible in expanded mode by default
- Can be collapsed to icon-only mode
- Pushes content when expanded/collapsed

```tsx
// Mobile-specific implementation
export const MobileNavigation: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  sections: INavigationSection[];
  logo: React.ReactNode;
  userRoles?: string[];
}> = ({ isOpen, onClose, sections, logo, userRoles = [] }) => {
  return (
    <>
      {/* Backdrop/overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      
      {/* Sliding drawer */}
      <div
        className={`
          fixed inset-y-0 left-0 z-50
          w-64 bg-white dark:bg-gray-900
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="h-full flex flex-col">
          {/* Close button */}
          <div className="p-4 flex items-center justify-between border-b border-gray-200 dark:border-gray-800">
            {logo}
            <button
              className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800"
              onClick={onClose}
              aria-label="Close navigation"
            >
              <XIcon className="h-5 w-5" />
            </button>
          </div>
          
          {/* Navigation content */}
          <div className="flex-1 overflow-y-auto p-2">
            <UserRolesContext.Provider value={{ roles: userRoles, hasRole: () => true }}>
              {sections.map(section => (
                <NavigationSection
                  key={section.id}
                  {...section}
                  onHeaderClick={() => {/* Keep drawer open */}}
                />
              ))}
            </UserRolesContext.Provider>
          </div>
        </div>
      </div>
    </>
  );
};

// Responsive navigation wrapper
export const ResponsiveNavigation: React.FC<INavigationContainer & { mobileMenuOpen: boolean; setMobileMenuOpen: (open: boolean) => void }> = ({
  mobileMenuOpen,
  setMobileMenuOpen,
  ...props
}) => {
  const { breakpoint } = useBreakpoint();
  const isMobile = breakpoint === 'xs' || breakpoint === 'sm';
  
  if (isMobile) {
    return (
      <MobileNavigation
        isOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        sections={props.sections}
        logo={props.logo}
        userRoles={props.userRoles}
      />
    );
  }
  
  return <NavigationContainer {...props} />;
};
```

## BDD Tests for Navigation Panel

```typescript
describe('NavigationItem', () => {
  it('should render correctly with all props', () => {
    // Given I have a navigation item with all props
    // When the component is rendered
    // Then it should display the label, icon, and badge
  });
  
  it('should handle active state properly', () => {
    // Given I have a navigation item in active state
    // When the component is rendered
    // Then it should have the active styling and aria-current="page"
  });
  
  it('should not be clickable when disabled', () => {
    // Given I have a disabled navigation item
    // When I click on it
    // Then the click handler should not be called
    // And it should have disabled styling
  });
  
  it('should hide items based on user roles', () => {
    // Given I have a navigation item requiring "admin" role
    // When the user does not have that role
    // Then the item should not be rendered
  });
});

describe('NavigationSection', () => {
  it('should expand and collapse when clicked', () => {
    // Given I have a collapsible navigation section
    // When I click on the section header
    // Then the section should toggle between expanded and collapsed states
  });
  
  it('should not be collapsible when collapsible is false', () => {
    // Given I have a non-collapsible navigation section
    // When I click on the section header
    // Then the section should remain expanded
    // And no collapse arrow should be shown
  });
  
  it('should hide entire section if no accessible items', () => {
    // Given I have a section where all items require roles the user doesn't have
    // When the component is rendered
    // Then the entire section should not be rendered
  });
});

describe('NavigationContainer', () => {
  it('should toggle between expanded and collapsed states', () => {
    // Given I have a navigation container
    // When I click the collapse button
    // Then the container should toggle between expanded and collapsed widths
  });
  
  it('should hide labels when collapsed', () => {
    // Given I have a collapsed navigation container
    // When the component is rendered
    // Then only icons should be visible, not text labels
  });
  
  it('should adapt to mobile screen sizes', () => {
    // Given I have a navigation container
    // When viewed on a mobile device
    // Then it should render as a slide-out drawer with overlay
  });
});
```

## Testing Navigation Component Substitution (LSP)

Liskov Substitution Principle (LSP) tests for the navigation system ensure that specialized navigation implementations can be substituted for the base implementation.

```typescript
describe('LSP Navigation Tests', () => {
  it('should allow substituting specialized navigation items', () => {
    // Given I have a custom navigation item extending INavigationItem
    // When I use it in place of the standard NavigationItem
    // Then it should function properly in the navigation system
  });
  
  it('should allow substituting specialized navigation sections', () => {
    // Given I have a custom navigation section with additional features
    // When I use it in place of the standard NavigationSection
    // Then it should function properly in the navigation system
  });
  
  it('should allow substituting the entire navigation container', () => {
    // Given I have a custom navigation container implementation
    // When I use it in place of the standard NavigationContainer
    // Then it should provide equivalent functionality
  });
});
```

## Example Usage

### Basic Navigation Setup

```tsx
// Example navigation structure
const navigationSections: INavigationSection[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <DashboardIcon />,
    items: [
      {
        id: 'home',
        label: 'Home',
        href: '/',
        icon: <HomeIcon />,
        isActive: true
      },
      {
        id: 'analytics',
        label: 'Analytics',
        href: '/analytics',
        icon: <ChartIcon />
      }
    ]
  },
  {
    id: 'content',
    label: 'Content',
    icon: <DocumentIcon />,
    items: [
      {
        id: 'articles',
        label: 'Articles',
        href: '/articles',
        icon: <ArticleIcon />
      },
      {
        id: 'media',
        label: 'Media Library',
        href: '/media',
        icon: <MediaIcon />,
        badge: 3
      }
    ]
  },
  {
    id: 'admin',
    label: 'Administration',
    icon: <SettingsIcon />,
    requiredRoles: ['admin'],
    items: [
      {
        id: 'users',
        label: 'User Management',
        href: '/admin/users',
        icon: <UsersIcon />
      },
      {
        id: 'settings',
        label: 'System Settings',
        href: '/admin/settings',
        icon: <CogIcon />
      }
    ]
  }
];

// Usage in application
const AppNavigation = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const userRoles = ['user']; // Example roles

  return (
    <>
      {/* Mobile menu button (only on small screens) */}
      <div className="block sm:hidden">
        <button 
          onClick={() => setMobileMenuOpen(true)}
          className="p-2 rounded-md"
        >
          <MenuIcon className="h-6 w-6" />
        </button>
      </div>
      
      <ResponsiveNavigation
        sections={navigationSections}
        logo={<LogoComponent />}
        footer={<UserProfileComponent />}
        userRoles={userRoles}
        mobileMenuOpen={mobileMenuOpen}
        setMobileMenuOpen={setMobileMenuOpen}
      />
    </>
  );
};
```

### Advanced Navigation with Multiple Levels

```tsx
// Multi-level navigation with custom item renderer
const CustomNavigationItem: React.FC<INavigationItem & { depth?: number }> = ({
  depth = 0,
  ...props
}) => {
  return (
    <li 
      style={{ 
        paddingLeft: `${depth * 12}px` 
      }}
    >
      <NavigationItem {...props} />
    </li>
  );
};

// Usage with nested items
const nestedNavigation = {
  id: 'products',
  label: 'Products',
  icon: <ProductIcon />,
  items: [
    {
      id: 'categories',
      label: 'Categories',
      href: '/products/categories',
      icon: <FolderIcon />,
      // Subcomponents can be rendered in the meta object
      meta: {
        subItems: [
          { id: 'electronics', label: 'Electronics', href: '/products/categories/electronics' },
          { id: 'clothing', label: 'Clothing', href: '/products/categories/clothing' }
        ]
      }
    }
  ]
};

// Custom renderer for section that handles nested items
const NestedNavigationSection: React.FC<INavigationSection> = (props) => {
  // ... implementation that can render nested items from meta.subItems
};
```

## Conclusion

The KAI Left Navigation Panel provides a flexible, accessible, and responsive navigation solution. By following SOLID principles, particularly Interface Segregation Principle (ISP) and Open/Closed Principle (OCP), the navigation system can be easily extended and customized while maintaining a consistent user experience. 