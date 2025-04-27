# KAI Top Bar Documentation

This document outlines the structure, components, and behaviors of the top bar in the KAI application. The top bar follows SOLID principles to provide a cohesive, maintainable header solution.

## Overall Architecture

The top bar follows a modular, component-based architecture:

1. **Top Bar Container**: The parent component that manages layout and positioning
2. **Logo & Home Button**: Application branding and quick navigation
3. **Search Component**: Global search functionality
4. **Notifications Dropdown**: User notifications and alerts
5. **Settings Menu**: Application-wide settings and preferences
6. **User Profile Menu**: User-specific actions and information
7. **Language Selector**: Multi-language support

```
┌─────────────────────────────────────────────────────────────────────────┐
│                             Top Bar Container                            │
├─────────────┬───────────────┬─────────────────┬─────────────────────────┤
│ Logo & Home │    Search     │   Navigation    │      User Actions       │
│             │               │   (optional)    │                         │
│   ┌─────┐   │ ┌───────────┐ │  ┌───┐  ┌───┐  │ ┌───┐  ┌───┐  ┌───────┐ │
│   │ KAI │   │ │  🔍 Search │ │  │ 1 │  │ 2 │  │ │🔔 │  │🌐 │  │ User  │ │
│   └─────┘   │ └───────────┘ │  └───┘  └───┘  │ └───┘  └───┘  └───────┘ │
└─────────────┴───────────────┴─────────────────┴─────────────────────────┘
```

## Top Bar Interfaces

The top bar system uses interfaces to ensure consistency and support the Interface Segregation Principle (ISP).

### Top Bar Container Interface

```typescript
export interface ITopBarContainer {
  /**
   * Logo/home button component
   */
  logo: React.ReactNode;
  
  /**
   * Whether to show the search component
   */
  showSearch?: boolean;
  
  /**
   * Search component props
   */
  searchProps?: ISearchProps;
  
  /**
   * Navigation links to display in the center
   */
  navigationLinks?: INavigationLink[];
  
  /**
   * Notification component props
   */
  notificationProps?: INotificationProps;
  
  /**
   * Settings menu props
   */
  settingsProps?: ISettingsProps;
  
  /**
   * User profile props
   */
  userProfileProps?: IUserProfileProps;
  
  /**
   * Language selector props
   */
  languageSelectorProps?: ILanguageSelectorProps;
  
  /**
   * Whether the top bar is fixed at the top
   */
  isFixed?: boolean;
  
  /**
   * Custom background color
   */
  backgroundColor?: string;
  
  /**
   * CSS class name
   */
  className?: string;
  
  /**
   * Children to render in the top bar
   */
  children?: React.ReactNode;
}
```

### Navigation Link Interface

```typescript
export interface INavigationLink {
  /**
   * Link label
   */
  label: string;
  
  /**
   * Link URL
   */
  href: string;
  
  /**
   * Whether the link is active
   */
  isActive?: boolean;
  
  /**
   * Icon to display with the link
   */
  icon?: React.ReactNode;
  
  /**
   * Whether the link opens in a new tab
   */
  isExternal?: boolean;
  
  /**
   * Click handler
   */
  onClick?: (e: React.MouseEvent) => void;
}
```

### Search Props Interface

```typescript
export interface ISearchProps {
  /**
   * Placeholder text
   */
  placeholder?: string;
  
  /**
   * Initial search query
   */
  initialQuery?: string;
  
  /**
   * Whether the search is expanded by default
   */
  isExpanded?: boolean;
  
  /**
   * Handler for search submission
   */
  onSearch: (query: string) => void;
  
  /**
   * Suggested search items
   */
  suggestions?: {
    label: string;
    value: string;
    category?: string;
  }[];
  
  /**
   * Maximum number of suggestions to show
   */
  maxSuggestions?: number;
}
```

### Notification Props Interface

