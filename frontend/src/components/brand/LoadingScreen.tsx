import React from 'react';
import { Box, Flex, Text } from '@chakra-ui/react';
import Logo from './Logo';

export interface LoadingScreenProps {
  message?: string;
  fullScreen?: boolean;
}

// Define CSS class names for animations
const ANIMATION_CLASSES = {
  PULSE: 'kai-pulse-animation',
  SHIMMER: 'kai-shimmer-animation',
  ROTATE: 'kai-rotate-animation',
  ROTATE_REVERSE: 'kai-rotate-reverse-animation',
  DOT_1: 'kai-dot-animation-1',
  DOT_2: 'kai-dot-animation-2',
  DOT_3: 'kai-dot-animation-3',
};

/**
 * KAI Branded Loading Screen
 * 
 * Displays a loading screen with KAI brand elements and optional message.
 * - fullScreen: whether to take up the entire viewport
 * - message: optional loading message to display
 */
export const LoadingScreen: React.FC<LoadingScreenProps> = ({ 
  message = 'Loading...',
  fullScreen = false,
}) => {
  // Insert CSS animations into document head on component mount
  React.useEffect(() => {
    // Skip on server-side rendering
    if (typeof document === 'undefined') return;
    
    // Check if we already added the styles
    if (document.getElementById('kai-loading-styles')) return;
    
    // Create style element
    const styleEl = document.createElement('style');
    styleEl.id = 'kai-loading-styles';
    styleEl.innerHTML = `
      @keyframes kai-pulse {
        0% { opacity: 0.7; transform: scale(0.95); }
        70% { opacity: 1; transform: scale(1.05); }
        100% { opacity: 0.7; transform: scale(0.95); }
      }
      
      @keyframes kai-shimmer {
        0% { background-position: -1000px 0; }
        100% { background-position: 1000px 0; }
      }
      
      @keyframes kai-rotate {
        from { transform: translate(-50%, -50%) rotate(0deg); }
        to { transform: translate(-50%, -50%) rotate(360deg); }
      }
      
      .${ANIMATION_CLASSES.PULSE} {
        animation: kai-pulse 3s infinite ease-in-out;
      }
      
      .${ANIMATION_CLASSES.SHIMMER} {
        animation: kai-shimmer 2s infinite linear;
      }
      
      .${ANIMATION_CLASSES.ROTATE} {
        animation: kai-rotate 10s infinite linear;
      }
      
      .${ANIMATION_CLASSES.ROTATE_REVERSE} {
        animation: kai-rotate 7s infinite linear reverse;
      }
      
      .${ANIMATION_CLASSES.DOT_1} {
        animation: kai-pulse 1.5s 0s infinite ease-in-out;
      }
      
      .${ANIMATION_CLASSES.DOT_2} {
        animation: kai-pulse 1.5s 0.2s infinite ease-in-out;
      }
      
      .${ANIMATION_CLASSES.DOT_3} {
        animation: kai-pulse 1.5s 0.4s infinite ease-in-out;
      }
    `;
    
    // Append to document head
    document.head.appendChild(styleEl);
    
    // Cleanup on unmount
    return () => {
      // Only remove if no other loading screens are present
      if (!document.querySelectorAll('.kai-loading-screen').length) {
        document.head.removeChild(styleEl);
      }
    };
  }, []);
  
  return (
    <Flex
      className="kai-loading-screen"
      width={fullScreen ? '100vw' : '100%'}
      height={fullScreen ? '100vh' : '100%'}
      minHeight={fullScreen ? 'unset' : '300px'}
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      bg="background.dark"
      position="relative"
      overflow="hidden"
    >
      {/* Animated background elements */}
      <Box
        className={ANIMATION_CLASSES.ROTATE}
        position="absolute"
        width="600px"
        height="600px"
        bg="transparent"
        border="2px solid"
        borderColor="kai.900"
        borderRadius="full"
        top="50%"
        left="50%"
        opacity={0.07}
      />
      
      <Box
        className={ANIMATION_CLASSES.ROTATE_REVERSE}
        position="absolute"
        width="400px"
        height="400px"
        bg="transparent"
        border="2px solid"
        borderColor="kai.800"
        borderRadius="full"
        top="50%"
        left="50%"
        opacity={0.1}
      />
      
      {/* Shimmer effect */}
      <Box
        className={ANIMATION_CLASSES.SHIMMER}
        position="absolute"
        width="200%"
        height="100%"
        background="linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent)"
        backgroundSize="2000px 100%"
      />
      
      {/* Logo with pulse animation */}
      <Box
        className={ANIMATION_CLASSES.PULSE}
        mb={6}
      >
        <Logo size="xl" variant="mark" />
      </Box>
      
      {/* Loading text */}
      <Text
        fontSize="xl"
        fontWeight="light"
        color="white"
        letterSpacing="wider"
        opacity={0.9}
      >
        {message}
      </Text>
      
      {/* Loading indicator dots */}
      <Flex mt={2}>
        <Box
          width="8px"
          height="8px"
          borderRadius="full"
          bg="kai.400"
          mx={1}
          opacity={0.7}
          className={ANIMATION_CLASSES.DOT_1}
        />
        <Box
          width="8px"
          height="8px"
          borderRadius="full"
          bg="kai.400"
          mx={1}
          opacity={0.7}
          className={ANIMATION_CLASSES.DOT_2}
        />
        <Box
          width="8px"
          height="8px"
          borderRadius="full"
          bg="kai.400"
          mx={1}
          opacity={0.7}
          className={ANIMATION_CLASSES.DOT_3}
        />
      </Flex>
    </Flex>
  );
};

export default LoadingScreen; 