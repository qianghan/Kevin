'use client';

import { Box, Heading, Text } from '@chakra-ui/react';
import ChatServiceTest from '../../src/components/test/ChatServiceTest';

export default function TestPage() {
  return (
    <Box p={5} maxWidth="1200px" margin="0 auto">
      <Heading mb={4}>Chat Service Test</Heading>
      <Text mb={6}>
        This page tests the chat service integration between the frontend and backend.
        It verifies that real API connections are being made instead of using the mock service.
      </Text>
      
      <ChatServiceTest />
    </Box>
  );
} 