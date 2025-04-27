import React from 'react';
import { Box, Container, Flex, Link, SimpleGrid, Text, Divider, HStack, Icon } from '@chakra-ui/react';
import Logo from './Logo';

export interface FooterLink {
  label: string;
  href: string;
  isExternal?: boolean;
}

export interface FooterLinkGroup {
  title: string;
  links: FooterLink[];
}

export interface SocialLink {
  label: string;
  href: string;
  icon: React.ReactElement;
}

export interface FooterProps {
  copyrightYear?: number;
  logoVariant?: 'full' | 'mark' | 'text';
  linkGroups?: FooterLinkGroup[];
  socialLinks?: SocialLink[];
  showLanguageSelector?: boolean;
}

/**
 * KAI Branded Footer Component
 * 
 * Displays a consistent footer across the application with brand elements,
 * navigation links, and copyright information.
 */
export const Footer: React.FC<FooterProps> = ({
  copyrightYear = new Date().getFullYear(),
  logoVariant = 'text',
  linkGroups = [],
  socialLinks = [],
  showLanguageSelector = false,
}) => {
  return (
    <Box as="footer" bg="background.dark" color="white" py={8}>
      <Container maxW="container.xl">
        <Flex 
          direction={{ base: 'column', md: 'row' }}
          justify="space-between"
          align={{ base: 'flex-start', md: 'center' }}
          mb={8}
        >
          {/* Logo section */}
          <Box mb={{ base: 6, md: 0 }}>
            <Logo variant={logoVariant} size="md" />
          </Box>
          
          {/* Social links */}
          {socialLinks.length > 0 && (
            <HStack spacing={4}>
              {socialLinks.map((link, index) => (
                <Link 
                  key={index}
                  href={link.href}
                  isExternal
                  aria-label={link.label}
                  color="gray.400"
                  _hover={{ color: 'kai.400' }}
                >
                  <Icon as={() => link.icon} boxSize={5} />
                </Link>
              ))}
            </HStack>
          )}
        </Flex>
        
        {/* Link groups */}
        {linkGroups.length > 0 && (
          <SimpleGrid 
            columns={{ base: 1, sm: 2, md: 4 }} 
            spacing={8}
            mb={12}
          >
            {linkGroups.map((group, index) => (
              <Box key={index}>
                <Text fontWeight="semibold" fontSize="sm" mb={4} color="kai.400">
                  {group.title}
                </Text>
                <Box as="ul" listStyleType="none" m={0} p={0}>
                  {group.links.map((link, linkIndex) => (
                    <Box as="li" mb={2} key={linkIndex}>
                      <Link
                        href={link.href}
                        isExternal={link.isExternal}
                        fontSize="sm"
                        color="gray.400"
                        _hover={{ color: 'white', textDecoration: 'none' }}
                      >
                        {link.label}
                      </Link>
                    </Box>
                  ))}
                </Box>
              </Box>
            ))}
          </SimpleGrid>
        )}
        
        <Divider borderColor="gray.700" mb={6} />
        
        {/* Bottom section */}
        <Flex 
          direction={{ base: 'column', md: 'row' }}
          justify="space-between"
          align={{ base: 'flex-start', md: 'center' }}
        >
          <Text fontSize="sm" color="gray.500">
            &copy; {copyrightYear} KAI. All rights reserved.
          </Text>
          
          <HStack 
            spacing={6} 
            mt={{ base: 4, md: 0 }}
            fontSize="sm" 
            color="gray.500"
          >
            <Link href="/privacy" _hover={{ color: 'white' }}>Privacy Policy</Link>
            <Link href="/terms" _hover={{ color: 'white' }}>Terms of Service</Link>
            {showLanguageSelector && (
              <Box>
                <Text as="span" cursor="pointer" _hover={{ color: 'white' }}>
                  English (US)
                </Text>
              </Box>
            )}
          </HStack>
        </Flex>
      </Container>
    </Box>
  );
};

export default Footer; 