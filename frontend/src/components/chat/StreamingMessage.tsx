/**
 * StreamingMessage Component
 * 
 * This component renders text that is being streamed, with optional
 * cursor blinking animation and typing indicator.
 */

import React, { useEffect, useState } from 'react';
import { Box, Text, keyframes, useColorModeValue } from '@chakra-ui/react';
import { StreamingMessageProps } from '../../interfaces/components/chat.components';

// Blinking cursor animation
const blink = keyframes`
  0% { opacity: 1; }
  50% { opacity: 0; }
  100% { opacity: 1; }
`;

/**
 * StreamingMessage Component
 * 
 * @param props - The component props
 * @returns A component that displays streaming text with animations
 */
export const StreamingMessage: React.FC<StreamingMessageProps> = ({
  content,
  isComplete = false,
  cursorBlinkSpeed = 530, // Default blink speed in ms
  typingIndicator = true,
  testId = 'streaming-message',
  ...boxProps
}) => {
  // Theme colors
  const textColor = useColorModeValue('gray.800', 'gray.100');
  const cursorColor = useColorModeValue('blue.500', 'blue.300');
  
  // Blinking animation style
  const blinkAnimation = `${blink} ${cursorBlinkSpeed}ms infinite`;
  
  return (
    <Box
      data-testid={testId}
      position="relative"
      {...boxProps}
    >
      <Text 
        color={textColor} 
        whiteSpace="pre-wrap"
        display="inline"
      >
        {content}
        
        {/* Blinking cursor when streaming is not complete */}
        {!isComplete && typingIndicator && (
          <Box
            as="span"
            display="inline-block"
            width="0.5em"
            height="1em"
            bg={cursorColor}
            ml="1px"
            animation={blinkAnimation}
            verticalAlign="middle"
          />
        )}
      </Text>
    </Box>
  );
};

export default StreamingMessage; 