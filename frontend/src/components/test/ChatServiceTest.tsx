'use client';

import { useState, useEffect } from 'react';
import { Box, Button, Text, VStack, Heading, Code, Badge } from '@chakra-ui/react';
import { useChatService } from '../../hooks/useChatService';
import { ChatServiceStrategy } from '../../services/chat/ChatServiceFactory';
import axios from 'axios';

/**
 * Component to test the chat service integration
 */
export function ChatServiceTest() {
  const [strategy, setStrategy] = useState<ChatServiceStrategy>('auto');
  const [testResults, setTestResults] = useState<Array<{name: string, success: boolean, message: string}>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [apiHealth, setApiHealth] = useState<{status: string, timestamp: number} | null>(null);
  
  const chatService = useChatService(strategy);
  
  // Run tests when strategy changes
  useEffect(() => {
    if (chatService) {
      runTests();
    }
  }, [chatService]);
  
  // Check API health on load
  useEffect(() => {
    checkApiHealth();
  }, []);
  
  const checkApiHealth = async () => {
    try {
      const response = await axios.get('/api/health');
      setApiHealth(response.data);
    } catch (error: any) {
      console.error('Failed to check API health:', error);
      setApiHealth(null);
    }
  };
  
  const runTests = async () => {
    setIsLoading(true);
    setTestResults([]);
    
    try {
      // Test 0: Check API health
      await checkApiHealth();
      
      if (apiHealth) {
        addTestResult('API Health Check', true, `API is healthy: ${apiHealth.status}`);
      } else {
        addTestResult('API Health Check', false, 'API health check failed - backend may not be running');
      }
      
      // Test 1: Check service type
      let serviceName = '';
      
      if (typeof window !== 'undefined') {
        if ((window as any).KAI_UI?.services?.chat) {
          serviceName = 'Real UI Chat Service';
        } else {
          serviceName = 'Mock Chat Service (UI service not found)';
        }
      } else {
        serviceName = 'Server-side - cannot determine';
      }
      
      addTestResult('Service Type', true, `Using ${serviceName}`);
      
      // Test 2: Create a session
      try {
        const session = await chatService.createSession({
          name: 'Test Session'
        });
        
        addTestResult('Create Session', true, `Created session with ID: ${session.id}`);
        
        // Test 3: Send a message
        try {
          const updatedSession = await chatService.sendMessage(
            session.id,
            'This is a test message to verify integration',
            { enableThinkingSteps: true }
          );
          
          const messageCount = updatedSession.messages.length;
          const lastMessage = updatedSession.messages[messageCount - 1];
          
          addTestResult(
            'Send Message', 
            true, 
            `Message sent and received response: "${lastMessage.content.substring(0, 50)}..."`
          );
          
          // Test 4: Delete the session
          try {
            await chatService.deleteSession(session.id);
            addTestResult('Delete Session', true, `Successfully deleted session ${session.id}`);
          } catch (error: any) {
            addTestResult('Delete Session', false, `Error deleting session: ${error.message}`);
          }
        } catch (error: any) {
          addTestResult('Send Message', false, `Error sending message: ${error.message}`);
        }
      } catch (error: any) {
        addTestResult('Create Session', false, `Error creating session: ${error.message}`);
      }
    } catch (error: any) {
      addTestResult('Overall Test', false, `Error running tests: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  const addTestResult = (name: string, success: boolean, message: string) => {
    setTestResults(prev => [...prev, { name, success, message }]);
  };
  
  const changeStrategy = (newStrategy: ChatServiceStrategy) => {
    setStrategy(newStrategy);
  };
  
  return (
    <Box p={5} borderWidth="1px" borderRadius="lg" shadow="md">
      <Heading size="md" mb={4}>Chat Service Integration Test</Heading>
      
      <Box mb={5}>
        <Text fontWeight="bold" mb={2}>Current Strategy: <Code>{strategy}</Code></Text>
        <Button 
          size="sm" 
          colorScheme="blue" 
          onClick={() => changeStrategy('auto')} 
          mr={2}
          isDisabled={strategy === 'auto'}
        >
          Auto
        </Button>
        <Button 
          size="sm" 
          colorScheme="green" 
          onClick={() => changeStrategy('ui-adapter')} 
          mr={2}
          isDisabled={strategy === 'ui-adapter'}
        >
          UI Adapter
        </Button>
        <Button 
          size="sm" 
          colorScheme="yellow" 
          onClick={() => changeStrategy('mock')}
          isDisabled={strategy === 'mock'}
        >
          Mock
        </Button>
      </Box>
      
      <Button 
        colorScheme="teal" 
        onClick={runTests} 
        isLoading={isLoading}
        loadingText="Running Tests"
        mb={5}
      >
        Run Tests
      </Button>
      
      <VStack align="stretch" spacing={3}>
        {testResults.length === 0 && !isLoading && (
          <Text color="gray.500">No test results yet. Click "Run Tests" to start.</Text>
        )}
        
        {testResults.map((result, index) => (
          <Box 
            key={index} 
            p={3} 
            borderWidth="1px" 
            borderRadius="md" 
            borderColor={result.success ? 'green.200' : 'red.200'}
            bg={result.success ? 'green.50' : 'red.50'}
          >
            <Box display="flex" alignItems="center" mb={1}>
              <Text fontWeight="bold" mr={2}>{result.name}</Text>
              <Badge colorScheme={result.success ? 'green' : 'red'}>
                {result.success ? 'PASS' : 'FAIL'}
              </Badge>
            </Box>
            <Text fontSize="sm">{result.message}</Text>
          </Box>
        ))}
      </VStack>
    </Box>
  );
}

export default ChatServiceTest; 