import { Box, BoxProps } from '@chakra-ui/react';
import { ReactNode } from 'react';

interface ContainerProps extends BoxProps {
  children: ReactNode;
  maxPageWidth?: string | object;
}

/**
 * Responsive container component that centers content and applies consistent padding
 */
export const Container = ({ 
  children, 
  maxPageWidth = { base: '100%', md: '768px', lg: '1024px', xl: '1280px' },
  ...rest 
}: ContainerProps) => {
  return (
    <Box
      width="100%"
      maxWidth={maxPageWidth}
      mx="auto"
      px={{ base: '4', md: '6', lg: '8' }}
      {...rest}
    >
      {children}
    </Box>
  );
}; 