```typescript
export interface INotificationProps {
  /**
   * Notification items
   */
  notifications: {
    id: string;
    title: string;
    message: string;
    time: string;
    isRead: boolean;
    type: 'info' | 'success' | 'warning' | 'error';
    link?: string;
  }[];
  
  /**
   * Number of unread notifications
   */
  unreadCount?: number;
  
  /**
   * Handler for marking notifications as read
   */
  onMarkAsRead: (id: string) => void;
  
  /**
   * Handler for marking all notifications as read
   */
  onMarkAllAsRead: () => void;
  
  /**
   * Handler for notification click
   */
  onNotificationClick?: (id: string) => void;
}
```

### User Profile Props Interface

```typescript
export interface IUserProfileProps {
  /**
   * User's display name
   */
  displayName: string;
  
  /**
   * User's email
   */
  email: string;
  
  /**
   * User's avatar URL
   */
  avatarUrl?: string;
  
  /**
   * User's role
   */
  role?: string;
  
  /**
   * Profile menu items
   */
  menuItems: {
    label: string;
    icon?: React.ReactNode;
    href?: string;
    onClick?: () => void;
    divider?: boolean;
  }[];
  
  /**
   * Handler for logout
   */
  onLogout: () => void;
}
```

## Component Implementations

### Top Bar Container

```tsx
export const TopBarContainer: React.FC<ITopBarContainer> = ({
  logo,
  showSearch = true,
  searchProps,
  navigationLinks,
  notificationProps,
  settingsProps,
  userProfileProps,
  languageSelectorProps,
  isFixed = true,
  backgroundColor,
  className,
  children
}) => {
  return (
    <header
      className={`
        kai-topbar
        w-full h-16
        bg-white dark:bg-gray-900
        border-b border-gray-200 dark:border-gray-800
        ${isFixed ? 'fixed top-0 left-0 right-0 z-50' : 'relative'}
        ${className || ''}
      `}
      style={{ backgroundColor }}
      data-testid="topbar-container"
    >
      <div className="h-full max-w-screen-2xl mx-auto px-4 flex items-center justify-between">
        {/* Left section - Logo and search */}
        <div className="flex items-center space-x-4">
          {/* Logo */}
          <div className="flex-shrink-0">
            {logo}
          </div>
          
          {/* Search */}
          {showSearch && searchProps && (
            <div className="hidden sm:block">
              <TopBarSearch {...searchProps} />
            </div>
          )}
        </div>
        
        {/* Center section - Navigation links */}
        {navigationLinks && navigationLinks.length > 0 && (
          <div className="hidden md:flex items-center space-x-4">
            {navigationLinks.map((link, index) => (
              <TopBarNavigationLink key={index} {...link} />
            ))}
          </div>
        )}
        
        {/* Right section - User actions */}
        <div className="flex items-center space-x-2">
          {/* Notifications */}
          {notificationProps && (
            <NotificationsDropdown {...notificationProps} />
          )}
          
          {/* Settings */}
          {settingsProps && (
            <SettingsDropdown {...settingsProps} />
          )}
          
          {/* Language selector */}
          {languageSelectorProps && (
            <LanguageSelector {...languageSelectorProps} />
          )}
          
          {/* User profile */}
          {userProfileProps && (
            <UserProfileMenu {...userProfileProps} />
          )}
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <MobileMenuButton />
          </div>
        </div>
        
        {/* Additional children */}
        {children}
      </div>
    </header>
  );
};
```

### KAI Logo and Home Button

```tsx
export interface ILogoProps {
  /**
   * Logo size variant
   */
  size?: 'small' | 'medium' | 'large';
  
  /**
   * Logo color variant
   */
  variant?: 'light' | 'dark' | 'color';
  
  /**
   * URL to navigate to on click
   */
  homeUrl?: string;
}

export const KAILogo: React.FC<ILogoProps> = ({
  size = 'medium',
  variant = 'color',
  homeUrl = '/'
}) => {
  // Size mapping
  const sizeClasses = {
    small: 'h-6',
    medium: 'h-8',
    large: 'h-10'
  };
  
  // Variant mapping
  const logoSrc = {
    light: '/assets/logo-light.svg',
    dark: '/assets/logo-dark.svg',
    color: '/assets/logo-color.svg'
  };
  
  return (
    <a 
      href={homeUrl}
      className="flex items-center focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
      aria-label="KAI Home"
    >
      <img 
        src={logoSrc[variant]} 
        alt="KAI Logo" 
        className={sizeClasses[size]}
      />
    </a>
  );
};
```

