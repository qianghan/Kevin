import React, { useState, ReactNode } from 'react';
import { Box, Flex, useMediaQuery } from '@chakra-ui/react';
import { FiHome, FiUsers, FiSettings, FiMessageSquare } from 'react-icons/fi';
import NavBar from '../navigation/NavBar';
import Sidebar, { SidebarItem } from '../navigation/Sidebar';

// Define props interface (ISP)
interface MainLayoutProps {
  children: ReactNode;
  title?: string;
  userName?: string;
  userAvatar?: string;
  onLogout?: () => void;
  sidebarItems?: SidebarItem[];
  showSidebar?: boolean;
}

// Default navigation items
const defaultNavItems = [
  {
    id: 'home',
    label: 'Home',
    href: '/',
    icon: <FiHome />,
  },
  {
    id: 'users',
    label: 'Users',
    href: '/users',
    icon: <FiUsers />,
  },
  {
    id: 'messages',
    label: 'Messages',
    href: '/messages',
    icon: <FiMessageSquare />,
  },
  {
    id: 'settings',
    label: 'Settings',
    href: '/settings',
    icon: <FiSettings />,
  },
];

// Default sidebar items
const defaultSidebarItems = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    href: '/dashboard',
    icon: <FiHome />,
  },
  {
    id: 'users',
    label: 'User Management',
    icon: <FiUsers />,
    children: [
      {
        id: 'user-list',
        label: 'User List',
        href: '/users',
      },
      {
        id: 'user-roles',
        label: 'User Roles',
        href: '/users/roles',
      },
    ],
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: <FiSettings />,
    children: [
      {
        id: 'account',
        label: 'Account Settings',
        href: '/settings/account',
      },
      {
        id: 'system',
        label: 'System Settings',
        href: '/settings/system',
      },
    ],
  },
];

// Main layout component (SRP)
export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  title = 'KAI Application',
  userName,
  userAvatar,
  onLogout,
  sidebarItems = defaultSidebarItems,
  showSidebar = true,
}) => {
  // Responsive design - detect mobile view
  const [isMobile] = useMediaQuery('(max-width: 768px)');
  
  // Sidebar collapsed state
  const [isSidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  // Toggle sidebar collapsed state
  const toggleSidebar = () => {
    setSidebarCollapsed(!isSidebarCollapsed);
  };
  
  // Calculate main content margin based on sidebar visibility
  const getMainContentMargin = () => {
    if (!showSidebar) return '0';
    if (isMobile) return '0';
    if (isSidebarCollapsed) return '70px'; // Collapsed width
    return '250px'; // Expanded width
  };
  
  return (
    <Flex direction="column" h="100vh" overflow="hidden">
      {/* Top navigation bar */}
      <NavBar
        title={title}
        navItems={defaultNavItems}
        userName={userName}
        userAvatar={userAvatar}
        onLogout={onLogout}
      />
      
      <Flex flex="1" overflow="hidden">
        {/* Sidebar - show only if specified */}
        {showSidebar && (
          <Sidebar
            items={sidebarItems}
            isCollapsible={!isMobile}
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={toggleSidebar}
          />
        )}
        
        {/* Main content area */}
        <Box
          as="main"
          flex="1"
          ml={getMainContentMargin()}
          transition="margin-left 0.3s ease"
          p={4}
          overflowY="auto"
        >
          {children}
        </Box>
      </Flex>
    </Flex>
  );
};

export default MainLayout; 