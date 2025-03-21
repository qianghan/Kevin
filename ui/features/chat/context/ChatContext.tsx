'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { ChatMessage, ThinkingStep } from '../../../lib/types';

interface ChatContextType {
  messages: ChatMessage[];
  isLoading: boolean;
  streamingMessage: string;
  thinkingSteps: ThinkingStep[];
  isThinking: boolean;
  sendMessage: (message: string) => void;
  startNewChat: () => void;
  clearChat: () => void;
  updateTitle: (title: string) => Promise<boolean>;
  saveChatSession: () => Promise<boolean>;
  conversationId?: string;
  getRandomSampleQuestions: () => Array<{
    text: string;
    query: string;
  }>;
  useWebSearch: boolean;
  toggleWebSearch: () => void;
}

// Create the context with default values
const ChatContext = createContext<ChatContextType>({
  messages: [],
  isLoading: false,
  streamingMessage: '',
  thinkingSteps: [],
  isThinking: false,
  sendMessage: () => {},
  startNewChat: () => {},
  clearChat: () => {},
  updateTitle: async () => false,
  saveChatSession: async () => false,
  getRandomSampleQuestions: () => [],
  useWebSearch: false,
  toggleWebSearch: () => {},
});

// Hook for using the chat context
export const useChatContext = () => useContext(ChatContext);

interface ChatProviderProps {
  children: ReactNode;
  initialConversationId?: string;
  initialMessages?: ChatMessage[];
}

