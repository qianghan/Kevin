/**
 * UserMessage Component
 * 
 * This component renders a message from the user with appropriate styling
 * and interaction options.
 */

import React from 'react';
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
  useColorModeValue
} from '@chakra-ui/react';
import { FiMoreVertical, FiEdit, FiTrash } from 'react-icons/fi';
import { UserMessageProps } from '../../interfaces/components/chat.components';
import { formatTimestamp } from '../../utils/date';

/**
 * UserMessage Component
 * 
 * @param props - The component props
 * @returns A styled user message component
 */
export const UserMessage: React.FC<UserMessageProps> = ({
  message,
  isLast = false,
  showTimestamp = true,
  avatarUrl,
  testId = 'user-message',
  ...boxProps
}) => {
  // Theme colors
  const bgColor = useColorModeValue('blue.50', 'blue.900');
  const textColor = useColorModeValue('gray.800', 'white');
  const timeColor = useColorModeValue('gray.500', 'gray.400');
  const borderColor = useColorModeValue('blue.100', 'blue.800');

  return (
    <Box
      data-testid={testId}
      mb={4}
      {...boxProps}
    >
      <Flex justifyContent="flex-end" mb={1}>
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
        
        <Avatar 
          size="sm" 
          ml={2} 
          src={avatarUrl} 
          name="User" 
          bg="blue.500"
          color="white"
        />
      </Flex>
      
      {showTimestamp && message.timestamp && (
        <Flex justifyContent="flex-end" pr={10}>
          <Text fontSize="xs" color={timeColor}>
            {formatTimestamp(message.timestamp)}
          </Text>
          
          {/* Message actions menu */}
          <Menu placement="bottom-end">
            <MenuButton
              as={IconButton}
              icon={<FiMoreVertical />}
              variant="ghost"
              size="xs"
              ml={1}
              aria-label="Message options"
            />
            <MenuList>
              <MenuItem icon={<FiEdit />} onClick={() => {}}>
                Edit
              </MenuItem>
              <MenuItem icon={<FiTrash />} color="red.500" onClick={() => {}}>
                Delete
              </MenuItem>
            </MenuList>
          </Menu>
        </Flex>
      )}
    </Box>
  );
};

export default UserMessage; 