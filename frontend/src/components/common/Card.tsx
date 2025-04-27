import { Box, BoxProps, Heading, Text, Flex } from '@chakra-ui/react';
import { ReactNode } from 'react';

export interface CardProps extends BoxProps {
  title?: string;
  subtitle?: string;
  isHoverable?: boolean;
  isSelectable?: boolean;
  isSelected?: boolean;
  variant?: 'outline' | 'filled' | 'elevated';
  headerContent?: ReactNode;
  footerContent?: ReactNode;
}

/**
 * Card component with various style variants and optional header/footer
 */
export const Card = ({
  title,
  subtitle,
  children,
  isHoverable = false,
  isSelectable = false,
  isSelected = false,
  variant = 'outline',
  headerContent,
  footerContent,
  ...rest
}: CardProps) => {
  // Compute styles based on variant and states
  const getBgColor = () => {
    if (isSelected) return 'kai.50';
    if (variant === 'filled') return 'gray.50';
    return 'white';
  };
  
  const getShadow = () => {
    if (variant === 'elevated') return 'md';
    return 'none';
  };
  
  const getBorder = () => {
    if (variant === 'outline') return '1px solid';
    return 'none';
  };
  
  const getBorderColor = () => {
    if (isSelected) return 'kai.400';
    return 'gray.200';
  };
  
  return (
    <Box
      borderRadius="md"
      overflow="hidden"
      bg={getBgColor()}
      boxShadow={getShadow()}
      border={getBorder()}
      borderColor={getBorderColor()}
      transition="all 0.2s"
      _hover={{
        transform: isHoverable ? 'translateY(-2px)' : undefined,
        boxShadow: isHoverable ? 'lg' : getShadow(),
      }}
      _dark={{
        bg: variant === 'filled' ? 'gray.700' : 'gray.800',
        borderColor: isSelected ? 'kai.400' : 'gray.600',
      }}
      cursor={isSelectable ? 'pointer' : 'default'}
      {...rest}
    >
      {(title || subtitle || headerContent) && (
        <Box p={4} borderBottomWidth={(title || headerContent) && (children || footerContent) ? '1px' : 0}>
          {headerContent || (
            <>
              {title && (
                <Heading size="md" mb={subtitle ? 1 : 0}>
                  {title}
                </Heading>
              )}
              {subtitle && <Text color="gray.500">{subtitle}</Text>}
            </>
          )}
        </Box>
      )}
      
      {children && <Box p={4}>{children}</Box>}
      
      {footerContent && (
        <Box p={4} borderTopWidth="1px" borderTopColor="inherit">
          {footerContent}
        </Box>
      )}
    </Box>
  );
}; 