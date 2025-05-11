/**
 * ChatContainer Component
 * 
 * This component serves as the main container for chat-related UI.
 * It provides theme-consistent styling and layout for chat components.
 */

import React from 'react';
import { Box, useColorModeValue } from '@chakra-ui/react';
import { ChatContainerProps } from '../../interfaces/components/chat.components';

/**
 * ChatContainer Component
 * 
 * @param props - The component props
 * @returns A themed container for chat content
 */
export const ChatContainer: React.FC<ChatContainerProps> = ({
  children,
  isLoading = false,
  isFullHeight = true,
  testId = 'chat-container',
  ...boxProps
}) => {
  // Theme-consistent colors
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  return (
    <Box
      data-testid={testId}
      position="relative"
      bg={bgColor}
      borderRadius="md"
      borderWidth="1px"
      borderColor={borderColor}
      overflow="hidden"
      height={isFullHeight ? "100%" : "auto"}
      display="flex"
      flexDirection="column"
      boxShadow="sm"
      {...boxProps}
    >
      {/* Loading overlay */}
      {isLoading && (
        <Box
          position="absolute"
          top="0"
          left="0"
          right="0"
          bottom="0"
          bg="blackAlpha.50"
          zIndex="1"
          display="flex"
          alignItems="center"
          justifyContent="center"
        >
          <Box
            width="40px"
            height="40px"
            borderRadius="full"
            border="2px"
            borderColor="blue.500"
            borderBottomColor="transparent"
            animation="spin 1s linear infinite"
          />
        </Box>
      )}
      
      {/* Content */}
      {children}
    </Box>
  );
};

export default ChatContainer; 