### Notifications Dropdown

```tsx
export const NotificationsDropdown: React.FC<INotificationProps> = ({
  notifications,
  unreadCount = 0,
  onMarkAsRead,
  onMarkAllAsRead,
  onNotificationClick
}) => {
  const [isOpen, setIsOpen] = useState(false);
  
  // Toggle dropdown
  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };
  
  // Close dropdown
  const closeDropdown = () => {
    setIsOpen(false);
  };
  
  // Handle notification click
  const handleNotificationClick = (id: string) => {
    onMarkAsRead(id);
    
    if (onNotificationClick) {
      onNotificationClick(id);
    }
    
    closeDropdown();
  };
  
  // Get icon based on notification type
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'info':
        return <InfoIcon className="h-5 w-5 text-blue-500" />;
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'warning':
        return <ExclamationIcon className="h-5 w-5 text-yellow-500" />;
      case 'error':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <BellIcon className="h-5 w-5 text-gray-500" />;
    }
  };
  
  return (
    <div className="relative">
      {/* Notification button */}
      <button
        className="
          p-2 rounded-full
          text-gray-600 dark:text-gray-300
          hover:bg-gray-100 dark:hover:bg-gray-800
          focus:outline-none focus:ring-2 focus:ring-primary-500
          relative
        "
        onClick={toggleDropdown}
        aria-label={`Notifications ${unreadCount > 0 ? `(${unreadCount} unread)` : ''}`}
        aria-expanded={isOpen}
        aria-controls="notifications-dropdown"
      >
        <BellIcon className="h-6 w-6" />
        
        {/* Notification badge */}
        {unreadCount > 0 && (
          <span className="
            absolute top-0 right-0
            bg-red-500 text-white
            text-xs font-bold
            rounded-full h-5 w-5
            flex items-center justify-center
          ">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>
      
      {/* Dropdown menu */}
      {isOpen && (
        <div
          id="notifications-dropdown"
          className="
            absolute right-0 mt-2
            w-80 max-h-96
            bg-white dark:bg-gray-900
            border border-gray-200 dark:border-gray-800
            rounded-md shadow-lg
            overflow-hidden z-50
          "
        >
          {/* Header */}
          <div className="p-3 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center">
            <h3 className="font-medium text-gray-900 dark:text-gray-100">Notifications</h3>
            {unreadCount > 0 && (
              <button
                className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
                onClick={() => {
                  onMarkAllAsRead();
                  closeDropdown();
                }}
              >
                Mark all as read
              </button>
            )}
          </div>
          
          {/* Notification list */}
          <div className="overflow-y-auto max-h-80">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500 dark:text-gray-400">
                No notifications
              </div>
            ) : (
              <ul>
                {notifications.map(notification => (
                  <li
                    key={notification.id}
                    className={`
                      p-3 border-b border-gray-100 dark:border-gray-800 last:border-0
                      hover:bg-gray-50 dark:hover:bg-gray-800
                      cursor-pointer
                      ${!notification.isRead ? 'bg-primary-50 dark:bg-primary-900/20' : ''}
                    `}
                    onClick={() => handleNotificationClick(notification.id)}
                  >
                    <div className="flex">
                      <div className="flex-shrink-0 mr-3">
                        {getNotificationIcon(notification.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                          {notification.title}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {notification.time}
                        </p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
          
          {/* Footer */}
          <div className="p-2 border-t border-gray-200 dark:border-gray-800 text-center">
            <a
              href="/notifications"
              className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
              onClick={closeDropdown}
            >
              View all notifications
            </a>
          </div>
        </div>
      )}
    </div>
  );
};
```

