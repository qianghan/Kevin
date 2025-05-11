import { useState } from 'react';
import { Box, Container, Heading, Text, VStack, Flex, Link, Button } from '@chakra-ui/react';
import NextLink from 'next/link';

export default function LegacyUIPage() {
  const [isDarkTheme, setIsDarkTheme] = useState(false);
  
  return (
    <Box className="ui-container" bg={isDarkTheme ? 'gray.800' : 'white'} color={isDarkTheme ? 'white' : 'gray.800'} minH="100vh">
      <Container maxW="container.xl" p={4}>
        <Flex 
          justify="space-between" 
          align="center" 
          py={4} 
          borderBottom="1px solid" 
          borderColor={isDarkTheme ? 'gray.700' : 'gray.200'}
          mb={6}
        >
          <Heading size="lg">KAI Legacy UI</Heading>
          <Flex align="center" gap={4}>
            <Button 
              onClick={() => setIsDarkTheme(!isDarkTheme)}
              className="ui-theme-toggle"
            >
              Toggle Theme
            </Button>
            <Text mr={4}>Legacy UI View</Text>
            <NextLink href="/" passHref>
              <Link color="teal.500">Go to New UI</Link>
            </NextLink>
          </Flex>
        </Flex>
        
        <Box className={isDarkTheme ? 'ui-dark-theme' : 'ui-light-theme'}>
          <VStack spacing={6} align="start">
            <Box 
              p={6} 
              borderWidth="1px" 
              borderRadius="lg" 
              shadow="md" 
              bg={isDarkTheme ? 'gray.700' : 'white'}
              w="100%"
            >
              <Heading size="md" mb={4}>Welcome to Legacy UI</Heading>
              <Text>This simulates the legacy UI application. In a real implementation, this would be a separate application at /ui.</Text>
              
              <VStack mt={8} align="start">
                <NextLink href="/ui/chat" passHref>
                  <Link color="teal.500" fontWeight="bold">
                    Open Legacy Chat Interface →
                  </Link>
                </NextLink>
                
                <Text fontSize="sm" mt={4} color={isDarkTheme ? 'gray.400' : 'gray.600'}>
                  Current theme: {isDarkTheme ? 'Dark' : 'Light'}
                </Text>
              </VStack>
            </Box>
            
            <Box
              p={6}
              borderWidth="1px"
              borderRadius="lg"
              shadow="md"
              bg={isDarkTheme ? 'gray.700' : 'white'}
              w="100%"
            >
              <Heading size="md" mb={4}>Integration Testing</Heading>
              <Text mb={3}>
                This demo shows how the integrated testing environment works to test:
              </Text>
              <VStack align="start" spacing={2} pl={4}>
                <Text>• Chat session synchronization between UIs</Text>
                <Text>• Theme preference synchronization</Text>
                <Text>• Message handling across services</Text>
                <Text>• Component substitution during transition</Text>
              </VStack>
            </Box>
          </VStack>
        </Box>
      </Container>
    </Box>
  );
} 