import { useState } from 'react';
import { Box, Container, Heading, Text, VStack, Flex, Link, Button, Input } from '@chakra-ui/react';
import NextLink from 'next/link';

// Simulate chat session data - same IDs as main chat for synchronization demo
const MOCK_SESSIONS = [
  { id: 'session1', title: 'Test Session' },
  { id: 'session2', title: 'Another Session' },
];

// Simulate chat messages
const MOCK_MESSAGES = [
  { id: 'msg1', type: 'user', content: 'Hello KAI', timestamp: new Date().toISOString() },
  { id: 'msg2', type: 'ai', content: 'Hello! How can I assist you today?', timestamp: new Date().toISOString() },
];

export default function LegacyUIChatPage() {
  const [isDarkTheme, setIsDarkTheme] = useState(false);
  const [sessions, setSessions] = useState(MOCK_SESSIONS);
  const [activeSession, setActiveSession] = useState(MOCK_SESSIONS[0]);
  const [messages, setMessages] = useState(MOCK_MESSAGES);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Handle sending a message
  const handleSendMessage = () => {
    if (!inputValue.trim()) return;
    
    // Add user message
    const userMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    };
    
    setMessages([...messages, userMessage]);
    setInputValue('');
    setIsLoading(true);
    
    // Simulate AI response after delay
    setTimeout(() => {
      const aiMessage = {
        id: `ai-${Date.now()}`,
        type: 'ai',
        content: `[Legacy UI] Response: "${inputValue}"`,
        timestamp: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    }, 1500);
  };
  
  return (
    <Box 
      className="ui-container" 
      bg={isDarkTheme ? 'gray.800' : 'white'} 
      color={isDarkTheme ? 'white' : 'gray.800'} 
      minH="100vh"
    >
      <Container maxW="container.xl" p={4}>
        <Flex 
          justify="space-between" 
          align="center" 
          py={4} 
          borderBottom="1px solid" 
          borderColor={isDarkTheme ? 'gray.700' : 'gray.200'}
          mb={6}
        >
          <Heading size="lg">KAI Legacy Chat</Heading>
          <Flex align="center" gap={4}>
            <Button 
              onClick={() => setIsDarkTheme(!isDarkTheme)}
              className="ui-theme-toggle"
            >
              Toggle Theme
            </Button>
            <NextLink href="/chat" passHref>
              <Link color="teal.500">Go to New Chat UI</Link>
            </NextLink>
          </Flex>
        </Flex>
        
        <Flex className={isDarkTheme ? 'ui-dark-theme' : 'ui-light-theme'} gap={4} h="calc(100vh - 150px)">
          {/* Session list */}
          <Box 
            w="250px" 
            borderWidth="1px" 
            borderRadius="md" 
            p={4} 
            bg={isDarkTheme ? 'gray.700' : 'gray.100'}
            overflowY="auto"
          >
            <Heading size="sm" mb={4}>Chat Sessions</Heading>
            
            {sessions.map(session => (
              <Box 
                key={session.id}
                p={3} 
                mb={2}
                borderRadius="md" 
                bg={activeSession.id === session.id ? 
                  (isDarkTheme ? 'teal.800' : 'teal.100') : 
                  (isDarkTheme ? 'gray.600' : 'white')}
                cursor="pointer"
                onClick={() => setActiveSession(session)}
                className="ui-chat-session"
                data-session-id={session.id}
              >
                <Text fontWeight={activeSession.id === session.id ? 'bold' : 'normal'}>
                  {session.title}
                </Text>
              </Box>
            ))}
          </Box>
          
          {/* Chat area */}
          <Flex 
            flex={1} 
            flexDir="column" 
            borderWidth="1px" 
            borderRadius="md" 
            bg={isDarkTheme ? 'gray.700' : 'white'}
            className="ui-chat-container"
          >
            {/* Chat header */}
            <Box p={4} borderBottomWidth="1px" borderColor={isDarkTheme ? 'gray.600' : 'gray.200'}>
              <Heading size="md">{activeSession.title} (Legacy UI)</Heading>
            </Box>
            
            {/* Messages */}
            <Box 
              flex={1} 
              p={4} 
              overflowY="auto"
              className="ui-chat-messages"
            >
              {messages.map(message => (
                <Box 
                  key={message.id}
                  mb={4}
                  p={3}
                  borderRadius="lg"
                  maxW="80%"
                  alignSelf={message.type === 'user' ? 'flex-end' : 'flex-start'}
                  ml={message.type === 'user' ? 'auto' : 0}
                  bg={message.type === 'user' ? 
                    (isDarkTheme ? 'blue.700' : 'blue.100') : 
                    (isDarkTheme ? 'gray.600' : 'gray.100')}
                  className={message.type === 'user' ? 'ui-user-message' : 'ui-ai-message'}
                >
                  <Text>{message.content}</Text>
                  <Text fontSize="xs" color={isDarkTheme ? 'gray.400' : 'gray.500'} mt={1}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </Text>
                </Box>
              ))}
              
              {isLoading && (
                <Box 
                  p={3} 
                  borderRadius="lg" 
                  bg={isDarkTheme ? 'gray.600' : 'gray.100'}
                >
                  <Text>AI is typing...</Text>
                </Box>
              )}
            </Box>
            
            {/* Input area */}
            <Flex 
              p={4} 
              borderTopWidth="1px" 
              borderColor={isDarkTheme ? 'gray.600' : 'gray.200'}
            >
              <Input
                flex={1}
                mr={2}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Type a message..."
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleSendMessage();
                  }
                }}
                bg={isDarkTheme ? 'gray.800' : 'white'}
                color={isDarkTheme ? 'white' : 'black'}
              />
              <Button
                onClick={handleSendMessage}
                colorScheme="teal"
                loading={isLoading}
              >
                Send
              </Button>
            </Flex>
          </Flex>
        </Flex>
      </Container>
    </Box>
  );
} 