### Language Selector

```tsx
export interface ILanguageSelectorProps {
  /**
   * Current language
   */
  currentLanguage: string;
  
  /**
   * Available languages
   */
  languages: {
    code: string;
    name: string;
    flag?: string;
  }[];
  
  /**
   * Handler for language change
   */
  onLanguageChange: (languageCode: string) => void;
}

export const LanguageSelector: React.FC<ILanguageSelectorProps> = ({
  currentLanguage,
  languages,
  onLanguageChange
}) => {
  const [isOpen, setIsOpen] = useState(false);
  
  // Current language data
  const current = languages.find(lang => lang.code === currentLanguage) || languages[0];
  
  // Toggle dropdown
  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };
  
  // Close dropdown
  const closeDropdown = () => {
    setIsOpen(false);
  };
  
  // Handle language selection
  const handleLanguageSelect = (code: string) => {
    onLanguageChange(code);
    closeDropdown();
  };
  
  return (
    <div className="relative">
      {/* Language button */}
      <button
        className="
          p-2 rounded-full
          text-gray-600 dark:text-gray-300
          hover:bg-gray-100 dark:hover:bg-gray-800
          focus:outline-none focus:ring-2 focus:ring-primary-500
          flex items-center
        "
        onClick={toggleDropdown}
        aria-label="Select language"
        aria-expanded={isOpen}
        aria-controls="language-dropdown"
      >
        {current.flag ? (
          <span className="mr-1">{current.flag}</span>
        ) : (
          <GlobeIcon className="h-5 w-5" />
        )}
        <span className="sr-only md:not-sr-only md:ml-1 text-sm">
          {current.code.toUpperCase()}
        </span>
      </button>
      
      {/* Dropdown menu */}
      {isOpen && (
        <div
          id="language-dropdown"
          className="
            absolute right-0 mt-2
            w-48
            bg-white dark:bg-gray-900
            border border-gray-200 dark:border-gray-800
            rounded-md shadow-lg
            overflow-hidden z-50
          "
        >
          <ul className="py-1">
            {languages.map(language => (
              <li key={language.code}>
                <button
                  className={`
                    w-full text-left px-4 py-2 text-sm
                    ${currentLanguage === language.code
                      ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                      : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                    }
                  `}
                  onClick={() => handleLanguageSelect(language.code)}
                >
                  <span className="flex items-center">
                    {language.flag && <span className="mr-2">{language.flag}</span>}
                    {language.name}
                    {currentLanguage === language.code && (
                      <CheckIcon className="h-4 w-4 ml-auto" />
                    )}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
```

### User Profile Menu

