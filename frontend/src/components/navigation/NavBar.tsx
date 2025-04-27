import React, { useState } from 'react';
import { 
  Box, 
  Flex, 
  Text, 
  IconButton, 
  Avatar, 
  Menu, 
  MenuButton, 
  MenuList, 
  MenuItem, 
  Link,
  useColorMode,
  useDisclosure,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  Stack,
  Button
} from '@chakra-ui/react';
import { FiMenu, FiX, FiUser, FiSettings, FiLogOut, FiMoon, FiSun } from 'react-icons/fi';

// NavBar item interface (ISP)
export interface NavItem {
  id: string;
  label: string;
  href: string;
  icon?: React.ReactElement;
}

// NavBar props interface (ISP)
export interface NavBarProps {
  title: string;
  logo?: React.ReactElement;
  navItems: NavItem[];
  userName?: string;
  userAvatar?: string;
  onLogout?: () => void;
}

// Component for individual navigation item (SRP)
const NavBarItem: React.FC<{ item: NavItem; isMobile?: boolean }> = ({ item, isMobile = false }) => {
  const { label, href, icon } = item;
  return (
    <Link 
      href={href}
      px={3}
      py={2}
      rounded={'md'}
      _hover={{
        textDecoration: 'none',
        bg: 'gray.200',
        _dark: { bg: 'gray.700' }
      }}
      display="flex"
      alignItems="center"
    >
      {icon && <Box mr={2}>{icon}</Box>}
      <Text>{label}</Text>
    </Link>
  );
};

// NavBar component (SRP)
export const NavBar: React.FC<NavBarProps> = ({ 
  title, 
  logo, 
  navItems, 
  userName, 
  userAvatar, 
  onLogout 
}) => {
  const { colorMode, toggleColorMode } = useColorMode();
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  // Mobile menu handling
  const [isMobileOpen, setMobileOpen] = useState(false);
  const handleMobileToggle = () => {
    if (isMobileOpen) {
      onClose();
    } else {
      onOpen();
    }
    setMobileOpen(!isMobileOpen);
  };

  return (
    <Box 
      as="nav" 
      bg="white" 
      _dark={{ bg: 'gray.800' }} 
      px={4} 
      shadow="md"
      position="sticky"
      top={0}
      zIndex={10}
    >
      <Flex h={16} alignItems={'center'} justifyContent={'space-between'}>
        {/* Logo and title */}
        <Flex alignItems="center">
          {logo && <Box mr={2}>{logo}</Box>}
          <Text fontSize="xl" fontWeight="bold">{title}</Text>
        </Flex>

        {/* Desktop navigation */}
        <Flex alignItems="center" display={{ base: 'none', md: 'flex' }}>
          {navItems.map((item) => (
            <NavBarItem key={item.id} item={item} />
          ))}
        </Flex>

        {/* Right side actions */}
        <Flex alignItems={'center'}>
          {/* Theme toggle */}
          <IconButton
            aria-label="Toggle color mode"
            icon={colorMode === 'light' ? <FiMoon /> : <FiSun />}
            onClick={toggleColorMode}
            variant="ghost"
            mr={2}
          />

          {/* User menu */}
          {userName && (
            <Menu>
              <MenuButton
                as={Button}
                variant="ghost"
                rounded={'full'}
                cursor={'pointer'}
              >
                <Flex alignItems="center">
                  <Avatar size={'sm'} src={userAvatar} mr={2} />
                  <Text display={{ base: 'none', md: 'block' }}>{userName}</Text>
                </Flex>
              </MenuButton>
              <MenuList>
                <MenuItem icon={<FiUser />}>Profile</MenuItem>
                <MenuItem icon={<FiSettings />}>Settings</MenuItem>
                {onLogout && (
                  <MenuItem icon={<FiLogOut />} onClick={onLogout}>Logout</MenuItem>
                )}
              </MenuList>
            </Menu>
          )}

          {/* Mobile menu button */}
          <IconButton
            display={{ base: 'flex', md: 'none' }}
            aria-label="Open menu"
            icon={isMobileOpen ? <FiX /> : <FiMenu />}
            onClick={handleMobileToggle}
            variant="ghost"
            ml={2}
          />
        </Flex>
      </Flex>

      {/* Mobile navigation drawer */}
      <Drawer isOpen={isOpen} placement="right" onClose={onClose}>
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader>{title}</DrawerHeader>
          <DrawerBody>
            <Stack spacing={4}>
              {navItems.map((item) => (
                <NavBarItem key={item.id} item={item} isMobile />
              ))}
            </Stack>
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Box>
  );
};

export default NavBar; 