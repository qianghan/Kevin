/**
 * Chat Service Hook
 * 
 * This hook provides access to the chat service and ensures it's properly initialized.
 */

import { useState, useEffect } from 'react';
import { getChatService, ChatServiceStrategy } from '../services/chat/ChatServiceFactory';
import { IChatService } from '../interfaces/services/chat.service';
import { loadUIChatService } from '../services/chat/ui-chat-service-utils';
import { initializeUIChatService } from '../services/chat/initialize-ui-service';

/**
 * Hook to access the chat service
 * @param strategy The strategy to use for creating the service
 * @returns The chat service instance
 */
export function useChatService(strategy: ChatServiceStrategy = 'auto'): IChatService | null {
  const [service, setService] = useState<IChatService | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function initializeService() {
      try {
        // Always check if we have a UI service first
        let uiService = null;
        
        if (typeof window !== 'undefined') {
          uiService = loadUIChatService();
          
          // If strategy is 'ui-adapter' but no UI service exists, try to initialize it
          if (!uiService && strategy === 'ui-adapter') {
            console.log('UI service not found but requested, attempting to initialize...');
            uiService = initializeUIChatService();
          }
          
          // If strategy is 'auto' and no UI service exists, try to initialize it
          if (!uiService && strategy === 'auto') {
            console.log('No UI service found with auto strategy, attempting to initialize...');
            try {
              uiService = initializeUIChatService();
              console.log('Successfully initialized UI service');
            } catch (initError) {
              console.warn('Failed to initialize UI service, will use factory fallback:', initError);
            }
          }
        }
        
        // If we have a UI service by now and the strategy is compatible, we're done
        if (uiService && (strategy === 'ui-adapter' || strategy === 'auto')) {
          console.log('Using UI-based chat service');
          setService(getChatService('ui-adapter'));
          return;
        }
        
        // Otherwise use the factory
        console.log(`Creating chat service with strategy: ${strategy}`);
        const chatService = getChatService(strategy);
        setService(chatService);
      } catch (error) {
        console.error('Error initializing chat service:', error);
        setError(error instanceof Error ? error : new Error(String(error)));
        
        // Fallback to mock service if something went wrong
        if (strategy !== 'mock') {
          console.warn('Falling back to mock service due to initialization error');
          try {
            const mockService = getChatService('mock');
            setService(mockService);
          } catch (mockError) {
            console.error('Error initializing mock service fallback:', mockError);
            setService(null);
          }
        } else {
          setService(null);
        }
      }
    }

    initializeService();
  }, [strategy]);

  return service;
}

export default useChatService; 