```tsx
export const UserProfileMenu: React.FC<IUserProfileProps> = ({
  displayName,
  email,
  avatarUrl,
  role,
  menuItems,
  onLogout
}) => {
  const [isOpen, setIsOpen] = useState(false);
  
  // Toggle dropdown
  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };
  
  // Close dropdown
  const closeDropdown = () => {
    setIsOpen(false);
  };
  
  // Generate avatar fallback using initials
  const getInitials = () => {
    return displayName
      .split(' ')
      .map(name => name[0])
      .join('')
      .toUpperCase()
      .substring(0, 2);
  };
  
  return (
    <div className="relative">
      {/* Profile button */}
      <button
        className="
          flex items-center
          focus:outline-none focus:ring-2 focus:ring-primary-500 rounded-full
        "
        onClick={toggleDropdown}
        aria-label="User menu"
        aria-expanded={isOpen}
        aria-controls="user-menu-dropdown"
      >
        {/* Avatar */}
        <div className="h-8 w-8 rounded-full overflow-hidden bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
          {avatarUrl ? (
            <img
              src={avatarUrl}
              alt={displayName}
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="text-sm font-medium text-primary-700 dark:text-primary-300">
              {getInitials()}
            </span>
          )}
        </div>
        
        {/* Name (visible on larger screens) */}
        <span className="hidden md:block ml-2 text-sm font-medium text-gray-700 dark:text-gray-300">
          {displayName}
        </span>
        
        {/* Dropdown indicator */}
        <ChevronDownIcon className="hidden md:block h-4 w-4 ml-1 text-gray-500 dark:text-gray-400" />
      </button>
      
      {/* Dropdown menu */}
      {isOpen && (
        <div
          id="user-menu-dropdown"
          className="
            absolute right-0 mt-2
            w-64
            bg-white dark:bg-gray-900
            border border-gray-200 dark:border-gray-800
            rounded-md shadow-lg
            overflow-hidden z-50
          "
        >
          {/* User info */}
          <div className="p-4 border-b border-gray-200 dark:border-gray-800">
            <div className="flex items-center">
              <div className="h-10 w-10 rounded-full overflow-hidden bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                {avatarUrl ? (
                  <img
                    src={avatarUrl}
                    alt={displayName}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span className="text-lg font-medium text-primary-700 dark:text-primary-300">
                    {getInitials()}
                  </span>
                )}
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {displayName}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {email}
                </p>
                {role && (
                  <p className="text-xs text-primary-600 dark:text-primary-400 mt-1">
                    {role}
                  </p>
                )}
              </div>
            </div>
          </div>
          
          {/* Menu items */}
          <div className="py-1">
            {menuItems.map((item, index) => (
              <React.Fragment key={index}>
                {item.divider && (
                  <hr className="my-1 border-gray-200 dark:border-gray-800" />
                )}
                <a
                  href={item.href || '#'}
                  className="
                    block px-4 py-2 text-sm
                    text-gray-700 hover:bg-gray-100 hover:text-gray-900
                    dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-gray-100
                  "
                  onClick={(e) => {
                    if (item.onClick) {
                      e.preventDefault();
                      item.onClick();
                      closeDropdown();
                    }
                  }}
                >
                  <div className="flex items-center">
                    {item.icon && (
                      <span className="mr-2">{item.icon}</span>
                    )}
                    {item.label}
                  </div>
                </a>
              </React.Fragment>
            ))}
            
            {/* Logout */}
            <button
              className="
                w-full text-left px-4 py-2 text-sm
                text-red-600 hover:bg-red-50 hover:text-red-700
                dark:text-red-400 dark:hover:bg-red-900/20 dark:hover:text-red-300
              "
              onClick={() => {
                onLogout();
                closeDropdown();
              }}
            >
              <div className="flex items-center">
                <LogoutIcon className="h-5 w-5 mr-2" />
                Sign out
              </div>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
```

## Responsive Behavior

The top bar implements responsive behavior to adapt to different screen sizes:

### Mobile (xs, sm)

- Logo is smaller
- Search is hidden or collapsible
- Navigation links are moved to a mobile menu
- Only essential action buttons are shown
- User name is hidden, only avatar is shown

### Tablet (md)

- Logo is medium-sized
- Search is visible
- Navigation links are visible
- All action buttons are shown
- User name is visible

### Desktop (lg, xl, xxl)

- Full functionality
- Optimized spacing
- Potential for additional features

