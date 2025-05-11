/**
 * ChatInput Component
 * 
 * This component provides a rich input for chat messages with support
 * for attachments, options, and enhanced user experience.
 */

import React, { useState, useRef, KeyboardEvent } from 'react';
import { 
  Box, 
  Flex, 
  Textarea, 
  Button, 
  IconButton, 
  useColorModeValue,
  FormControl,
  Tooltip,
  HStack,
  Text,
  Menu,
  MenuButton,
  MenuList,
  MenuItem
} from '@chakra-ui/react';
import { 
  FiSend, 
  FiPaperclip, 
  FiX, 
  FiSettings 
} from 'react-icons/fi';
import { ChatInputProps } from '../../interfaces/components/chat.components';
import { Attachment } from '../../interfaces/services/chat.service';

/**
 * ChatInput Component
 * 
 * @param props - The component props
 * @returns A chat input component with attachment support
 */
export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onSendAttachments,
  isDisabled = false,
  isLoading = false,
  placeholder = "Type a message...",
  initialValue = "",
  supportedAttachmentTypes = [".txt", ".pdf", ".png", ".jpg", ".jpeg"],
  maxAttachmentSize = 10 * 1024 * 1024, // 10MB
  showOptionsMenu = false,
  availableOptions = {},
  testId = 'chat-input',
  ...boxProps
}) => {
  // State
  const [message, setMessage] = useState(initialValue);
  const [attachments, setAttachments] = useState<File[]>([]);
  const [selectedOptions, setSelectedOptions] = useState({});
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Theme colors
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  // Handle message submission
  const handleSubmit = async () => {
    if (!message.trim() && attachments.length === 0) return;
    
    if (attachments.length > 0 && onSendAttachments) {
      await onSendAttachments(message.trim(), attachments.map(fileToAttachment), selectedOptions);
    } else {
      await onSendMessage(message.trim(), selectedOptions);
    }
    
    // Reset state
    setMessage("");
    setAttachments([]);
  };
  
  // Convert File to Attachment type
  const fileToAttachment = (file: File): Attachment => {
    return {
      id: `attachment-${Date.now()}-${file.name}`,
      name: file.name,
      type: file.type,
      size: file.size,
      content: file
    };
  };
  
  // Handle enter key press (submit on Enter, new line on Shift+Enter)
  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };
  
  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    
    const newFiles = Array.from(e.target.files);
    // Filter by size and type
    const validFiles = newFiles.filter(file => {
      const validSize = file.size <= maxAttachmentSize;
      const validType = supportedAttachmentTypes.some(type => 
        file.name.toLowerCase().endsWith(type) || file.type.includes(type.replace('.', ''))
      );
      return validSize && validType;
    });
    
    setAttachments(prev => [...prev, ...validFiles]);
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };
  
  // Remove an attachment
  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <Box
      data-testid={testId}
      p={4}
      borderTopWidth="1px"
      borderTopColor={borderColor}
      bg={bgColor}
      {...boxProps}
    >
      {/* Attachments preview */}
      {attachments.length > 0 && (
        <Flex wrap="wrap" gap={2} mb={2}>
          {attachments.map((file, index) => (
            <Box
              key={`file-${index}`}
              bg={useColorModeValue('gray.100', 'gray.700')}
              borderRadius="md"
              py={1}
              px={2}
              display="flex"
              alignItems="center"
            >
              <Text fontSize="xs" noOfLines={1} maxWidth="150px">
                {file.name}
              </Text>
              <IconButton
                icon={<FiX />}
                aria-label="Remove file"
                size="xs"
                variant="ghost"
                ml={1}
                onClick={() => removeAttachment(index)}
              />
            </Box>
          ))}
        </Flex>
      )}
      
      {/* Input area */}
      <FormControl>
        <Flex>
          {/* File attachment button */}
          {onSendAttachments && (
            <>
              <input
                type="file"
                multiple
                ref={fileInputRef}
                style={{ display: 'none' }}
                onChange={handleFileSelect}
                accept={supportedAttachmentTypes.join(',')}
              />
              <Tooltip label="Attach files">
                <IconButton
                  icon={<FiPaperclip />}
                  aria-label="Attach files"
                  variant="ghost"
                  isDisabled={isDisabled || isLoading}
                  onClick={() => fileInputRef.current?.click()}
                  mr={2}
                />
              </Tooltip>
            </>
          )}
          
          {/* Text input */}
          <Textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder={placeholder}
            onKeyDown={handleKeyPress}
            minH="40px"
            maxH="200px"
            resize="none"
            py={2}
            pr={10}
            isDisabled={isDisabled || isLoading}
            variant="filled"
            borderRadius="md"
            _focus={{ borderColor: 'blue.500' }}
            flexGrow={1}
          />
          
          {/* Options menu */}
          {showOptionsMenu && (
            <Menu placement="top">
              <MenuButton
                as={IconButton}
                icon={<FiSettings />}
                aria-label="Chat options"
                variant="ghost"
                isDisabled={isDisabled || isLoading}
                ml={2}
              />
              <MenuList>
                {/* Render options based on availableOptions */}
                <MenuItem>Option 1</MenuItem>
                <MenuItem>Option 2</MenuItem>
              </MenuList>
            </Menu>
          )}
          
          {/* Send button */}
          <Button
            colorScheme="blue"
            isDisabled={isDisabled || isLoading || (!message.trim() && attachments.length === 0)}
            isLoading={isLoading}
            onClick={handleSubmit}
            ml={2}
            px={4}
            leftIcon={<FiSend />}
          >
            Send
          </Button>
        </Flex>
      </FormControl>
    </Box>
  );
};

export default ChatInput; 