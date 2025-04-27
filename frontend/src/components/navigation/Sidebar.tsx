import React from 'react';
import {
  Box,
  Flex,
  Stack,
  Text,
  Icon,
  Divider,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Link,
  useColorModeValue,
} from '@chakra-ui/react';
import { FiHome, FiChevronRight } from 'react-icons/fi';

// Interface for navigation item (ISP)
export interface SidebarItem {
  id: string;
  label: string;
  href?: string;
  icon?: React.ReactElement;
  children?: SidebarItem[];
  onClick?: () => void;
}

// Interface for sidebar props (ISP)
export interface SidebarProps {
  items: SidebarItem[];
  title?: string;
  logo?: React.ReactElement;
  isCollapsible?: boolean;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  width?: string | number;
  collapsedWidth?: string | number;
}

// Component for simple navigation item (SRP)
const SidebarNavItem: React.FC<{ 
  item: SidebarItem;
  isActive?: boolean;
}> = ({ 
  item, 
  isActive = false 
}) => {
  const { label, href, icon, onClick } = item;
  
  const bg = useColorModeValue('gray.100', 'gray.700');
  const hoverBg = useColorModeValue('gray.200', 'gray.600');
  const activeBg = useColorModeValue('kai.50', 'kai.900');
  const activeColor = useColorModeValue('kai.600', 'kai.200');
  
  return (
    <Link
      href={href}
      onClick={onClick}
      textDecoration="none"
      _hover={{ textDecoration: 'none' }}
      width="100%"
    >
      <Flex
        align="center"
        p="3"
        mx="4"
        borderRadius="lg"
        role="group"
        cursor="pointer"
        _hover={{
          bg: hoverBg,
        }}
        bg={isActive ? activeBg : 'transparent'}
        color={isActive ? activeColor : 'inherit'}
      >
        {icon && (
          <Icon
            mr="4"
            fontSize="16"
            as={() => icon}
            color={isActive ? activeColor : 'inherit'}
          />
        )}
        <Text fontSize="sm" fontWeight={isActive ? 'bold' : 'medium'}>
          {label}
        </Text>
      </Flex>
    </Link>
  );
};

// Component for group of navigation items (SRP)
const SidebarNavGroup: React.FC<{ 
  item: SidebarItem;
  isActive?: boolean;
}> = ({ 
  item,
  isActive = false 
}) => {
  const { label, icon, children = [] } = item;
  
  const groupColor = useColorModeValue('gray.600', 'gray.300');
  
  return (
    <AccordionItem border="none">
      <AccordionButton
        p={3}
        _hover={{ bg: useColorModeValue('gray.100', 'gray.700') }}
        borderRadius="lg"
      >
        <Flex flex="1" align="center">
          {icon && <Icon as={() => icon} mr={4} />}
          <Text fontWeight="medium" fontSize="sm" color={groupColor}>
            {label}
          </Text>
        </Flex>
        <AccordionIcon />
      </AccordionButton>
      <AccordionPanel pb={4} pt={1} px={0}>
        {children.map((child) => (
          <SidebarNavItem
            key={child.id}
            item={child}
            isActive={isActive && child.id === 'activeChild'} // You'd compare with the actual active item
          />
        ))}
      </AccordionPanel>
    </AccordionItem>
  );
};

// Main sidebar component (SRP)
export const Sidebar: React.FC<SidebarProps> = ({
  items,
  title = 'Navigation',
  logo,
  isCollapsible = false,
  isCollapsed = false,
  onToggleCollapse,
  width = '250px',
  collapsedWidth = '70px',
}) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Box
      as="nav"
      pos="fixed"
      top="0"
      left="0"
      h="100vh"
      bg={bgColor}
      borderRight="1px"
      borderRightColor={borderColor}
      w={isCollapsed ? collapsedWidth : width}
      transition="width 0.3s ease"
      overflowX="hidden"
      overflowY="auto"
    >
      {/* Logo and title */}
      <Flex
        h="20"
        alignItems="center"
        justifyContent={isCollapsed ? 'center' : 'start'}
        px={isCollapsed ? 0 : 4}
      >
        {logo && (
          <Box mr={isCollapsed ? 0 : 2}>
            {logo}
          </Box>
        )}
        {!isCollapsed && (
          <Text fontSize="xl" fontWeight="bold">
            {title}
          </Text>
        )}
      </Flex>
      
      <Divider />
      
      {/* Navigation items */}
      <Stack spacing={1} py={3}>
        <Accordion allowMultiple defaultIndex={[0]}>
          {items.map((item) => (
            <React.Fragment key={item.id}>
              {item.children && item.children.length > 0 ? (
                <SidebarNavGroup item={item} />
              ) : (
                <SidebarNavItem item={item} />
              )}
            </React.Fragment>
          ))}
        </Accordion>
      </Stack>
    </Box>
  );
};

export default Sidebar; 