export function ChatProvider({ 
  children, 
  initialConversationId,
  initialMessages = [] 
}: ChatProviderProps) {
  // Generate initial conversation ID if not provided
  const startingConversationId = initialConversationId || (initialMessages.length > 0 ? uuidv4() : undefined);
  
  // State for managing chat
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [conversationId, setConversationId] = useState<string | undefined>(startingConversationId);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);
  const [useWebSearch, setUseWebSearch] = useState(false);

  // Toggle web search
  const toggleWebSearch = useCallback(() => {
    setUseWebSearch(prev => !prev);
  }, []);

  // Clean up the event source on unmount
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  // Get URL for streaming chat
  const getStreamUrl = useCallback((query: string): string => {
    try {
      const baseUrl = '/api/chat/query/stream';
      const params = new URLSearchParams();
      
      // Add required parameters
      params.append('query', query);
      
      // Only add conversationId if it exists
      if (conversationId) {
        params.append('conversation_id', conversationId);
      }
      
      // Additional parameters if needed
      params.append('use_web_search', useWebSearch.toString());
      params.append('stream', 'true');
      
      const queryString = params.toString();
      const url = queryString ? `${baseUrl}?${queryString}` : baseUrl;
      
      console.log('Generated stream URL:', url, { useWebSearch });
      return url;
    } catch (error) {
      console.error('Error generating stream URL:', error);
      throw new Error(`Failed to generate stream URL: ${error}`);
    }
  }, [conversationId, useWebSearch]);

  // Setup event source for streaming
  const setupEventSource = useCallback((url: string) => {
    // Close any existing connection
    if (eventSource) {
      eventSource.close();
    }
    
    // Create a new EventSource connection
    const source = new EventSource(url);
    setEventSource(source);
    console.log('EventSource created for URL:', url);
    
    // Reset streaming state
    setStreamingMessage('');
    setThinkingSteps([]);
    
    // Add message event handler (catch all events)
    source.onmessage = (event) => {
      console.log('Generic event received:', event.type, event.data);
      try {
        const data = JSON.parse(event.data);
        console.log('Parsed event data:', data);
        
        // First try handling as direct event data
        if (typeof data === 'string') {
          // Just append the string to the streaming message
          console.log('Detected string data, adding to stream:', data);
          setStreamingMessage(prev => prev + data);
          return;
        }
        
        // Handle various structures
        
        // Structure 1: { type: 'event_type', ... }
        if (data.type) {
          console.log('Detected type property:', data.type);
          // Process different event types
          if (data.type === 'thinking:start') {
            console.log('Thinking start detected in onmessage');
            setIsThinking(true);
            if (data.step) {
              setThinkingSteps(prev => [...prev, data.step]);
            }
          } else if (data.type === 'thinking:step') {
            console.log('Thinking step detected in onmessage');
            if (data.step) {
              setThinkingSteps(prev => [...prev, data.step]);
            }
          } else if (data.type === 'answer:chunk') {
            console.log('Answer chunk detected in onmessage');
            if (data.content) {
              setStreamingMessage(prev => prev + data.content);
            }
          } else if (data.type === 'done') {
            console.log('Done event detected in onmessage');
            // Create assistant message
            const assistantMessage: ChatMessage = {
              id: uuidv4(),
              role: 'assistant' as 'assistant',
              content: data.content || streamingMessage,
              timestamp: new Date(),
              thinkingSteps: thinkingSteps
            };
            
            console.log('Creating assistant message:', assistantMessage);
            setMessages(prev => [...prev, assistantMessage]);
            setStreamingMessage('');
            setIsLoading(false);
            setIsThinking(false);
            
            // Save conversation ID if provided
            if (data.conversation_id) {
              console.log('Setting conversation ID:', data.conversation_id);
              setConversationId(data.conversation_id);
            }
            
            // Close the connection
            console.log('Closing EventSource connection');
            source.close();
            setEventSource(null);
          }
        } 
        // Structure 2: { event: 'event_type', data: {...} }
        else if (data.event) {
          console.log('Detected event property:', data.event);
          if (data.event === 'thinking:start' || data.event === 'thinking') {
            setIsThinking(true);
            if (data.data && data.data.step) {
              setThinkingSteps(prev => [...prev, data.data.step]);
            }
          } else if (data.event === 'thinking:step' || data.event === 'thinking_step') {
            if (data.data && data.data.step) {
              setThinkingSteps(prev => [...prev, data.data.step]);
            }
          } else if (data.event === 'answer:chunk' || data.event === 'chunk' || data.event === 'answer') {
            if (data.data && data.data.content) {
              setStreamingMessage(prev => prev + data.data.content);
            } else if (data.data && typeof data.data === 'string') {
              setStreamingMessage(prev => prev + data.data);
            }
          } else if (data.event === 'done' || data.event === 'complete') {
            // Create assistant message
            let content = streamingMessage;
            if (data.data) {
              content = data.data.content || data.data || content;
            }
            
            const assistantMessage: ChatMessage = {
              id: uuidv4(),
              role: 'assistant' as 'assistant',
              content: content,
              timestamp: new Date(),
              thinkingSteps: thinkingSteps
            };
            
            console.log('Creating assistant message from event:', assistantMessage);
            setMessages(prev => [...prev, assistantMessage]);
            setStreamingMessage('');
            setIsLoading(false);
            setIsThinking(false);
            
            // Close the connection
            source.close();
            setEventSource(null);
          }
        }
        // Structure 3: Direct content in response
        else if (data.content || data.answer || data.response) {
          console.log('Detected direct content/answer/response');
          const content = data.content || data.answer || data.response;
          setStreamingMessage(prev => prev + content);
        }
      } catch (e) {
        console.error('Failed to parse event data:', e, event.data);
        
        // Try handling as plain text if JSON parsing fails
        const text = event.data;
        if (typeof text === 'string' && text.trim()) {
          console.log('Handling as plain text:', text);
          setStreamingMessage(prev => prev + text);
        }
      }
    };
    
    // Keep the specific event handlers for backwards compatibility
    
    // Handle thinking:start event
    source.addEventListener('thinking:start', (event) => {
      console.log('thinking:start event received:', event.data);
      setIsThinking(true);
      
      try {
        const data = JSON.parse(event.data);
        if (data && data.type && data.description) {
          setThinkingSteps(prev => [...prev, {
            type: data.type,
            description: data.description,
            time: new Date().toISOString()
          }]);
        }
      } catch (e) {
        console.error('Failed to parse thinking:start data:', e);
      }
    });
    
    // Handle thinking:update/step event
    source.addEventListener('thinking:step', (event) => {
      console.log('thinking:step event received:', event.data);
      try {
        const data = JSON.parse(event.data);
        if (data && data.step) {
          setThinkingSteps(prev => [...prev, data.step]);
        }
      } catch (e) {
        console.error('Failed to parse thinking:step data:', e);
      }
    });
    
    // Handle thinking:end event
    source.addEventListener('thinking:end', (event) => {
      console.log('thinking:end event received:', event.data);
      setIsThinking(false);
    });
    
    // Handle answer:chunk event
    source.addEventListener('answer:chunk', (event) => {
      console.log('answer:chunk event received:', event.data);
      try {
        const data = JSON.parse(event.data);
        if (data && data.content) {
          console.log('Adding content to streaming message:', data.content);
          // Append the content to the streaming message
          setStreamingMessage(prev => prev + data.content);
        }
      } catch (e) {
        console.error('Failed to parse answer:chunk data:', e);
      }
    });
    
    // Handle done event
    source.addEventListener('done', (event) => {
      console.log('done event received:', event.data);
      try {
        const data = JSON.parse(event.data);
        console.log('Done event data:', data);
        
        // Create the assistant message with the accumulated answer
        const assistantMessage: ChatMessage = {
          id: uuidv4(),
          role: 'assistant' as 'assistant',
          content: data.content || streamingMessage,
          timestamp: new Date(),
          thinkingSteps: thinkingSteps,
          documents: data.documents || []
        };
        
        console.log('Creating assistant message from done event:', assistantMessage);
        setMessages(prev => [...prev, assistantMessage]);
        
        // Save the conversation ID if provided
        if (data.conversation_id && !conversationId) {
          console.log('Setting conversation ID from done event:', data.conversation_id);
          setConversationId(data.conversation_id);
        }
        
        // Reset streaming state
        setStreamingMessage('');
        setIsLoading(false);
        setIsThinking(false);
        
        // Close the connection
        source.close();
        setEventSource(null);
      } catch (e) {
        console.error('Failed to parse done event data:', e);
        setIsLoading(false);
        setIsThinking(false);
      }
    });
    
    // Handle error event
    source.onerror = (error) => {
      console.error('EventSource error detailed:', error);
      setIsLoading(false);
      setIsThinking(false);
      
      // Add an error message
      const errorMessage: ChatMessage = {
        id: uuidv4(),
        role: 'assistant' as 'assistant',
        content: 'Sorry, there was an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      
      // Close the connection
      source.close();
      setEventSource(null);
    };
    
    return source;
  }, [conversationId, eventSource, streamingMessage, thinkingSteps]);

  // Handle sending a message
  const sendMessage = useCallback(async (content: string) => {
    if (isLoading || !content.trim()) return;

    // Generate a conversation ID if one doesn't exist yet
    if (!conversationId) {
      const newConversationId = uuidv4();
      console.log('Generated new conversation ID for new message:', newConversationId);
      setConversationId(newConversationId);
    }

    // Create a user message
    const userMessage: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    // Add user message to the messages list
    setMessages(prevMessages => [...prevMessages, userMessage]);
    
    // Set loading state
    setIsLoading(true);
    setStreamingMessage('');
    setThinkingSteps([]);
    setIsThinking(false);

    try {
      // Get streaming URL
      const url = getStreamUrl(content);
      console.log('Creating EventSource for URL:', url);
      
      // Create EventSource for streaming
      const source = new EventSource(url);
      setEventSource(source);
      
      // Variable to accumulate the final answer
      let accumulatedAnswer = '';
      
      // Generic onmessage handler for events without specific event handlers
      source.onmessage = (event) => {
        console.log('Generic message received:', event.data);
        try {
          const data = JSON.parse(event.data);
          console.log('Parsed generic data:', data);
        } catch (e) {
          console.error('Failed to parse generic event data:', e);
        }
      };
      
      // Handle thinking events
      source.addEventListener('thinking_start', (event) => {
        console.log('Thinking started');
        setIsThinking(true);
      });
      
      source.addEventListener('thinking_update', (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Thinking step:', data);
          if (data.type && data.description) {
            setThinkingSteps(prev => [...prev, {
              type: data.type,
              description: data.description,
              time: data.time || new Date().toISOString(),
              duration_ms: data.duration_ms
            }]);
          }
        } catch (e) {
          console.error('Failed to parse thinking update data:', e);
        }
      });
      
      source.addEventListener('thinking_end', () => {
        console.log('Thinking ended');
        setIsThinking(false);
      });
      
      // Handle answer chunks - this creates the typing effect
      source.addEventListener('answer_chunk', (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Answer chunk received:', data);
          
          if (data.chunk) {
            // Add the chunk to the accumulated answer
            accumulatedAnswer += data.chunk;
            
            // Update the streaming message for the typing effect
            setStreamingMessage(accumulatedAnswer);
          }
        } catch (e) {
          console.error('Failed to parse answer chunk data:', e);
        }
      });
      
      // Handle final answer
      source.addEventListener('answer', (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('Final answer received:', data);
          
          if (data.answer) {
            // Use the complete answer from the server if available
            accumulatedAnswer = data.answer;
            setStreamingMessage(accumulatedAnswer);
          }
        } catch (e) {
          console.error('Failed to parse answer data:', e);
        }
      });
      
      // Handle completion
      source.addEventListener('done', (event) => {
        console.log('Done event received');
        
        // Create the assistant message with the accumulated answer
        const assistantMessage: ChatMessage = {
          id: uuidv4(),
          role: 'assistant' as 'assistant',
          content: accumulatedAnswer || 'No response received',
          timestamp: new Date(),
          thinkingSteps: thinkingSteps
        };
        
        // Add the message to the chat
        setMessages(prevMessages => [...prevMessages, assistantMessage]);
        
        // Extract conversation ID if present
        try {
          const data = JSON.parse(event.data);
          if (data.conversation_id && !conversationId) {
            setConversationId(data.conversation_id);
          }
        } catch (e) {
          console.error('Failed to parse done event data:', e);
        }
        
        // Reset states
        setIsLoading(false);
        setStreamingMessage('');
        setIsThinking(false);
        
        // Close the event source
        source.close();
        setEventSource(null);
      });
      
      // Handle errors
      source.onerror = (error) => {
        console.error('EventSource error:', error);
        
        // Add error message only if we don't have an answer yet
        if (!accumulatedAnswer) {
          const errorMessage: ChatMessage = {
            id: uuidv4(),
            role: 'assistant' as 'assistant',
            content: 'Sorry, there was an error processing your request. Please try again.',
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, errorMessage]);
        } else {
          // If we have a partial answer, add it as the final message
          const assistantMessage: ChatMessage = {
            id: uuidv4(),
            role: 'assistant' as 'assistant',
            content: accumulatedAnswer,
            timestamp: new Date(),
            thinkingSteps: thinkingSteps
          };
          setMessages(prev => [...prev, assistantMessage]);
        }
        
        // Reset states
        setIsLoading(false);
        setIsThinking(false);
        setStreamingMessage('');
        
        // Close the event source
        source.close();
        setEventSource(null);
      };
      
    } catch (error) {
      console.error('Error setting up EventSource:', error);
      setIsLoading(false);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: uuidv4(),
        role: 'assistant' as 'assistant',
        content: 'Sorry, there was an error sending your message. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  }, [isLoading, getStreamUrl, thinkingSteps, conversationId]);
  
  // Save chat session
  const saveChatSession = useCallback(async (): Promise<boolean> => {
    console.log('Attempting to save chat session:', { 
      conversationId, 
      messageCount: messages.length 
    });
    
    // Generate a conversation ID if one doesn't exist
    let currentConversationId = conversationId;
    if (!currentConversationId) {
      currentConversationId = uuidv4();
      console.log('Generated new conversation ID for saving:', currentConversationId);
      setConversationId(currentConversationId);
    }
    
    if (messages.length === 0) {
      console.warn('Cannot save chat: No messages to save');
      return false;
    }
    
    try {
      console.log('Making save request to /api/chat/save');
      
      // Check user authentication status
      const authCheck = await fetch('/api/auth/session');
      if (!authCheck.ok) {
        console.error('Authentication check failed:', authCheck.status, authCheck.statusText);
        return false;
      }
      
      const authData = await authCheck.json();
      if (!authData || !authData.user) {
        console.error('User is not authenticated:', authData);
        return false;
      }
      
      // Now proceed with saving
      const payload = {
        conversation_id: currentConversationId,
        messages,
        context_summary: '' // Include this if your API expects it
      };
      
      console.log('Save payload:', {
        conversation_id: currentConversationId,
        messageCount: messages.length,
        firstMessageSample: messages.length > 0 ? 
          `${messages[0].role}: ${messages[0].content.substring(0, 30)}...` : 'none'
      });
      
      const response = await fetch('/api/chat/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        credentials: 'include' // Include cookies for authentication
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Failed to save chat session:', {
          status: response.status,
          statusText: response.statusText,
          error: errorText
        });
        return false;
      }
      
      const result = await response.json();
      console.log('Chat session saved successfully', {
        conversationId: currentConversationId,
        status: response.status,
        result
      });
      return true;
    } catch (error) {
      console.error('Error saving chat session:', error);
      return false;
    }
  }, [conversationId, messages]);

  // Start a new chat
  const startNewChat = useCallback(async () => {
    // First save the current chat if needed
    if (messages.length > 0 && conversationId) {
      console.log('Saving current chat before starting new one');
      try {
        const saved = await saveChatSession();
        console.log('Previous chat save result:', saved);
      } catch (error) {
        console.error('Error saving previous chat:', error);
      }
    }
    
    // Reset all state for new chat
    console.log('Starting new chat, resetting state');
    setMessages([]);
    
    // Generate a new conversation ID immediately
    const newConversationId = uuidv4();
    console.log('Generated new conversation ID for new chat:', newConversationId);
    setConversationId(newConversationId);
    
    setStreamingMessage('');
    setThinkingSteps([]);
    setIsThinking(false);
    setIsLoading(false);
    
    if (eventSource) {
      console.log('Closing existing EventSource');
      eventSource.close();
      setEventSource(null);
    }
  }, [eventSource, messages, conversationId, saveChatSession]);

  // Clear chat history
  const clearChat = useCallback(() => {
    setMessages([]);
    setStreamingMessage('');
    setThinkingSteps([]);
    setIsThinking(false);
    
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
    }
  }, [eventSource]);

  // Update the chat title
  const updateTitle = useCallback(async (title: string): Promise<boolean> => {
    if (!conversationId || !title.trim()) return false;
    
    try {
      const response = await fetch(`/api/chat/sessions/${conversationId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      });
      
      return response.ok;
    } catch (error) {
      console.error('Error updating title:', error);
      return false;
    }
  }, [conversationId]);

  // Auto-save when user navigates away
  useEffect(() => {
    const handleBeforeUnload = () => {
      if (messages.length > 0 && conversationId) {
        saveChatSession();
      }
    };
    
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [conversationId, messages, saveChatSession]);

  // Function to get random sample questions
  const getRandomSampleQuestions = useCallback(() => {
    // Define a pool of sample questions
    const questionPool = [
      {
        text: "UBC admission requirements",
        query: "What are the admission requirements for UBC Computer Science?"
      },
      {
        text: "Compare U of T vs McGill tuition",
        query: "Compare tuition costs between University of Toronto and McGill for international students"
      },
      {
        text: "Waterloo co-op programs",
        query: "Tell me about Waterloo University's co-op programs for engineering students"
      },
      {
        text: "UBC vs SFU comparison",
        query: "What are the main differences between UBC and SFU for a Biology major?"
      },
      {
        text: "Queen's University scholarships",
        query: "What scholarships are available for first-year students at Queen's University?"
      },
      {
        text: "Western University residence",
        query: "What are the housing options for first-year students at Western University?"
      },
      {
        text: "McGill graduate programs",
        query: "What are the admission requirements for McGill's MBA program?"
      },
      {
        text: "UVic vs UNBC comparison",
        query: "Compare the Environmental Science programs at UVic and UNBC"
      }
    ];
    
    // Shuffle the array
    const shuffled = [...questionPool].sort(() => 0.5 - Math.random());
    
    // Take the first 2 questions
    return shuffled.slice(0, 2);
  }, []);

  // Context value
  const contextValue: ChatContextType = {
    messages,
    isLoading,
    streamingMessage,
    thinkingSteps,
    isThinking,
    sendMessage,
    startNewChat,
    clearChat,
    updateTitle,
    saveChatSession,
    conversationId,
    getRandomSampleQuestions,
    useWebSearch,
    toggleWebSearch
  };

  return (
    <ChatContext.Provider value={contextValue}>
      {children}
    </ChatContext.Provider>
  );
} 