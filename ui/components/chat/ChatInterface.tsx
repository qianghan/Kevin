'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { useSession } from 'next-auth/react';
import { chatApi, ChatRequest, ChatResponse } from '@/lib/api/kevin';
import { ChatMessage } from '@/models/ChatSession';
import { useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { generateContextSummary } from '@/lib/utils/contextSummary';

// Types for streaming events
interface ThinkingStep {
  type: string;
  description: string;
  time: string;
  duration_ms?: number;
  content?: string;
}

interface StreamEvent {
  event: string;
  data: any;
}

interface ChatInterfaceProps {
  sessionId?: string;
  onNewSession?: (sessionId: string) => void;
  initialMessages?: ChatMessage[];
}

// Debug logger function for thinking steps
const logThinkingStep = (prefix: string, step: ThinkingStep | null, eventData?: string) => {
  console.log(
    `%c${prefix}`,
    'background: #0066cc; color: white; padding: 2px 5px; border-radius: 3px; font-weight: bold;',
    step 
      ? {
          description: step.description,
          time: step.time,
          duration: step.duration_ms,
          contentLength: step.content?.length || 0
        }
      : 'No step data',
    eventData ? `Raw data: ${eventData.substring(0, 100)}${eventData.length > 100 ? '...' : ''}` : ''
  );
};

export default function ChatInterface({ 
  sessionId, 
  onNewSession,
  initialMessages = [] 
}: ChatInterfaceProps) {
  const { data: session } = useSession();
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(sessionId);
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  // Track the last saved state to prevent duplicate saves
  const [lastSavedHash, setLastSavedHash] = useState<string>('');
  const [contextSummary, setContextSummary] = useState<string>('');
  
  // Use a ref to keep track of the accumulated message content
  // This is more reliable than relying only on state for capturing content
  const accumulatedContentRef = useRef('');
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Group messages into exchanges (user + assistant pairs)
  const messageExchanges = useMemo(() => {
    const exchanges: ChatMessage[][] = [];
    let currentExchange: ChatMessage[] = [];
    
    messages.forEach(message => {
      currentExchange.push(message);
      if (message.role === 'assistant') {
        exchanges.push([...currentExchange]);
        currentExchange = [];
      }
    });
    
    // Add any remaining messages
    if (currentExchange.length > 0) {
      exchanges.push(currentExchange);
    }
    
    return exchanges;
  }, [messages]);

  // Log component initialization
  useEffect(() => {
    console.log('ChatInterface mounted/initialized', 
      { initialMessagesCount: initialMessages.length, sessionId });
  }, []);

  // Scroll to bottom when new messages are added
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Add debug logging to track state changes
    console.log('State updated - Messages:', messages.length, 'Streaming:', streamingMessage ? 'yes' : 'no');
  }, [messages, streamingMessage, thinkingSteps]);

  // Clean up event source on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // Generate a hash of the current messages to track if they've been saved
  const generateMessageHash = (msgs: ChatMessage[]): string => {
    return msgs.map(m => `${m.role}:${m.content.substring(0, 50)}`).join('|');
  };

  // Update context summary when messages change
  useEffect(() => {
    if (messages.length > 0) {
      const summary = generateContextSummary(messages);
      setContextSummary(summary);
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading) return;
    
    // Add user message to the UI
    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setInput('');
    
    // If in search mode, add search prefix
    if (isSearchMode) {
      await streamResponse(`[Search] ${input}`);
      setIsSearchMode(false); // Reset search mode after sending
    } else {
      // Regular chat mode
      await streamResponse(input);
    }
  };

  const streamResponse = async (query: string) => {
    // Close any existing event source
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    
    // Reset all state for new response
    setIsThinking(true); // Always set thinking to true when we start a response
    setThinkingSteps([]);
    setStreamingMessage('');
    setIsLoading(true);
    
    // Reset the accumulated content ref
    accumulatedContentRef.current = '';
    
    // Create request for Kevin API
    const chatRequest: ChatRequest = {
      query,
      conversation_id: conversationId,
      context_summary: contextSummary,
      stream: true,
      debug_mode: true // Enable debug mode to get thinking steps
    };
    
    console.log('Sending chat request with debug_mode enabled:', chatRequest);
    
    // Get streaming URL
    const streamUrl = chatApi.getStreamUrl(chatRequest);
    console.log('Stream URL:', streamUrl);
    
    // Create synthetic thinking step immediately
    const initialStep = {
      type: 'thinking',
      description: 'Starting request to DeepSeek r1',
      time: new Date().toTimeString().split(' ')[0],
      duration_ms: 0
    };
    setThinkingSteps([initialStep]);
    
    // Create new event source
    const eventSource = new EventSource(streamUrl);
    eventSourceRef.current = eventSource;
    
    // Setup progressive synthetic thinking steps with constant reference for cleanup
    const syntheticSteps = [
      'Starting query processing',
      'Analyzing query context',
      'Processing with DeepSeek r1',
      'Reasoning through the question',
      'Formulating response',
      'Organizing content',
      'Finalizing answer'
    ];

    // Add first synthetic step immediately after connection establishes
    setTimeout(() => {
      console.log('Adding first synthetic step');
      if (isThinking) {
        const newStep = {
          type: 'thinking',
          description: syntheticSteps[0],
          time: new Date().toTimeString().split(' ')[0],
          duration_ms: 500
        };
        setThinkingSteps(prev => {
          // Check if we already have this step
          const hasStep = prev.some(step => step.description === newStep.description);
          if (hasStep) {
            console.log('Step already exists, not adding duplicate:', newStep.description);
            return prev;
          }
          console.log('Adding synthetic step:', newStep.description);
          return [...prev, newStep];
        });
      }
    }, 500);
    
    // Add remaining synthetic steps at intervals
    let stepCount = 1; // Start with the second step (index 1)
    const syntheticStepsInterval = setInterval(() => {
      console.log('Synthetic steps interval fired, step:', stepCount);
      
      if (stepCount < syntheticSteps.length && isThinking) {
        const newStep = {
          type: 'thinking',
          description: syntheticSteps[stepCount],
          time: new Date().toTimeString().split(' ')[0],
          duration_ms: (stepCount + 1) * 500
        };
        
        setThinkingSteps(prev => {
          // Check if we already have this step
          const hasStep = prev.some(step => step.description === newStep.description);
          if (hasStep) {
            console.log('Step already exists, not adding duplicate:', newStep.description);
            return prev;
          }
          console.log('Adding synthetic step:', newStep.description);
          return [...prev, newStep];
        });
        
        stepCount++;
      } else {
        console.log('Clearing synthetic steps interval');
        clearInterval(syntheticStepsInterval);
      }
    }, 2000); // 2 seconds between steps
    
    // Log connection state changes
    eventSource.onopen = () => {
      console.log('EventSource connection opened');
    };
    
    // Set up event listeners with better debugging
    eventSource.addEventListener('thinking_start', (e) => {
      console.log('Thinking START event received:', e.data);
      handleThinkingStart(e);
    });
    
    eventSource.addEventListener('thinking_update', (e) => {
      console.log('Thinking UPDATE event received:', e.data);
      handleThinkingUpdate(e);
    });
    
    eventSource.addEventListener('thinking_end', (e) => {
      console.log('Thinking END event received:', e.data);
      handleThinkingEnd(e);
    });
    
    eventSource.addEventListener('answer_start', (e) => {
      console.log('Answer START event received');
      handleAnswerStart();
    });
    
    eventSource.addEventListener('answer_chunk', (e) => {
      console.log('Answer CHUNK event received');
      handleAnswerChunk(e as MessageEvent);
    });
    
    // Add handler for the plain 'answer' event to handle full answers (e.g., from cache)
    eventSource.addEventListener('answer', (e) => {
      console.log('Answer event received');
      handleAnswer(e as MessageEvent);
    });
    
    eventSource.addEventListener('document', (e) => {
      console.log('Document event received');
      handleDocument(e as MessageEvent);
    });
    
    eventSource.addEventListener('done', (e) => {
      console.log('Done event received');
      handleDone(e as MessageEvent);
    });
    
    eventSource.addEventListener('error', (e) => {
      console.log('Error event received');
      handleError(e as MessageEvent);
    });
    
    // Clean up function for synthetic steps when done
    const cleanup = () => {
      console.log('Cleaning up synthetic steps interval');
      clearInterval(syntheticStepsInterval);
    };
    
    // Handle errors
    eventSource.onerror = (error) => {
      console.log('EventSource connection error occurred:', error);
      eventSource.close();
      setIsLoading(false);
      setIsThinking(false);
      cleanup();
      
      // Add user-friendly error message to the chat
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: "I'm sorry, there was an error connecting to the chat service. Please try again later.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    };
    
    // Return cleanup function
    return () => {
      cleanup();
    };
  };

  // Event handlers for streaming
  const handleThinkingStart = (e: MessageEvent) => {
    console.log('handleThinkingStart called with data:', e.data);
    setIsThinking(true);
    try {
      const data = JSON.parse(e.data);
      console.log('Thinking started:', data);
      logThinkingStep('THINKING START', data, e.data);
    } catch (err) {
      console.error('Error parsing thinking_start event', err);
    }
  };

  // Enhance handleThinkingUpdate to better debug and handle real thinking steps
  const handleThinkingUpdate = (e: MessageEvent) => {
    console.log('handleThinkingUpdate called with data:', e.data);
    try {
      const data = JSON.parse(e.data) as ThinkingStep;
      console.log('Thinking update parsed:', data);
      logThinkingStep('THINKING UPDATE', data, e.data);
      
      // Only add real steps that have unique descriptions
      if (data && data.description) {
        // Check if we already have this step (avoid duplicates)
        setThinkingSteps(prev => {
          const isDuplicate = prev.some(
            step => step.description === data.description
          );
          
          if (!isDuplicate) {
            console.log('Adding real thinking step:', data.description);
            return [...prev, data];
          } else {
            console.log('Skipping duplicate thinking step:', data.description);
            return prev;
          }
        });
      }
    } catch (err) {
      console.error('Error parsing thinking_update event', err, 'Raw data:', e.data);
    }
  };

  const handleThinkingEnd = (e: MessageEvent) => {
    console.log('handleThinkingEnd called with data:', e.data);
    // We don't set isThinking to false here anymore so steps remain visible
    // The state will be cleared after everything is complete in handleDone
    try {
      const data = JSON.parse(e.data);
      console.log('Thinking ended with data:', data);
      logThinkingStep('THINKING END', data, e.data);
      
      // Add a final thinking step when thinking ends
      const finalStep = {
        type: 'thinking',
        description: 'Thinking complete, generating response',
        time: new Date().toTimeString().split(' ')[0],
        duration_ms: 0
      };
      
      setThinkingSteps(prev => {
        // Check for duplicate
        const isDuplicate = prev.some(step => step.description === finalStep.description);
        if (!isDuplicate) {
          return [...prev, finalStep];
        }
        return prev;
      });
    } catch (err) {
      console.error('Error in thinking_end handler:', err);
    }
  };

  const handleAnswerStart = () => {
    console.log('handleAnswerStart called');
    // Generate a unique ID for this streaming session
    const newStreamingId = Date.now().toString();
    setStreamingId(newStreamingId);
    
    // Reset both the state and the ref
    setStreamingMessage('');
    accumulatedContentRef.current = '';
    
    // Add a thinking step for answer start
    const answerStartStep = {
      type: 'thinking',
      description: 'Starting to generate response',
      time: new Date().toTimeString().split(' ')[0],
      duration_ms: 0
    };
    
    setThinkingSteps(prev => {
      // Check for duplicate
      const isDuplicate = prev.some(step => step.description === answerStartStep.description);
      if (!isDuplicate) {
        return [...prev, answerStartStep];
      }
      return prev;
    });
  };

  const handleAnswerChunk = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      const chunk = data.chunk || '';
      
      // Add logging for answer chunks (but limit to avoid flooding)
      if (chunk && chunk.length < 50) {
        console.log('Answer chunk received:', chunk);
      } else {
        console.log('Answer chunk received, length:', chunk?.length || 0);
      }
      
      // Update both the state (for display) and the ref (for storage)
      accumulatedContentRef.current += chunk;
      setStreamingMessage(prev => prev + chunk);
      
      // Periodically add thinking steps during long responses
      if (accumulatedContentRef.current.length % 500 === 0) {
        const progressStep = {
          type: 'thinking',
          description: `Generated ${accumulatedContentRef.current.length} characters so far`,
          time: new Date().toTimeString().split(' ')[0],
          duration_ms: 0
        };
        
        setThinkingSteps(prev => {
          // Avoid too many progress updates by checking if we already have a similar one
          const hasProgressStep = prev.some(step => 
            step.description.includes('Generated') && 
            step.description.includes('characters so far')
          );
          
          if (!hasProgressStep) {
            return [...prev, progressStep];
          }
          return prev;
        });
      }
    } catch (err) {
      console.error('Error parsing answer_chunk event', err);
    }
  };

  // Handler for the full answer event
  const handleAnswer = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data) as { answer?: string };
      
      // Only use this if we haven't accumulated content from chunks
      if (!accumulatedContentRef.current || accumulatedContentRef.current.trim().length === 0) {
        console.log('Using full answer as accumulated content was empty');
        
        // Get the answer from the event data
        const fullAnswer = data.answer || '';
        
        if (fullAnswer && fullAnswer.trim().length > 0) {
          // Update both the reference and the displayed message
          accumulatedContentRef.current = fullAnswer;
          setStreamingMessage(fullAnswer);
          
          // Add a thinking step to show we received the full answer
          const answerStep = {
            type: 'thinking',
            description: 'Received complete answer from server',
            time: new Date().toTimeString().split(' ')[0],
            duration_ms: 0
          };
          
          setThinkingSteps(prev => {
            const isDuplicate = prev.some(step => step.description === answerStep.description);
            if (!isDuplicate) {
              return [...prev, answerStep];
            }
            return prev;
          });
        }
      } else {
        console.log('Ignoring full answer as we already have accumulated content:', 
          accumulatedContentRef.current.length);
      }
    } catch (err) {
      console.error('Error parsing answer event', err);
    }
  };

  const handleDocument = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      console.log('Document:', data);
      // Handle documents as needed
    } catch (err) {
      console.error('Error parsing document event', err);
    }
  };

  const handleDone = (e: MessageEvent) => {
    try {
      console.log('handleDone called - Starting message processing');
      const data = JSON.parse(e.data);
      
      // Update conversation ID
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
        
        // Notify parent about new session if needed
        if (!sessionId && onNewSession) {
          onNewSession(data.conversation_id);
        }
      }
      
      // Get the content from our ref instead of the state
      const finalContent = accumulatedContentRef.current;
      console.log('Final content from ref length:', finalContent.length);
      
      // Close the event source first
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      
      if (!finalContent || finalContent.trim().length === 0) {
        console.error('Empty message content detected, not adding to chat. Ref content:', 
          finalContent ? 'empty string' : 'null/undefined');
        setIsLoading(false);
        setIsThinking(false);
        return;
      }
      
      // Add a final synthetic thinking step if needed
      const finalStep = {
        type: 'thinking',
        description: 'Response completed',
        time: new Date().toTimeString().split(' ')[0],
        duration_ms: 0
      };
      
      setThinkingSteps(prev => {
        // Check for duplicate
        const isDuplicate = prev.some(step => step.description === finalStep.description);
        if (!isDuplicate) {
          return [...prev, finalStep];
        }
        return prev;
      });
      
      // Create the assistant message
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: finalContent,
        timestamp: new Date(),
        thinkingSteps: [...thinkingSteps],
      };
      
      // Add message to chat history
      console.log('Adding message to chat history with content length:', finalContent.length);
      
      // First add the message to the chat history
      setMessages(prevMessages => {
        const updatedMessages = [...prevMessages, assistantMessage];
        
        // Save the conversation to the database in the background
        if (data.conversation_id) {
          saveConversationToDatabase(data.conversation_id, updatedMessages)
            .catch(err => console.error('Failed to save conversation:', err));
        }
        
        return updatedMessages;
      });
      
      // Then clear the streaming message state after a delay
      setTimeout(() => {
        console.log('Timeout executed - clearing streaming state');
        setStreamingMessage('');
        setStreamingId(null);
        setThinkingSteps([]);
        setIsLoading(false);
        setIsThinking(false); // Finally clear the thinking state
      }, 500);
      
    } catch (err) {
      console.error('Error parsing done event', err);
      setIsLoading(false);
      setIsThinking(false);
    }
  };

  // Function to save the conversation to the database
  const saveConversationToDatabase = async (conversationId: string, messageList: ChatMessage[]) => {
    if (!session?.user) return;
    
    const currentHash = generateMessageHash(messageList);
    
    // Skip saving if this exact message set was already saved
    if (currentHash === lastSavedHash) {
      console.log('Skipping save - messages already saved');
      return;
    }
    
    try {
      const response = await fetch('/api/chat/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          title: messageList.length > 0 ? messageList[0].content.substring(0, 50) : 'New Chat',
          messages: messageList,
          context_summary: contextSummary // Include the context summary
        }),
      });

      if (response.ok) {
        setLastSavedHash(currentHash);
        console.log('Conversation saved successfully');
      } else {
        console.error('Failed to save conversation');
      }
    } catch (error) {
      console.error('Error saving conversation:', error);
    }
  };

  const handleError = (e: MessageEvent) => {
    // Simple logging without trying to access detailed properties
    console.log('Stream error event received');
    
    setIsLoading(false);
    
    // Close the event source
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  // Non-streaming fallback
  const sendMessageWithoutStreaming = async (query: string) => {
    try {
      const chatRequest: ChatRequest = {
        query,
        conversation_id: conversationId,
        stream: false
      };
      
      const response = await chatApi.query(chatRequest);
      
      // Update conversation ID
      if (response.conversation_id) {
        setConversationId(response.conversation_id);
        
        // Notify parent about new session if needed
        if (!sessionId && onNewSession) {
          onNewSession(response.conversation_id);
        }
      }
      
      // Add assistant message
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        thinkingSteps: response.thinking_steps,
        documents: response.documents
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Add a function to copy message content to clipboard
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        console.log('Text copied to clipboard');
      })
      .catch(err => {
        console.error('Failed to copy text: ', err);
      });
  };

  // Add a function to toggle search mode
  const toggleSearchMode = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsSearchMode(!isSearchMode);
  };

  // Function to start a new chat
  const startNewChat = async () => {
    // Don't allow starting a new chat while loading or saving
    if (isLoading || isSaving) return;
    
    try {
      // If we have messages and a conversation ID, save the current session
      if (messages.length > 0) {
        setIsSaving(true);
        
        // Generate a temporary conversation ID if we don't have one
        const chatId = conversationId || `temp-${Date.now()}`;
        
        console.log('Saving session before starting new chat, conversationId:', chatId);
        
        // Get current hash - may already be saved from previous assistant message
        const currentHash = generateMessageHash(messages);
        if (currentHash === lastSavedHash) {
          console.log('Chat already saved with current messages, skipping duplicate save');
        } else {
          // Save the current conversation to the database
          await saveConversationToDatabase(chatId, messages);
          console.log('Session saved successfully before starting new chat');
        }
      } else {
        console.log('No messages to save before starting new chat');
      }
    } catch (error) {
      console.error('Error saving session before new chat:', error);
    } finally {
      setIsSaving(false);
    }
    
    // Clear current conversation state and reset hash tracking
    setMessages([]);
    setConversationId(undefined);
    setInput('');
    setStreamingMessage('');
    setStreamingId(null);
    setThinkingSteps([]);
    setLastSavedHash(''); // Reset the hash for the new conversation
    accumulatedContentRef.current = '';
    
    // Reset search mode
    setIsSearchMode(false);
    
    // If there's a handler to notify the parent component
    if (onNewSession) {
      onNewSession('new'); // Signal to parent that we want a new chat
    }
  };

  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-6 relative bg-gray-50 w-full">
        {/* Debug output */}
        {process.env.NODE_ENV === 'development' && (
          <div className="text-xs text-gray-400 mb-2">
            Accumulated content length: {accumulatedContentRef.current.length}
          </div>
        )}
        
        {/* Welcome message when no messages exist */}
        {messages.length === 0 && !streamingMessage && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md mx-auto p-8 rounded-xl bg-white shadow-lg border border-gray-100 bg-gradient-to-b from-white to-gray-50">
              <div className="mb-6 bg-gradient-to-br from-indigo-500 to-purple-600 text-white w-20 h-20 rounded-full flex items-center justify-center mx-auto shadow-md">
                <span className="text-3xl font-bold" style={{ textShadow: '0px 2px 3px rgba(0, 0, 0, 0.3)' }}>K</span>
              </div>
              <h3 className="text-2xl font-semibold text-gray-800 mb-3">Welcome to Kevin.AI</h3>
              <p className="text-gray-600 mb-8 leading-relaxed">Let Kevin.AI assist you with Canadian university information...</p>
              <div className="flex flex-col sm:flex-row justify-center gap-3">
                <button 
                  onClick={() => setInput("What are the admission requirements for UBC Computer Science?")}
                  className="px-4 py-3 bg-gray-100 hover:bg-gray-200 rounded-xl text-sm text-gray-700 transition-colors font-medium shadow-sm hover:shadow"
                >
                  UBC Computer Science requirements
                </button>
                <button 
                  onClick={() => setInput("Compare tuition costs between University of Toronto and McGill for international students")}
                  className="px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-xl text-sm text-white transition-colors font-medium shadow-sm hover:shadow"
                >
                  UofT vs McGill tuition costs
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Show date separator for messages */}
        {messages.length > 0 && (
          <div className="flex justify-center">
            <span className="text-xs text-gray-600 bg-white px-3 py-1.5 rounded-full shadow-md border border-gray-100 font-medium">
              {new Date(messages[0].timestamp).toLocaleDateString(undefined, {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </span>
          </div>
        )}
        
        {/* Show all message exchanges instead of just the most recent one */}
        {messageExchanges.map((exchange, exchangeIndex) => (
          <div key={`exchange-${exchangeIndex}`} className="space-y-6 mb-6">
            {exchange.map((message, messageIndex) => (
              <div 
                key={`message-${exchangeIndex}-${messageIndex}-${message.timestamp.getTime()}`} 
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {/* Role indicator for assistant */}
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-emerald-600 text-white flex items-center justify-center mr-2 flex-shrink-0 mt-1 shadow-md">
                    <span className="text-lg font-bold" style={{ textShadow: '0px 1px 2px rgba(0, 0, 0, 0.2)' }}>K</span>
                  </div>
                )}
                
                <div 
                  className={`p-5 rounded-2xl max-w-[85%] md:max-w-[75%] relative group ${
                    message.role === 'user' 
                      ? 'bg-gradient-to-br from-indigo-600 to-purple-700 text-white shadow-lg'
                      : 'bg-white text-gray-800 border border-gray-100 shadow-md hover:shadow-lg transition-shadow'
                  }`}
                >
                  {/* Copy button - only visible on hover */}
                  <button
                    onClick={() => copyToClipboard(message.content)}
                    className={`absolute top-3 right-3 p-1.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity text-xs ${
                      message.role === 'user' 
                        ? 'bg-indigo-400/50 hover:bg-indigo-400 text-white backdrop-blur-sm' 
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
                    }`}
                    title="Copy message"
                    aria-label="Copy message"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                    </svg>
                  </button>
                  
                  <div className={`whitespace-pre-wrap markdown-content text-base leading-relaxed ${
                    message.role === 'user' 
                      ? 'text-white !important font-medium' 
                      : 'text-gray-700'
                  }`}
                  style={message.role === 'user' 
                    ? { 
                        color: 'white', 
                        textShadow: '0px 1px 2px rgba(0, 0, 0, 0.25)'
                      } 
                    : undefined
                  }
                  >
                    {message.role === 'assistant' ? (
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          a: ({ node, ...props }) => (
                            <a 
                              {...props} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 hover:underline"
                            />
                          )
                        }}
                      >
                        {message.content}
                      </ReactMarkdown>
                    ) : (
                      message.content
                    )}
                  </div>

                  {/* Message timestamp */}
                  <div className={`text-xs mt-3 flex items-center ${
                    message.role === 'user' 
                      ? 'text-indigo-100/75' 
                      : 'text-gray-400'
                  }`}>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {message.timestamp.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
                  </div>
                </div>
                
                {/* Role indicator for user */}
                {message.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center ml-2 flex-shrink-0 mt-1 shadow-md">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        ))}
        
        {/* Simple loading indicator when waiting for response */}
        {isLoading && !streamingMessage && (
          <div className="flex justify-center my-6">
            <div className="flex items-center space-x-2 bg-white px-5 py-3 rounded-full shadow-md border border-gray-100">
              <div className="animate-pulse flex items-center">
                <div className="h-2.5 w-2.5 mr-1 bg-indigo-500 rounded-full"></div>
                <div className="h-2.5 w-2.5 mr-1 bg-indigo-500 rounded-full animation-delay-200"></div>
                <div className="h-2.5 w-2.5 bg-indigo-500 rounded-full animation-delay-500"></div>
              </div>
              <span className="text-sm text-gray-600 font-medium">Kevin is thinking...</span>
            </div>
          </div>
        )}
        
        {/* Streaming message - only show if not already in messages array and we're loading */}
        {streamingMessage && isLoading && (
          <div className="flex justify-start" id={`streaming-${streamingId}`}>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-emerald-600 text-white flex items-center justify-center mr-2 flex-shrink-0 mt-1 shadow-md">
              <span className="text-lg font-bold" style={{ textShadow: '0px 1px 2px rgba(0, 0, 0, 0.2)' }}>K</span>
            </div>
            <div className="p-5 rounded-2xl max-w-[85%] md:max-w-[75%] bg-white text-gray-700 border border-gray-100 relative group shadow-md hover:shadow-lg transition-shadow">
              {/* Copy button for streaming message */}
              <button
                onClick={() => copyToClipboard(streamingMessage)}
                className="absolute top-3 right-3 p-1.5 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity text-xs"
                title="Copy message"
                aria-label="Copy message"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                </svg>
              </button>
              
              <div className="whitespace-pre-wrap markdown-content text-base leading-relaxed">
                <ReactMarkdown 
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: ({ node, ...props }) => (
                      <a 
                        {...props} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 hover:underline"
                      />
                    )
                  }}
                >
                  {streamingMessage}
                </ReactMarkdown>
                <span className="animate-pulse text-indigo-500 font-medium">▋</span>
              </div>
              {/* Add length info for debugging */}
              {process.env.NODE_ENV === 'development' && (
                <div className="text-xs text-gray-500 opacity-50 mt-3">
                  Streaming length: {streamingMessage.length}
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* New Chat Button - Now at the bottom of the chat area */}
        {messages.length > 0 && (
          <div className="flex justify-center my-8 sticky bottom-4">
            <button
              onClick={startNewChat}
              disabled={isLoading || isSaving}
              className="flex items-center px-5 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 border border-transparent rounded-full hover:shadow-lg transition-all text-white font-medium shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              {isSaving ? 'Saving conversation...' : 'Start New Chat'}
            </button>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input form - Updated for a more modern look */}
      <div className="bg-gray-50 p-4 border-t border-gray-100">
        <div className="max-w-4xl mx-auto relative">
          <form onSubmit={handleSubmit} className="flex space-x-3">
            <div className="relative flex-1 flex items-start">
              {/* Styled textarea for multi-line support */}
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (input.trim() && !isLoading) {
                      handleSubmit(e);
                    }
                  }
                }}
                placeholder={isSearchMode ? "Search the web..." : "Ask me anything..."}
                rows={1}
                style={{ 
                  minHeight: '56px', 
                  maxHeight: '200px',
                  resize: 'none', 
                  height: 'auto',
                  paddingRight: '3rem' 
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = `${Math.min(target.scrollHeight, 200)}px`;
                }}
                className={`w-full p-4 pr-12 border rounded-xl shadow-md ${
                  isSearchMode 
                    ? "bg-blue-50 border-blue-200 focus:bg-blue-50/80" 
                    : "bg-white border-gray-200 focus:bg-white"
                } focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all text-gray-700`}
                disabled={isLoading}
              />
              
              {/* Search toggle button with improved styling */}
              <div className="absolute right-3 top-3">
                <button
                  onClick={toggleSearchMode}
                  type="button"
                  className={`p-2 rounded-full transition-all ${
                    isSearchMode 
                      ? "text-white bg-indigo-500 shadow-md" 
                      : "text-gray-500 bg-gray-100 hover:bg-gray-200 hover:text-gray-700"
                  }`}
                  title={isSearchMode ? "Back to chat mode" : "Switch to search mode"}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </button>
              </div>
            </div>
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className={`p-4 rounded-xl w-14 h-auto flex-shrink-0 flex items-center justify-center transition-all ${
                isLoading 
                  ? "bg-gray-300 text-gray-500 cursor-not-allowed" 
                  : isSearchMode 
                    ? "bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:shadow-md shadow-sm hover:from-indigo-600 hover:to-purple-700" 
                    : "bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:shadow-md shadow-sm hover:from-indigo-600 hover:to-purple-700"
              }`}
              style={{ alignSelf: 'flex-start' }}
            >
              {isLoading ? (
                <span className="animate-pulse">...</span>
              ) : isSearchMode ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                </svg>
              )}
            </button>
          </form>
          
          <div className="text-xs text-gray-500 mt-3 text-center">
            AI responses may not always be accurate. Verify important information.
          </div>
        </div>
      </div>
    </div>
  );
} 