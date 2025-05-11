import { useState } from 'react';
import { Box, Container, Flex, Heading, Switch, Text, FormControl, FormLabel, Card, SimpleGrid, Button, useColorMode } from '@chakra-ui/react';

export default function Settings() {
  const { colorMode, toggleColorMode } = useColorMode();
  const [notifications, setNotifications] = useState(true);
  const [language, setLanguage] = useState('en');

  const isDarkMode = colorMode === 'dark';

  return (
    <Container maxW="container.md" py={8} className="settings-container">
      <Heading mb={6}>Settings</Heading>
      
      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
        <Card p={5} shadow="md" borderWidth="1px">
          <Heading size="md" mb={4}>Display</Heading>
          
          <FormControl display="flex" alignItems="center" mb={4}>
            <FormLabel htmlFor="dark-mode" mb="0">
              Dark Mode
            </FormLabel>
            <Switch 
              id="dark-mode" 
              className="theme-toggle"
              isChecked={isDarkMode}
              onChange={toggleColorMode}
              colorScheme="teal"
            />
          </FormControl>
          
          <Box mt={4} p={3} bg={isDarkMode ? 'gray.700' : 'gray.100'} borderRadius="md" className={isDarkMode ? 'dark-theme' : 'light-theme'}>
            <Text>Theme preview</Text>
          </Box>
        </Card>
        
        <Card p={5} shadow="md" borderWidth="1px">
          <Heading size="md" mb={4}>Notifications</Heading>
          
          <FormControl display="flex" alignItems="center" mb={4}>
            <FormLabel htmlFor="notifications" mb="0">
              Enable Notifications
            </FormLabel>
            <Switch 
              id="notifications" 
              isChecked={notifications}
              onChange={() => setNotifications(!notifications)}
              colorScheme="teal"
            />
          </FormControl>
        </Card>
        
        <Card p={5} shadow="md" borderWidth="1px">
          <Heading size="md" mb={4}>Language</Heading>
          
          <Flex gap={2} mt={4}>
            <Button 
              colorScheme={language === 'en' ? 'teal' : 'gray'}
              onClick={() => setLanguage('en')}
            >
              English
            </Button>
            <Button 
              colorScheme={language === 'fr' ? 'teal' : 'gray'}
              onClick={() => setLanguage('fr')}
            >
              Français
            </Button>
            <Button 
              colorScheme={language === 'zh' ? 'teal' : 'gray'}
              onClick={() => setLanguage('zh')}
            >
              中文
            </Button>
          </Flex>
        </Card>
        
        <Card p={5} shadow="md" borderWidth="1px">
          <Heading size="md" mb={4}>UI Version</Heading>
          
          <FormControl display="flex" alignItems="center" mb={4}>
            <FormLabel htmlFor="ui-version" mb="0">
              Use New UI Components
            </FormLabel>
            <Switch 
              id="ui-version" 
              defaultChecked
              colorScheme="teal"
            />
          </FormControl>
          
          <Text fontSize="sm" color="gray.500">
            Switches between legacy /ui components and new frontend components
          </Text>
        </Card>
      </SimpleGrid>
    </Container>
  );
} 