/**
 * AIMessage Component
 * 
 * This component renders a message from the AI with appropriate styling
 * and support for thinking steps visualization.
 */

import React, { useState } from 'react';
import { 
  Box, 
  Flex, 
  Text, 
  Avatar, 
  IconButton, 
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Button,
  useColorModeValue,
  useClipboard
} from '@chakra-ui/react';
import { 
  FiMoreVertical, 
  FiCopy, 
  FiThumbsUp, 
  FiThumbsDown, 
  FiRefreshCw, 
  FiChevronDown, 
  FiChevronUp 
} from 'react-icons/fi';
import { AIMessageProps } from '../../interfaces/components/chat.components';
import { formatTimestamp } from '../../utils/date';
import ThinkingSteps from './ThinkingSteps';

/**
 * AIMessage Component
 * 
 * @param props - The component props
 * @returns A styled AI message component with thinking steps
 */
export const AIMessage: React.FC<AIMessageProps> = ({
  message,
  isLast = false,
  showTimestamp = true,
  showThinkingSteps = false,
  onFetchThinkingSteps,
  thinkingSteps,
  isThinkingStepsLoading = false,
  testId = 'ai-message',
  ...boxProps
}) => {
  // Theme colors
  const bgColor = useColorModeValue('gray.100', 'gray.700');
  const textColor = useColorModeValue('gray.800', 'white');
  const timeColor = useColorModeValue('gray.500', 'gray.400');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  
  // Local state
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(false);
  const { hasCopied, onCopy } = useClipboard(
    typeof message.content === 'string' ? message.content : ''
  );
  
  // Handle thinking steps toggle
  const handleToggleThinking = async () => {
    if (!isThinkingExpanded && showThinkingSteps && onFetchThinkingSteps && !thinkingSteps) {
      await onFetchThinkingSteps(message.id);
    }
    setIsThinkingExpanded(!isThinkingExpanded);
  };

  return (
    <Box
      data-testid={testId}
      mb={4}
      {...boxProps}
    >
      <Flex mb={1}>
        <Avatar 
          size="sm" 
          mr={2} 
          name="AI Assistant" 
          bg="purple.500"
          color="white"
        />
        
        <Box 
          maxWidth="80%"
          bg={bgColor}
          p={3}
          borderRadius="lg"
          borderWidth="1px"
          borderColor={borderColor}
        >
          {typeof message.content === 'string' ? (
            <Text color={textColor}>{message.content}</Text>
          ) : (
            message.content
          )}
        </Box>
      </Flex>
      
      <Flex pl={10} alignItems="center">
        {showTimestamp && message.timestamp && (
          <Text fontSize="xs" color={timeColor} mr={2}>
            {formatTimestamp(message.timestamp)}
          </Text>
        )}
        
        {/* Feedback buttons */}
        <IconButton
          icon={<FiThumbsUp />}
          size="xs"
          variant="ghost"
          aria-label="Thumbs up"
          mr={1}
        />
        
        <IconButton
          icon={<FiThumbsDown />}
          size="xs"
          variant="ghost"
          aria-label="Thumbs down"
          mr={1}
        />
        
        {/* Copy button */}
        <IconButton
          icon={<FiCopy />}
          size="xs"
          variant="ghost"
          aria-label={hasCopied ? "Copied" : "Copy"}
          onClick={() => typeof message.content === 'string' && onCopy()}
          mr={1}
        />
        
        {/* Regenerate button */}
        <IconButton
          icon={<FiRefreshCw />}
          size="xs"
          variant="ghost"
          aria-label="Regenerate"
          mr={1}
        />
        
        {/* Thinking steps toggle */}
        {showThinkingSteps && (
          <Button
            rightIcon={isThinkingExpanded ? <FiChevronUp /> : <FiChevronDown />}
            size="xs"
            variant="ghost"
            onClick={handleToggleThinking}
            ml={2}
          >
            Thinking Steps
          </Button>
        )}
      </Flex>
      
      {/* Thinking steps component */}
      {showThinkingSteps && isThinkingExpanded && (
        <Box mt={2} ml={10}>
          <ThinkingSteps
            steps={thinkingSteps || []}
            isLoading={isThinkingStepsLoading}
            isExpanded={isThinkingExpanded}
            onToggleExpand={() => setIsThinkingExpanded(!isThinkingExpanded)}
          />
        </Box>
      )}
    </Box>
  );
};

export default AIMessage; 