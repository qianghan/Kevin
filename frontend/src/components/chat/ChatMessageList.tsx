/**
 * ChatMessageList Component
 * 
 * This component displays a list of chat messages with support for virtualization
 * to handle large conversations efficiently.
 */

import React, { useEffect, useRef } from 'react';
import { Box, VStack, Text, useColorModeValue } from '@chakra-ui/react';
import { ChatMessageListProps } from '../../interfaces/components/chat.components';
import AutoSizer from 'react-virtualized-auto-sizer';
import { VariableSizeList as List } from 'react-window';
import UserMessage from './UserMessage';
import AIMessage from './AIMessage';

/**
 * Calculates estimated height for a message based on content length
 */
const estimateMessageHeight = (content: string): number => {
  const baseHeight = 80; // Base height for avatar, timestamp, etc.
  const charsPerLine = 40; // Reduced from 60 to account for word wrapping
  const lineHeight = 24; // Height per line in pixels
  const maxHeight = 800; // Maximum height for a single message
  
  // Calculate lines based on content length and word wrapping
  const lines = Math.ceil(content.length / charsPerLine);
  const estimatedHeight = baseHeight + (lines * lineHeight);
  
  // Return the minimum of estimated height and max height
  return Math.min(estimatedHeight, maxHeight);
};

/**
 * ChatMessageList Component
 * 
 * @param props - The component props
 * @returns A virtualized list of chat messages
 */
export const ChatMessageList: React.FC<ChatMessageListProps> = ({
  messages = [],
  isLoading = false,
  showThinkingSteps = false,
  onFetchThinkingSteps,
  scrollBehavior = 'smooth',
  emptyStateMessage = 'No messages yet. Start a conversation!',
  isFullHeight = true,
  testId = 'chat-message-list',
  ...boxProps
}) => {
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const emptyTextColor = useColorModeValue('gray.500', 'gray.400');
  const listRef = useRef<List>(null);
  
  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > 0 && listRef.current) {
      listRef.current.scrollToItem(messages.length - 1);
    }
  }, [messages.length]);
  
  // Row renderer for the virtualized list
  const renderRow = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const message = messages[index];
    const isLast = index === messages.length - 1;
    
    return (
      <Box style={style} width="100%" px={4} overflow="hidden">
        {message.role === 'user' ? (
          <UserMessage
            message={message}
            isLast={isLast}
            showTimestamp={true}
          />
        ) : (
          <AIMessage
            message={message}
            isLast={isLast}
            showTimestamp={true}
            showThinkingSteps={showThinkingSteps}
            onFetchThinkingSteps={onFetchThinkingSteps}
          />
        )}
      </Box>
    );
  };
  
  // Get item size for the virtualized list
  const getItemSize = (index: number) => {
    const message = messages[index];
    return estimateMessageHeight(message.content as string);
  };
  
  return (
    <Box
      data-testid={testId}
      bg={bgColor}
      height={isFullHeight ? "100%" : "auto"}
      overflowY="auto"
      flex="1"
      position="relative"
      {...boxProps}
    >
      {messages.length === 0 ? (
        <Box
          height="100%"
          display="flex"
          alignItems="center"
          justifyContent="center"
          p={4}
        >
          <Text color={emptyTextColor}>{emptyStateMessage}</Text>
        </Box>
      ) : (
        <AutoSizer>
          {({ height, width }) => (
            <List
              ref={listRef}
              height={height}
              width={width}
              itemCount={messages.length}
              itemSize={getItemSize}
              overscanCount={5}
            >
              {renderRow}
            </List>
          )}
        </AutoSizer>
      )}
    </Box>
  );
};

export default ChatMessageList; 