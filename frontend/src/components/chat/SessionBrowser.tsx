/**
 * SessionBrowser Component
 * 
 * This component provides a UI for browsing, searching, and managing chat sessions.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Input,
  InputGroup,
  InputLeftElement,
  Button,
  IconButton,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  Divider,
  Flex,
  Badge,
  useColorModeValue,
  Spinner,
  Tooltip
} from '@chakra-ui/react';
import {
  FiSearch,
  FiPlus,
  FiFilter,
  FiStar,
  FiMoreVertical,
  FiEdit,
  FiTrash2,
  FiDownload,
  FiX,
  FiTag
} from 'react-icons/fi';
import { useSessionContext } from '../../contexts/SessionContext';
import { ChatSession, ExportFormat } from '../../interfaces/services/chat.session';
import { formatTimestamp } from '../../utils/date';

/**
 * SessionBrowser Component Props
 */
interface SessionBrowserProps {
  onSessionSelect?: (sessionId: string) => void;
  onCreateSession?: () => void;
  testId?: string;
}

/**
 * SessionBrowser Component
 * 
 * @param props - The component props
 * @returns A browser interface for managing chat sessions
 */
export const SessionBrowser: React.FC<SessionBrowserProps> = ({
  onSessionSelect,
  onCreateSession,
  testId = 'session-browser'
}) => {
  // Colors
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const hoverBgColor = useColorModeValue('gray.50', 'gray.700');
  const activeBgColor = useColorModeValue('blue.50', 'blue.900');
  const textColor = useColorModeValue('gray.800', 'gray.100');
  const secondaryTextColor = useColorModeValue('gray.600', 'gray.400');
  
  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredSessions, setFilteredSessions] = useState<ChatSession[]>([]);
  const [starredOnly, setStarredOnly] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  
  // Get session context
  const {
    sessions,
    currentSession,
    isLoading,
    error,
    createSession,
    selectSession,
    updateSession,
    deleteSession,
    exportSession,
    searchSessions,
    refreshSessions
  } = useSessionContext();
  
  // Filter sessions when search query or starred filter changes
  useEffect(() => {
    const applyFilters = async () => {
      if (searchQuery.trim()) {
        setIsSearching(true);
        try {
          const results = await searchSessions(searchQuery);
          const filtered = starredOnly ? results.filter(s => s.starred) : results;
          setFilteredSessions(filtered);
        } catch (err) {
          console.error('Error searching sessions:', err);
          // Fall back to client-side filtering on error
          const filtered = sessions.filter(session => 
            session.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
            (!starredOnly || session.starred)
          );
          setFilteredSessions(filtered);
        } finally {
          setIsSearching(false);
        }
      } else {
        // No search query, just apply starred filter
        const filtered = starredOnly ? sessions.filter(s => s.starred) : sessions;
        setFilteredSessions(filtered);
      }
    };
    
    applyFilters();
  }, [searchQuery, starredOnly, sessions, searchSessions]);
  
  // Handle session creation
  const handleCreateSession = async () => {
    try {
      const newSession = await createSession('New Chat');
      
      if (onSessionSelect) {
        onSessionSelect(newSession.id);
      }
      
      if (onCreateSession) {
        onCreateSession();
      }
    } catch (err) {
      console.error('Error creating session:', err);
    }
  };
  
  // Handle session selection
  const handleSelectSession = async (sessionId: string) => {
    try {
      await selectSession(sessionId);
      
      if (onSessionSelect) {
        onSessionSelect(sessionId);
      }
    } catch (err) {
      console.error('Error selecting session:', err);
    }
  };
  
  // Handle session starring/unstarring
  const handleToggleStar = async (sessionId: string, isStarred: boolean) => {
    try {
      await updateSession(sessionId, { starred: !isStarred });
    } catch (err) {
      console.error('Error toggling star:', err);
    }
  };
  
  // Handle session renaming
  const handleRenameSession = async (sessionId: string, currentName: string) => {
    const newName = window.prompt('Enter a new name for this chat:', currentName);
    
    if (newName && newName !== currentName) {
      try {
        await updateSession(sessionId, { name: newName });
      } catch (err) {
        console.error('Error renaming session:', err);
      }
    }
  };
  
  // Handle session deletion
  const handleDeleteSession = async (sessionId: string) => {
    if (window.confirm('Are you sure you want to delete this chat? This action cannot be undone.')) {
      try {
        await deleteSession(sessionId);
      } catch (err) {
        console.error('Error deleting session:', err);
      }
    }
  };
  
  // Handle session export
  const handleExportSession = async (sessionId: string, format: ExportFormat) => {
    try {
      const result = await exportSession(sessionId, format);
      
      // Create a download link for the exported data
      const blob = result.data instanceof Blob 
        ? result.data 
        : new Blob([result.data as string], { type: result.mimeType });
      
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting session:', err);
    }
  };
  
  // Render session list
  const renderSessions = () => {
    const sessionsToRender = filteredSessions.length > 0 ? filteredSessions : sessions;
    
    if (isLoading) {
      return (
        <Flex justify="center" align="center" height="200px">
          <Spinner size="lg" color="blue.500" />
        </Flex>
      );
    }
    
    if (error) {
      return (
        <Flex 
          direction="column" 
          justify="center" 
          align="center" 
          height="200px"
          p={4}
          textAlign="center"
        >
          <Text color="red.500" mb={2}>Error loading sessions</Text>
          <Text fontSize="sm" color={secondaryTextColor}>{error.message}</Text>
          <Button 
            mt={4} 
            size="sm" 
            onClick={() => refreshSessions()}
          >
            Try Again
          </Button>
        </Flex>
      );
    }
    
    if (sessionsToRender.length === 0) {
      return (
        <Flex 
          direction="column" 
          justify="center" 
          align="center" 
          height="200px"
          p={4}
          textAlign="center"
        >
          <Text color={secondaryTextColor}>
            {searchQuery 
              ? 'No sessions found matching your search'
              : 'No chat sessions yet'}
          </Text>
          {searchQuery && (
            <Button 
              mt={4} 
              size="sm" 
              leftIcon={<FiX />}
              onClick={() => setSearchQuery('')}
            >
              Clear Search
            </Button>
          )}
        </Flex>
      );
    }
    
    return (
      <VStack spacing={1} align="stretch">
        {sessionsToRender.map(session => (
          <Box
            key={session.id}
            p={3}
            borderRadius="md"
            cursor="pointer"
            onClick={() => handleSelectSession(session.id)}
            bg={currentSession?.id === session.id ? activeBgColor : bgColor}
            _hover={{ bg: currentSession?.id !== session.id ? hoverBgColor : activeBgColor }}
            borderWidth="1px"
            borderColor={currentSession?.id === session.id ? 'blue.400' : borderColor}
            data-testid={`session-item-${session.id}`}
          >
            <Flex justify="space-between" align="flex-start">
              <VStack align="flex-start" spacing={1} flex={1}>
                <Text 
                  fontWeight={currentSession?.id === session.id ? 'semibold' : 'normal'}
                  color={textColor}
                  noOfLines={1}
                >
                  {session.name}
                </Text>
                
                {session.preview && (
                  <Text 
                    fontSize="xs" 
                    color={secondaryTextColor} 
                    noOfLines={1}
                  >
                    {session.preview}
                  </Text>
                )}
                
                <HStack spacing={2} mt={1}>
                  <Text fontSize="xs" color={secondaryTextColor}>
                    {formatTimestamp(session.updatedAt)}
                  </Text>
                  
                  {session.tags && session.tags.length > 0 && (
                    session.tags.slice(0, 2).map(tag => (
                      <Badge 
                        key={tag} 
                        colorScheme="blue" 
                        variant="subtle" 
                        fontSize="xs"
                      >
                        {tag}
                      </Badge>
                    ))
                  )}
                  
                  {session.tags && session.tags.length > 2 && (
                    <Badge colorScheme="gray" variant="subtle" fontSize="xs">
                      +{session.tags.length - 2}
                    </Badge>
                  )}
                </HStack>
              </VStack>
              
              <HStack>
                <IconButton
                  aria-label={session.starred ? "Unstar session" : "Star session"}
                  icon={<FiStar />}
                  size="sm"
                  variant="ghost"
                  color={session.starred ? "yellow.400" : "gray.400"}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleToggleStar(session.id, !!session.starred);
                  }}
                />
                
                <Menu>
                  <MenuButton
                    as={IconButton}
                    aria-label="Session options"
                    icon={<FiMoreVertical />}
                    size="sm"
                    variant="ghost"
                    onClick={(e) => e.stopPropagation()}
                  />
                  <MenuList onClick={(e) => e.stopPropagation()}>
                    <MenuItem 
                      icon={<FiEdit />} 
                      onClick={() => handleRenameSession(session.id, session.name)}
                    >
                      Rename
                    </MenuItem>
                    <MenuItem 
                      icon={<FiDownload />} 
                      onClick={() => handleExportSession(session.id, 'json')}
                    >
                      Export as JSON
                    </MenuItem>
                    <MenuItem 
                      icon={<FiDownload />} 
                      onClick={() => handleExportSession(session.id, 'markdown')}
                    >
                      Export as Markdown
                    </MenuItem>
                    <MenuItem 
                      icon={<FiTag />} 
                      onClick={() => {/* Tag management would go here */}}
                    >
                      Manage Tags
                    </MenuItem>
                    <Divider />
                    <MenuItem 
                      icon={<FiTrash2 />} 
                      color="red.500"
                      onClick={() => handleDeleteSession(session.id)}
                    >
                      Delete
                    </MenuItem>
                  </MenuList>
                </Menu>
              </HStack>
            </Flex>
          </Box>
        ))}
      </VStack>
    );
  };
  
  return (
    <Box
      data-testid={testId}
      height="100%"
      display="flex"
      flexDirection="column"
      bg={bgColor}
      borderRightWidth="1px"
      borderRightColor={borderColor}
    >
      {/* Header */}
      <Box p={4} borderBottomWidth="1px" borderBottomColor={borderColor}>
        <Flex justify="space-between" align="center" mb={4}>
          <Text fontWeight="semibold" fontSize="lg">Chat Sessions</Text>
          <Tooltip label="Create new chat">
            <IconButton
              aria-label="New chat"
              icon={<FiPlus />}
              onClick={handleCreateSession}
              colorScheme="blue"
              size="sm"
              data-testid="new-session-button"
            />
          </Tooltip>
        </Flex>
        
        {/* Search */}
        <InputGroup size="md">
          <InputLeftElement pointerEvents="none">
            {isSearching ? <Spinner size="sm" /> : <FiSearch color="gray.300" />}
          </InputLeftElement>
          <Input
            placeholder="Search chats..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            bg={useColorModeValue('gray.50', 'gray.700')}
            data-testid="session-search-input"
          />
        </InputGroup>
        
        {/* Filters */}
        <HStack mt={2} spacing={2}>
          <Button
            size="xs"
            leftIcon={<FiStar />}
            variant={starredOnly ? "solid" : "outline"}
            colorScheme={starredOnly ? "yellow" : "gray"}
            onClick={() => setStarredOnly(!starredOnly)}
            data-testid="starred-filter-button"
          >
            Starred
          </Button>
          <Button
            size="xs"
            leftIcon={<FiFilter />}
            variant="outline"
            onClick={() => {/* Additional filters would go here */}}
          >
            Filter
          </Button>
        </HStack>
      </Box>
      
      {/* Session List */}
      <Box p={2} flex="1" overflowY="auto">
        {renderSessions()}
      </Box>
    </Box>
  );
};

export default SessionBrowser; 