```tsx
// Mobile menu button component
export const MobileMenuButton: React.FC<{ onClick?: () => void }> = ({ onClick }) => {
  return (
    <button
      className="
        p-2 rounded-md
        text-gray-700 dark:text-gray-300
        hover:bg-gray-100 dark:hover:bg-gray-800
        focus:outline-none focus:ring-2 focus:ring-primary-500
      "
      aria-label="Open main menu"
      onClick={onClick}
    >
      <MenuIcon className="h-6 w-6" />
    </button>
  );
};

// Mobile top bar specific implementation
export const MobileTopBar: React.FC<{
  logo: React.ReactNode;
  onMenuClick: () => void;
  userProfileProps?: IUserProfileProps;
  notificationProps?: INotificationProps;
}> = ({
  logo,
  onMenuClick,
  userProfileProps,
  notificationProps
}) => {
  return (
    <header className="h-16 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 fixed top-0 left-0 right-0 z-50">
      <div className="h-full px-4 flex items-center justify-between">
        {/* Logo */}
        <div className="flex-shrink-0">
          {logo}
        </div>
        
        {/* Right actions */}
        <div className="flex items-center space-x-1">
          {/* Notifications (compact) */}
          {notificationProps && (
            <CompactNotificationsButton
              unreadCount={notificationProps.unreadCount || 0}
              onClick={() => {/* Open notifications */}}
            />
          )}
          
          {/* User avatar (without name) */}
          {userProfileProps && (
            <CompactUserButton
              avatarUrl={userProfileProps.avatarUrl}
              displayName={userProfileProps.displayName}
              onClick={() => {/* Open user menu */}}
            />
          )}
          
          {/* Menu button */}
          <MobileMenuButton onClick={onMenuClick} />
        </div>
      </div>
    </header>
  );
};
```

## BDD Tests for Top Bar

```typescript
describe('TopBarContainer', () => {
  it('should render all provided components', () => {
    // Given I have a top bar with all components
    // When the component is rendered
    // Then it should display logo, search, navigation links, and user actions
  });
  
  it('should adapt to different screen sizes', () => {
    // Given I have a top bar
    // When viewed on a mobile device
    // Then it should hide certain elements and show a mobile menu button
    
    // When viewed on a desktop
    // Then it should show all elements
  });
});

describe('NotificationsDropdown', () => {
  it('should display notification count badge', () => {
    // Given I have unread notifications
    // When the component is rendered
    // Then it should display the unread count badge
  });
  
  it('should toggle dropdown when clicked', () => {
    // Given I have a notifications dropdown
    // When I click the notification button
    // Then it should toggle the visibility of the dropdown
  });
  
  it('should mark notifications as read when clicked', () => {
    // Given I have unread notifications
    // When I click on a notification
    // Then it should call the onMarkAsRead handler with the correct ID
  });
});

describe('UserProfileMenu', () => {
  it('should display the user avatar and name', () => {
    // Given I have user profile data
    // When the component is rendered
    // Then it should display the avatar and name
  });
  
  it('should render initials when no avatar is provided', () => {
    // Given I have a user profile without an avatar
    // When the component is rendered
    // Then it should display the user's initials
  });
  
  it('should show menu items when clicked', () => {
    // Given I have a user profile menu
    // When I click on the profile button
    // Then it should display the menu items
  });
  
  it('should trigger logout when logout button is clicked', () => {
    // Given I have an open user profile menu
    // When I click the logout button
    // Then it should call the onLogout handler
  });
});

describe('LanguageSelector', () => {
  it('should display the current language', () => {
    // Given I have a language selector with a current language
    // When the component is rendered
    // Then it should display the current language code
  });
  
  it('should show language options when clicked', () => {
    // Given I have a language selector
    // When I click on the selector button
    // Then it should display the available language options
  });
  
  it('should change language when an option is selected', () => {
    // Given I have an open language selector
    // When I click on a language option
    // Then it should call the onLanguageChange handler with the correct code
  });
});
```

## Example Usage

### Basic Top Bar Setup

