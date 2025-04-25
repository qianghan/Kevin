/**
 * Mobile Navigation Components
 * 
 * Mobile-optimized navigation patterns including bottom bar and drawer navigation.
 * Follows single responsibility principle by focusing only on mobile navigation.
 */

import React, { useState } from 'react';
import {
  Box,
  Flex,
  IconButton,
  VStack,
  HStack,
  Text,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  useDisclosure,
  useColorModeValue,
  Icon,
  FlexProps,
  BoxProps,
} from '@chakra-ui/react';
import { useRouter } from 'next/router';
import Link from 'next/link';

/**
 * Navigation item data structure
 */
export interface NavItem {
  /** Unique identifier for the item */
  id: string;
  /** Display label */
  label: string;
  /** URL path */
  href: string;
  /** Icon component */
  icon: React.ElementType;
  /** Whether this item requires authentication */
  requiresAuth?: boolean;
  /** Whether the item should only be visible to specific roles */
  roles?: string[];
  /** Badge content to display (e.g., notification count) */
  badge?: string | number;
}

/**
 * Properties for mobile navigation components
 */
export interface MobileNavigationProps {
  /** Navigation items to display */
  items: NavItem[];
  /** Current path to determine active item */
  currentPath: string;
  /** Logo or brand element to display in drawer header */
  logo?: React.ReactNode;
  /** User data for conditional display */
  userData?: { isAuthenticated: boolean; role?: string };
  /** Custom color scheme */
  colorScheme?: string;
}

/**
 * Mobile bottom bar navigation
 * 
 * @example
 * ```tsx
 * <MobileBottomNav 
 *   items={navItems} 
 *   currentPath={router.asPath} 
 * />
 * ```
 */
export const MobileBottomNav: React.FC<MobileNavigationProps & BoxProps> = ({
  items,
  currentPath,
  userData,
  colorScheme = 'kai',
  ...rest
}) => {
  // Filter items based on authentication status and roles
  const filteredItems = items.filter(item => {
    if (item.requiresAuth && (!userData || !userData.isAuthenticated)) {
      return false;
    }
    if (item.roles?.length && (!userData?.role || !item.roles.includes(userData.role))) {
      return false;
    }
    return true;
  });

  // Show max 5 items in bottom nav
  const visibleItems = filteredItems.slice(0, 5);
  
  // Color values
  const bgColor = useColorModeValue('white', 'gray.800');
  const activeColor = useColorModeValue(`${colorScheme}.500`, `${colorScheme}.200`);
  const inactiveColor = useColorModeValue('gray.500', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Box
      position="fixed"
      bottom="0"
      left="0"
      right="0"
      bg={bgColor}
      boxShadow="0 -2px 10px rgba(0, 0, 0, 0.05)"
      borderTop="1px solid"
      borderColor={borderColor}
      zIndex="sticky"
      {...rest}
    >
      <HStack
        as="nav"
        justify="space-around"
        align="center"
        height="60px"
        px={2}
      >
        {visibleItems.map((item) => {
          const isActive = currentPath === item.href || currentPath.startsWith(`${item.href}/`);
          
          return (
            <Link key={item.id} href={item.href} passHref>
              <Box
                as="a"
                display="flex"
                flexDirection="column"
                alignItems="center"
                justifyContent="center"
                flex="1"
                py={2}
                position="relative"
                color={isActive ? activeColor : inactiveColor}
                _hover={{ color: activeColor }}
                transition="all 0.2s"
              >
                <Icon as={item.icon} boxSize={6} />
                <Text fontSize="xs" mt={1} fontWeight={isActive ? 'medium' : 'normal'}>
                  {item.label}
                </Text>
                
                {/* Indicator for active item */}
                {isActive && (
                  <Box
                    position="absolute"
                    bottom="-1px"
                    width="50%"
                    height="2px"
                    bg={activeColor}
                    borderRadius="full"
                  />
                )}
                
                {/* Badge indicator */}
                {item.badge && (
                  <Box
                    position="absolute"
                    top="0"
                    right="50%"
                    transform="translateX(8px)"
                    fontSize="xs"
                    bg={activeColor}
                    color="white"
                    borderRadius="full"
                    minWidth="18px"
                    height="18px"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    fontWeight="bold"
                  >
                    {item.badge}
                  </Box>
                )}
              </Box>
            </Link>
          );
        })}
      </HStack>
    </Box>
  );
};

/**
 * Slide-in drawer navigation for mobile
 * 
 * @example
 * ```tsx
 * <MobileDrawerNav 
 *   items={navItems} 
 *   currentPath={router.asPath}
 *   logo={<Logo />}
 * />
 * ```
 */
