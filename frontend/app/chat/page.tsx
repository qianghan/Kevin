'use client';

import { useState, useEffect } from 'react';
import { Box, Container, Heading, Text, VStack, useToast } from '@chakra-ui/react';
import ChatContainer from '../../src/components/chat/ChatContainer';
import ChatInput from '../../src/components/chat/ChatInput';
import ChatMessageList from '../../src/components/chat/ChatMessageList';
import ChatHeader from '../../src/components/chat/ChatHeader';
import { useChatService } from '../../src/hooks/useChatService';

export default function ChatPage() {
  // State for the current chat session
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Get toast for notifications
  const toast = useToast();
  
  // Get the chat service - try the real service first
  const chatService = useChatService('auto');
  
  // Create a new session on component mount
  useEffect(() => {
    async function createInitialSession() {
      if (!chatService) return;
      
      try {
        setLoading(true);
        console.log('Creating initial chat session...');
        const session = await chatService.createSession({
          name: 'New Conversation',
          initialQuery: 'Hello, I want to learn about Canadian universities.'
        });
        
        setSessionId(session.id);
        setMessages(session.messages || []);
        
        // Log success for debugging
        console.log('Session created:', session.id);
        console.log('Using service type:', chatService.constructor.name);
      } catch (err: any) {
        console.error('Failed to create session:', err);
        setError('Failed to create chat session: ' + (err.message || 'Unknown error'));
        toast({
          title: 'Error',
          description: 'Failed to start a new chat session. Please try again.',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      } finally {
        setLoading(false);
      }
    }
    
    if (chatService && !sessionId) {
      createInitialSession();
    }
  }, [chatService, sessionId, toast]);
  
  // Handle sending a message
  const handleSendMessage = async (message: string, options: any = {}) => {
    if (!chatService || !sessionId || !message.trim()) return;
    
    try {
      setLoading(true);
      
      // Add the user message immediately for better UX
      setMessages(prev => [...prev, {
        role: 'user',
        content: message
      }]);
      
      // Send the message to the API
      const updatedSession = await chatService.sendMessage(
        sessionId,
        message,
        {
          enableThinkingSteps: true,
          useWebSearch: true,
          ...options
        }
      );
      
      // Update messages with the response
      setMessages(updatedSession.messages || []);
      
      console.log('Message sent and response received');
    } catch (err: any) {
      console.error('Failed to send message:', err);
      setError('Failed to send message: ' + (err.message || 'Unknown error'));
      toast({
        title: 'Error',
        description: 'Failed to send your message. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Container maxW="container.lg" height="calc(100vh - 80px)" py={4}>
      <VStack height="100%" spacing={0}>
        <Heading mb={4}>Chat with Kevin</Heading>
        
        {error && (
          <Text color="red.500" mb={4}>
            {error}
          </Text>
        )}
        
        <Box width="100%" height="100%" borderRadius="md" overflow="hidden">
          <ChatContainer isFullHeight>
            <ChatHeader
              title="Kevin - University Assistant"
              subtitle="Ask anything about Canadian universities"
            />
            
            <ChatMessageList
              messages={messages}
              isLoading={loading}
              showTypingIndicator={loading}
            />
            
            <ChatInput
              onSendMessage={handleSendMessage}
              isDisabled={!chatService || loading}
              isLoading={loading}
              placeholder="Type your question about Canadian universities..."
              showOptionsMenu={true}
              availableOptions={{
                useWebSearch: true,
                enableThinkingSteps: true
              }}
            />
          </ChatContainer>
        </Box>
      </VStack>
    </Container>
  );
} 