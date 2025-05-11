'use client';

import { Box, Heading, Text, Button, VStack, Code, Divider } from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import axios from 'axios';

export default function DebugPage() {
  const [apiResults, setApiResults] = useState<{[key: string]: any}>({});
  const [loading, setLoading] = useState<{[key: string]: boolean}>({});
  
  // Check if the UI service is registered globally
  const checkUIService = () => {
    if (typeof window !== 'undefined') {
      const hasUI = !!(window as any).KAI_UI;
      const hasServices = hasUI && !!(window as any).KAI_UI.services;
      const hasChatService = hasServices && !!(window as any).KAI_UI.services.chat;
      
      setApiResults(prev => ({
        ...prev,
        ui_service: {
          hasUI,
          hasServices,
          hasChatService
        }
      }));
    }
  };
  
  // Check API health at different endpoints
  const checkApiHealth = async (endpoint: string) => {
    setLoading(prev => ({ ...prev, [endpoint]: true }));
    try {
      const response = await axios.get(endpoint);
      setApiResults(prev => ({
        ...prev,
        [endpoint]: {
          status: 'success',
          data: response.data,
          statusCode: response.status
        }
      }));
    } catch (error: any) {
      setApiResults(prev => ({
        ...prev,
        [endpoint]: {
          status: 'error',
          message: error.message,
          statusCode: error.response?.status || 'unknown'
        }
      }));
    } finally {
      setLoading(prev => ({ ...prev, [endpoint]: false }));
    }
  };
  
  // Run checks automatically on page load
  useEffect(() => {
    checkUIService();
    checkApiHealth('/api/health');
    checkApiHealth('/api/chat/health');
    checkApiHealth('/api/chat/sessions');
  }, []);
  
  return (
    <Box p={5} maxWidth="1200px" margin="0 auto">
      <Heading mb={4}>Chat Service Debug</Heading>
      <Text mb={6}>
        This page helps diagnose why the chat service might be using simulated responses instead of connecting to the real backend.
      </Text>
      
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="md" mb={3}>UI Service Registration</Heading>
          <Button 
            colorScheme="blue" 
            onClick={checkUIService} 
            mb={3}
          >
            Check UI Service
          </Button>
          
          <Box p={4} borderWidth={1} borderRadius="md">
            <pre>{JSON.stringify(apiResults.ui_service || {}, null, 2)}</pre>
          </Box>
        </Box>
        
        <Divider />
        
        <Box>
          <Heading size="md" mb={3}>API Health Checks</Heading>
          <VStack spacing={4} align="stretch">
            {['/api/health', '/api/chat/health', '/api/chat/sessions'].map(endpoint => (
              <Box key={endpoint}>
                <Button 
                  colorScheme="teal" 
                  onClick={() => checkApiHealth(endpoint)} 
                  isLoading={loading[endpoint]}
                  mb={2}
                >
                  Check {endpoint}
                </Button>
                
                <Box p={4} borderWidth={1} borderRadius="md">
                  <Text fontWeight="bold" mb={2}>Endpoint: <Code>{endpoint}</Code></Text>
                  <pre>{JSON.stringify(apiResults[endpoint] || {}, null, 2)}</pre>
                </Box>
              </Box>
            ))}
          </VStack>
        </Box>
        
        <Divider />
        
        <Box>
          <Heading size="md" mb={3}>Manual API Endpoint Check</Heading>
          <Text mb={2}>Enter an API endpoint to check:</Text>
          <Box display="flex" mb={3}>
            <input 
              id="endpoint-input" 
              style={{ 
                padding: '8px',
                borderWidth: '1px',
                borderRadius: '4px',
                width: '100%',
                marginRight: '8px'
              }}
              defaultValue="/docs"
            />
            <Button 
              colorScheme="purple" 
              onClick={() => {
                const input = document.getElementById('endpoint-input') as HTMLInputElement;
                if (input && input.value) {
                  checkApiHealth(input.value);
                }
              }}
            >
              Check
            </Button>
          </Box>
        </Box>
      </VStack>
    </Box>
  );
} 