export const MobileDrawerNav: React.FC<MobileNavigationProps & FlexProps> = ({
  items,
  currentPath,
  logo,
  userData,
  colorScheme = 'kai',
  ...rest
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  // Filter items based on authentication status and roles
  const filteredItems = items.filter(item => {
    if (item.requiresAuth && (!userData || !userData.isAuthenticated)) {
      return false;
    }
    if (item.roles?.length && (!userData?.role || !item.roles.includes(userData.role))) {
      return false;
    }
    return true;
  });
  
  // Color values
  const bgColor = useColorModeValue('white', 'gray.800');
  const activeColor = useColorModeValue(`${colorScheme}.500`, `${colorScheme}.200`);
  const activeBgColor = useColorModeValue(`${colorScheme}.50`, `${colorScheme}.900`);
  const inactiveColor = useColorModeValue('gray.700', 'gray.300');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <>
      <Flex
        as="header"
        align="center"
        justify="space-between"
        padding={4}
        bg={bgColor}
        borderBottom="1px solid"
        borderColor={borderColor}
        width="100%"
        {...rest}
      >
        {logo}
        <IconButton
          aria-label="Open navigation menu"
          variant="ghost"
          icon={<HamburgerIcon />}
          onClick={onOpen}
        />
      </Flex>

      <Drawer
        isOpen={isOpen}
        placement="left"
        onClose={onClose}
        size="xs"
      >
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader borderBottomWidth="1px">
            {logo}
          </DrawerHeader>

          <DrawerBody p={0}>
            <VStack
              spacing={0}
              align="stretch"
              as="nav"
            >
              {filteredItems.map((item) => {
                const isActive = currentPath === item.href || currentPath.startsWith(`${item.href}/`);
                
                return (
                  <Link key={item.id} href={item.href} passHref>
                    <Box
                      as="a"
                      py={3}
                      px={4}
                      display="flex"
                      alignItems="center"
                      bg={isActive ? activeBgColor : 'transparent'}
                      color={isActive ? activeColor : inactiveColor}
                      fontWeight={isActive ? 'medium' : 'normal'}
                      borderLeft={isActive ? '4px solid' : '4px solid transparent'}
                      borderColor={isActive ? activeColor : 'transparent'}
                      _hover={{
                        bg: activeBgColor,
                        color: activeColor,
                      }}
                      onClick={onClose}
                      position="relative"
                    >
                      <Icon as={item.icon} boxSize={5} mr={3} />
                      <Text>{item.label}</Text>
                      
                      {/* Badge indicator */}
                      {item.badge && (
                        <Box
                          ml="auto"
                          bg={activeColor}
                          color="white"
                          borderRadius="full"
                          minWidth="20px"
                          height="20px"
                          display="flex"
                          alignItems="center"
                          justifyContent="center"
                          fontSize="xs"
                          fontWeight="bold"
                        >
                          {item.badge}
                        </Box>
                      )}
                    </Box>
                  </Link>
                );
              })}
            </VStack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </>
  );
};

/**
 * Combined mobile navigation with drawer and bottom bar
 * 
 * @example
 * ```tsx
 * <MobileNavigation 
 *   items={navItems} 
 *   currentPath={router.asPath}
 *   type="both"
 * />
 * ```
 */
export const MobileNavigation: React.FC<
  MobileNavigationProps & {
    /** Type of navigation to display */
    type?: 'drawer' | 'bottom' | 'both';
  }
> = ({
  items,
  currentPath,
  logo,
  userData,
  colorScheme = 'kai',
  type = 'bottom',
}) => {
  // If type is "both", show drawer for all items and bottom bar for primary items
  if (type === 'both') {
    // Items for bottom navigation (first 5 items only)
    const bottomItems = items.slice(0, 5);
    
    return (
      <>
        <MobileDrawerNav
          items={items}
          currentPath={currentPath}
          logo={logo}
          userData={userData}
          colorScheme={colorScheme}
        />
        <MobileBottomNav
          items={bottomItems}
          currentPath={currentPath}
          userData={userData}
          colorScheme={colorScheme}
          paddingBottom="env(safe-area-inset-bottom)"
        />
        <Box pb="60px" /> {/* Spacer for bottom navigation */}
      </>
    );
  }
  
  // Show just drawer or bottom navigation based on type
  return type === 'drawer' ? (
    <MobileDrawerNav
      items={items}
      currentPath={currentPath}
      logo={logo}
      userData={userData}
      colorScheme={colorScheme}
    />
  ) : (
    <>
      <MobileBottomNav
        items={items}
        currentPath={currentPath}
        userData={userData}
        colorScheme={colorScheme}
        paddingBottom="env(safe-area-inset-bottom)"
      />
      <Box pb="60px" /> {/* Spacer for bottom navigation */}
    </>
  );
};

// Basic hamburger icon for menu
const HamburgerIcon = () => (
  <Box>
    <Box as="span" display="block" width="24px" height="3px" bg="currentColor" mb="5px" />
    <Box as="span" display="block" width="24px" height="3px" bg="currentColor" mb="5px" />
    <Box as="span" display="block" width="24px" height="3px" bg="currentColor" />
  </Box>
); 