```tsx
// Example top bar configuration
const App = () => {
  // User profile props
  const userProfileProps: IUserProfileProps = {
    displayName: 'Jane Doe',
    email: 'jane.doe@example.com',
    avatarUrl: '/assets/avatars/jane.jpg',
    role: 'Admin',
    menuItems: [
      {
        label: 'Profile',
        icon: <UserIcon className="h-5 w-5" />,
        href: '/profile'
      },
      {
        label: 'Settings',
        icon: <CogIcon className="h-5 w-5" />,
        href: '/settings'
      },
      {
        label: 'Billing',
        icon: <CreditCardIcon className="h-5 w-5" />,
        href: '/billing'
      }
    ],
    onLogout: () => {
      // Handle logout
      console.log('Logging out...');
    }
  };
  
  // Notifications props
  const notificationProps: INotificationProps = {
    notifications: [
      {
        id: '1',
        title: 'New message',
        message: 'You have a new message from Alex',
        time: '5 minutes ago',
        isRead: false,
        type: 'info'
      },
      {
        id: '2',
        title: 'Account verified',
        message: 'Your account has been verified successfully',
        time: '1 hour ago',
        isRead: true,
        type: 'success'
      }
    ],
    unreadCount: 1,
    onMarkAsRead: (id) => {
      // Mark notification as read
      console.log(`Marking notification ${id} as read`);
    },
    onMarkAllAsRead: () => {
      // Mark all notifications as read
      console.log('Marking all notifications as read');
    }
  };
  
  // Language selector props
  const languageSelectorProps: ILanguageSelectorProps = {
    currentLanguage: 'en',
    languages: [
      { code: 'en', name: 'English', flag: '🇺🇸' },
      { code: 'es', name: 'Español', flag: '🇪🇸' },
      { code: 'fr', name: 'Français', flag: '🇫🇷' },
      { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
      { code: 'zh', name: '中文', flag: '🇨🇳' }
    ],
    onLanguageChange: (code) => {
      // Change language
      console.log(`Changing language to ${code}`);
    }
  };
  
  // Search props
  const searchProps: ISearchProps = {
    placeholder: 'Search...',
    onSearch: (query) => {
      // Handle search
      console.log(`Searching for: ${query}`);
    },
    suggestions: [
      { label: 'Dashboard', value: 'dashboard' },
      { label: 'Profile', value: 'profile' },
      { label: 'Settings', value: 'settings' }
    ]
  };
  
  // Navigation links
  const navigationLinks: INavigationLink[] = [
    {
      label: 'Dashboard',
      href: '/dashboard',
      isActive: true
    },
    {
      label: 'Projects',
      href: '/projects'
    },
    {
      label: 'Team',
      href: '/team'
    }
  ];
  
  return (
    <div>
      <TopBarContainer
        logo={<KAILogo />}
        showSearch={true}
        searchProps={searchProps}
        navigationLinks={navigationLinks}
        notificationProps={notificationProps}
        userProfileProps={userProfileProps}
        languageSelectorProps={languageSelectorProps}
        isFixed={true}
      />
      
      {/* Page content with appropriate padding for fixed header */}
      <main className="pt-16">
        {/* Page content */}
      </main>
    </div>
  );
};
```

### Responsive Top Bar with Mobile Menu

```tsx
// Example responsive implementation
const ResponsiveApp = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  // Toggle mobile menu
  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };
  
  // Close mobile menu
  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };
  
  return (
    <div>
      {/* Use the appropriate top bar based on screen size */}
      <div className="block md:hidden">
        <MobileTopBar
          logo={<KAILogo size="small" />}
          onMenuClick={toggleMobileMenu}
          userProfileProps={userProfileProps}
          notificationProps={notificationProps}
        />
        
        {/* Mobile slide-out menu */}
        <MobileMenu
          isOpen={isMobileMenuOpen}
          onClose={closeMobileMenu}
          navigationLinks={navigationLinks}
          userProfileProps={userProfileProps}
        />
      </div>
      
      {/* Desktop top bar */}
      <div className="hidden md:block">
        <TopBarContainer
          logo={<KAILogo />}
          showSearch={true}
          searchProps={searchProps}
          navigationLinks={navigationLinks}
          notificationProps={notificationProps}
          userProfileProps={userProfileProps}
          languageSelectorProps={languageSelectorProps}
        />
      </div>
      
      {/* Page content */}
      <main className="pt-16">
        {/* Page content */}
      </main>
    </div>
  );
};
```

## Conclusion

The KAI Top Bar provides a comprehensive, accessible, and responsive header solution for the application. By following SOLID principles and implementing a component-based architecture, it enables a consistent user experience while adapting to different screen sizes and user needs. 