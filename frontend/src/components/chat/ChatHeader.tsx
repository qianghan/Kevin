/**
 * ChatHeader Component
 * 
 * This component displays the chat session title and provides
 * controls for managing the current chat session.
 */

import React from 'react';
import { 
  Box, 
  Flex, 
  Heading, 
  IconButton, 
  Menu, 
  MenuButton, 
  MenuItem, 
  MenuList,
  Tooltip,
  useColorModeValue
} from '@chakra-ui/react';
import { FiInfo, FiMoreVertical, FiSave, FiTrash2, FiEdit } from 'react-icons/fi';
import { ChatHeaderProps } from '../../interfaces/components/chat.components';

/**
 * ChatHeader Component
 * 
 * @param props - The component props
 * @returns A header for chat sessions with title and controls
 */
export const ChatHeader: React.FC<ChatHeaderProps> = ({
  title = 'New Chat',
  onInfoClick,
  onSaveClick,
  onDeleteClick,
  onRenameClick,
  menuItems = [],
  showControls = true,
  isEditable = true,
  testId = 'chat-header',
}) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  return (
    <Flex
      data-testid={testId}
      px={4}
      py={3}
      bg={bgColor}
      borderBottomWidth="1px"
      borderBottomColor={borderColor}
      justifyContent="space-between"
      alignItems="center"
    >
      <Heading size="md" fontWeight="medium" noOfLines={1} flex="1">
        {title || 'New Chat'}
      </Heading>
      
      {showControls && (
        <Flex gap={2}>
          {onInfoClick && (
            <Tooltip label="Session Info">
              <IconButton
                aria-label="Chat Info"
                icon={<FiInfo />}
                size="sm"
                variant="ghost"
                onClick={onInfoClick}
                data-testid="chat-info-button"
              />
            </Tooltip>
          )}
          
          <Menu placement="bottom-end">
            <MenuButton
              as={IconButton}
              aria-label="Chat Options"
              icon={<FiMoreVertical />}
              size="sm"
              variant="ghost"
              data-testid="chat-options-button"
            />
            <MenuList>
              {isEditable && onRenameClick && (
                <MenuItem 
                  icon={<FiEdit />} 
                  onClick={onRenameClick}
                  data-testid="rename-chat-option"
                >
                  Rename
                </MenuItem>
              )}
              
              {onSaveClick && (
                <MenuItem 
                  icon={<FiSave />} 
                  onClick={onSaveClick}
                  data-testid="save-chat-option"
                >
                  Save
                </MenuItem>
              )}
              
              {onDeleteClick && (
                <MenuItem 
                  icon={<FiTrash2 />} 
                  onClick={onDeleteClick}
                  color="red.500"
                  data-testid="delete-chat-option"
                >
                  Delete
                </MenuItem>
              )}
              
              {menuItems.map((item, index) => (
                <MenuItem
                  key={`menu-item-${index}`}
                  icon={item.icon}
                  onClick={item.onClick}
                  color={item.color}
                  data-testid={item.testId || `custom-option-${index}`}
                >
                  {item.label}
                </MenuItem>
              ))}
            </MenuList>
          </Menu>
        </Flex>
      )}
    </Flex>
  );
};

export default ChatHeader; 