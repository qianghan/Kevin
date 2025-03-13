'use client';

import { useState, useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { chatApi, ChatRequest, ChatResponse } from '@/lib/api/kevin';
import { ChatMessage } from '@/models/ChatSession';
import { useRouter } from 'next/navigation';

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

export default function ChatInterface({ 
  sessionId, 
  onNewSession,
  initialMessages = [] 
}: ChatInterfaceProps) {
  const { data: session } = useSession();
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const eventSourceRef = useRef<EventSource | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage, thinkingSteps]);

  // Clean up event source on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

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
    
    // Start streaming response
    await streamResponse(input);
  };

  const streamResponse = async (query: string) => {
    // Close any existing event source
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    
    // Reset state for new response
    setIsThinking(false);
    setThinkingSteps([]);
    setStreamingMessage('');
    
    // Create request for Kevin API
    const chatRequest: ChatRequest = {
      query,
      conversation_id: conversationId,
      stream: true
    };
    
    // Get streaming URL
    const streamUrl = chatApi.getStreamUrl(chatRequest);
    
    // Create new event source
    const eventSource = new EventSource(streamUrl);
    eventSourceRef.current = eventSource;
    
    // Set up event listeners
    eventSource.addEventListener('thinking_start', handleThinkingStart);
    eventSource.addEventListener('thinking_update', handleThinkingUpdate);
    eventSource.addEventListener('thinking_end', handleThinkingEnd);
    eventSource.addEventListener('answer_start', handleAnswerStart);
    eventSource.addEventListener('answer_chunk', handleAnswerChunk);
    eventSource.addEventListener('document', handleDocument);
    eventSource.addEventListener('done', handleDone);
    eventSource.addEventListener('error', handleError);
    
    // Handle errors
    eventSource.onerror = (error) => {
      console.error('EventSource error:', error);
      eventSource.close();
      setIsLoading(false);
    };
  };

  // Event handlers for streaming
  const handleThinkingStart = (e: MessageEvent) => {
    setIsThinking(true);
    try {
      const data = JSON.parse(e.data);
      console.log('Thinking started:', data);
    } catch (err) {
      console.error('Error parsing thinking_start event', err);
    }
  };

  const handleThinkingUpdate = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data) as ThinkingStep;
      setThinkingSteps(prev => [...prev, data]);
    } catch (err) {
      console.error('Error parsing thinking_update event', err);
    }
  };

  const handleThinkingEnd = () => {
    setIsThinking(false);
  };

  const handleAnswerStart = () => {
    setStreamingMessage('');
  };

  const handleAnswerChunk = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      setStreamingMessage(prev => prev + (data.chunk || ''));
    } catch (err) {
      console.error('Error parsing answer_chunk event', err);
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
      const data = JSON.parse(e.data);
      
      // Update conversation ID
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
        
        // Notify parent about new session if needed
        if (!sessionId && onNewSession) {
          onNewSession(data.conversation_id);
        }
      }
      
      // Add assistant message to messages
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: streamingMessage,
        timestamp: new Date(),
        thinkingSteps: thinkingSteps,
        // Add documents if needed
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      setStreamingMessage('');
      setThinkingSteps([]);
      
      // Close the event source
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      
      setIsLoading(false);
    } catch (err) {
      console.error('Error parsing done event', err);
      setIsLoading(false);
    }
  };

  const handleError = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      console.error('Stream error:', data);
    } catch (err) {
      console.error('Error parsing error event', err);
    }
    
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

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Messages */}
        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div 
              className={`p-3 rounded-lg max-w-[80%] ${
                message.role === 'user' 
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>
            </div>
          </div>
        ))}
        
        {/* Thinking steps */}
        {isThinking && (
          <div className="bg-gray-100 p-3 rounded-lg space-y-2">
            <h3 className="font-semibold text-sm">Thinking...</h3>
            {thinkingSteps.map((step, i) => (
              <div key={i} className="text-xs">
                <span className="text-gray-500">{step.time}</span>
                <span className="ml-2">{step.description}</span>
              </div>
            ))}
          </div>
        )}
        
        {/* Streaming message */}
        {streamingMessage && (
          <div className="flex justify-start">
            <div className="p-3 rounded-lg max-w-[80%] bg-gray-200 text-gray-800">
              <div className="whitespace-pre-wrap">
                {streamingMessage}
                {isLoading && <span className="animate-pulse">▋</span>}
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input form */}
      <div className="border-t p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 p-2 border rounded-lg"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50"
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  );
} 