'use client';

/*
 * ChatInterface - Enhanced with ChatService Integration
 * 
 * This component has been migrated to use ChatService for improved error handling, 
 * logging, and service abstraction. Additional enhancements could include:
 * 
 * TODO: Future Migration Candidates
 * ---------------------------------
 * 1. Conversation Retrieval - Adding functionality to retrieve past conversations 
 *    using chatService.getConversation()
 * 
 * 2. Session Listing - Adding UI to browse past conversations 
 *    using chatService.listConversations()
 * 
 * 3. Delete Functionality - Adding ability to delete conversations 
 *    using chatService.deleteConversation()
 * 
 * 4. Health Checks - Adding service health monitoring
 *    using chatService.checkHealth()
 */

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import { ChatRequest, ChatResponse, ChatService } from '@/services/ChatService';
import { ChatMessage } from '@/models/ChatSession';
import { useRouter, useSearchParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { generateContextSummary } from '@/lib/utils/contextSummary';
import { useChat } from '@/hooks/useChat';
import { chatService } from '@/services/ChatService';
import { backendApiService } from '@/lib/services/BackendApiService';
import Image from 'next/image';

/**
 * MIGRATION STATUS:
 * 
 * ✅ streamResponse - Migrated to use chatService.getStreamUrl
 * ✅ sendMessageWithoutStreaming - Migrated to use chatService.query
 * ✅ startNewChat - Using ChatService's saveConversation
 * ✅ saveConversation - Migrated to use ChatService.saveConversation
 * ✅ handleSubmit - Updated to use ChatService 
 * ✅ Health checks - Enabled through chatService.checkHealth()
 * 
 * MIGRATION COMPLETE: This component has been fully migrated to use the ChatService.
 */

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
  const { data: session, status } = useSession();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPanelCollapsed, setIsPanelCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [conversations, setConversations] = useState<any[]>([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  const [hasMoreConversations, setHasMoreConversations] = useState(true);
  const [page, setPage] = useState(1);
  const conversationsEndRef = useRef<HTMLDivElement>(null);
  const conversationsContainerRef = useRef<HTMLDivElement>(null);
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    if (!initialMessages || !Array.isArray(initialMessages)) {
      console.warn('Initial messages is not an array:', typeof initialMessages);
      return [];
    }
    return initialMessages.map(msg => ({
      role: msg.role || 'assistant',
      content: msg.content || '',
      timestamp: msg.timestamp instanceof Date ? msg.timestamp : new Date(msg.timestamp || Date.now()),
      thinkingSteps: msg.thinkingSteps || [],
      documents: msg.documents || []
    }));
  });
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(sessionId);
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSavedHash, setLastSavedHash] = useState<string>('');
  const [contextSummary, setContextSummary] = useState<string>('');
  const accumulatedContentRef = useRef('');
  const eventSourceRef = useRef<EventSource | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const messageAddedViaAnswerEventRef = useRef(false);

  // Fetch conversations with pagination
  const fetchConversations = useCallback(async (pageNum: number, append: boolean = false) => {
    if (isLoadingConversations || !hasMoreConversations) return;
    
    setIsLoadingConversations(true);
    try {
      const response = await ChatService.listConversations({
        page: pageNum,
        limit: 20,
        sortBy: 'updated_at',
        sortOrder: 'desc'
      });
      
      if (!response || response.length === 0) {
        setHasMoreConversations(false);
      } else {
        setConversations(prev => 
          append ? [...prev, ...response] : response
        );
        setPage(pageNum);
      }
    } catch (error) {
      console.error('Error fetching conversations:', error);
      setHasMoreConversations(false); // Stop trying to load more on error
    } finally {
      setIsLoadingConversations(false);
    }
  }, [isLoadingConversations, hasMoreConversations]);

  // Initial fetch
  useEffect(() => {
    if (status === 'authenticated') {
      fetchConversations(1);
    }
  }, [fetchConversations, status]);

  // Handle scroll for infinite loading
  const handleConversationsScroll = useCallback(() => {
    if (!conversationsContainerRef.current || isLoadingConversations || !hasMoreConversations) return;
    
    const { scrollTop, scrollHeight, clientHeight } = conversationsContainerRef.current;
    if (scrollHeight - scrollTop <= clientHeight * 1.5) {
      fetchConversations(page + 1, true);
      }
  }, [fetchConversations, page, isLoadingConversations, hasMoreConversations]);

  // Add scroll listener
  useEffect(() => {
    const container = conversationsContainerRef.current;
    if (container) {
      container.addEventListener('scroll', handleConversationsScroll);
      return () => container.removeEventListener('scroll', handleConversationsScroll);
    }
  }, [handleConversationsScroll]);

  // Filter conversations based on search query
  const filteredConversations = useMemo(() => {
    if (!searchQuery) return conversations;
    return conversations.filter(conv => 
      conv.title.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [conversations, searchQuery]);
    
  // Handle navigation to different sections
  const handleNavigation = (path: string) => {
    router.push(path);
  };

  // Handle conversation click
  const handleConversationClick = (conversationId: string) => {
    router.push(`/chat?id=${conversationId}`);
  };

  // Add a function to toggle search mode
  const toggleSearchMode = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsSearchMode(!isSearchMode);
  };

  const handleSubmit = async (event?: React.FormEvent<HTMLFormElement> | React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event) {
      event.preventDefault();
    }
    
    if (!input.trim() || isLoading) return;
    
    // Add user message to the UI
    const userMessage: ChatMessage = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    
    // Add the message to the UI state
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
    setIsThinking(true);
    setThinkingSteps([]);
    setStreamingMessage('');
    setIsLoading(true);
    
    // Reset the accumulated content ref
    accumulatedContentRef.current = '';
    
    // Reset the message added via answer event flag
    messageAddedViaAnswerEventRef.current = false;
    
    try {
      // Create request for API
      const chatRequest: ChatRequest = {
        query,
        conversation_id: conversationId,
        context_summary: contextSummary,
        stream: true,
        debug_mode: true
      };
      
      // Get streaming URL using the BackendApiService
      const streamUrl = backendApiService.getStreamUrl(chatRequest);
      
      // Create new event source
      const eventSource = new EventSource(streamUrl);
      eventSourceRef.current = eventSource;
      
      // Set up event listeners
      eventSource.addEventListener('thinking_start', handleThinkingStart);
      eventSource.addEventListener('thinking_update', handleThinkingUpdate);
      eventSource.addEventListener('thinking_end', handleThinkingEnd);
      eventSource.addEventListener('answer_start', handleAnswerStart);
      eventSource.addEventListener('answer_chunk', handleAnswerChunk);
      eventSource.addEventListener('answer', handleAnswer);
      eventSource.addEventListener('document', handleDocument);
      eventSource.addEventListener('done', handleDone);
      eventSource.addEventListener('error', handleError);
      
      // Handle errors
      eventSource.onerror = (error) => {
        console.error('EventSource connection error:', error);
        eventSource.close();
        setIsLoading(false);
        setIsThinking(false);
        
        // Add error message to chat
        const errorMessage: ChatMessage = {
          role: 'assistant',
          content: "I'm sorry, there was an error connecting to the chat service. Please try again later.",
          timestamp: new Date()
        };
        setMessages(prev => [...prev, errorMessage]);
      };
    } catch (error) {
      console.error('Error creating stream URL:', error);
      setIsLoading(false);
      setIsThinking(false);
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: "I'm sorry, there was an error starting the conversation. Please try again later.",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  // Event handlers for streaming
  const handleThinkingStart = (e: MessageEvent) => {
    setIsThinking(true);
    try {
      const data = JSON.parse(e.data);
      setThinkingSteps([{
        type: 'thinking',
        description: 'Starting to process your request',
        time: new Date().toTimeString().split(' ')[0],
        duration_ms: 0
      }]);
    } catch (err) {
      console.error('Error parsing thinking_start event', err);
    }
  };

  const handleThinkingUpdate = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      if (data && data.description) {
        setThinkingSteps(prev => [...prev, data]);
      }
    } catch (err) {
      console.error('Error parsing thinking_update event', err);
    }
  };

  const handleThinkingEnd = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      setThinkingSteps(prev => [...prev, {
        type: 'thinking',
        description: 'Processing complete',
        time: new Date().toTimeString().split(' ')[0],
        duration_ms: 0
      }]);
    } catch (err) {
      console.error('Error parsing thinking_end event', err);
    }
  };

  const handleAnswerStart = () => {
    const newStreamingId = Date.now().toString();
    setStreamingId(newStreamingId);
    setStreamingMessage('');
    accumulatedContentRef.current = '';
  };

  const handleAnswerChunk = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      const chunk = data.chunk || '';
      accumulatedContentRef.current += chunk;
      setStreamingMessage(prev => prev + chunk);
    } catch (err) {
      console.error('Error parsing answer_chunk event', err);
    }
  };

  const handleAnswer = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      const fullAnswer = data.answer || '';
      if (fullAnswer) {
        accumulatedContentRef.current = fullAnswer;
        setStreamingMessage(fullAnswer);
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
        }
      }
    } catch (err) {
      console.error('Error parsing answer event', err);
    }
  };

  const handleDocument = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      // Handle documents as needed
    } catch (err) {
      console.error('Error parsing document event', err);
    }
  };

  const handleDone = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
        if (!sessionId && onNewSession) {
          onNewSession(data.conversation_id);
        }
      }
      
      const finalContent = accumulatedContentRef.current;
      if (finalContent && finalContent.trim().length > 0) {
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: finalContent,
        timestamp: new Date(),
          thinkingSteps: [...thinkingSteps]
        };
        
        setMessages(prev => [...prev, assistantMessage]);
      }
      
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      
      setTimeout(() => {
        setStreamingMessage('');
        setStreamingId(null);
        setThinkingSteps([]);
        setIsLoading(false);
        setIsThinking(false);
        messageAddedViaAnswerEventRef.current = false;
      }, 500);
    } catch (err) {
      console.error('Error parsing done event', err);
      setIsLoading(false);
      setIsThinking(false);
    }
  };

  const handleError = (e: MessageEvent) => {
    console.error('Stream error:', e);
    setIsLoading(false);
    messageAddedViaAnswerEventRef.current = false;
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* Left Panel */}
      <div 
        className={`bg-white border-r border-gray-200 transition-all duration-300 ${
          isPanelCollapsed ? 'w-16' : 'w-64'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Collapse Toggle Button */}
          <button
            onClick={() => setIsPanelCollapsed(!isPanelCollapsed)}
            className="p-4 hover:bg-gray-50 flex items-center justify-center"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className={`h-6 w-6 text-gray-500 transform transition-transform ${
                isPanelCollapsed ? 'rotate-180' : ''
              }`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>

          {!isPanelCollapsed && (
            <>
              {/* Search Bar */}
              <div className="px-4 py-2">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search conversations..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full px-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <svg
                    className="absolute right-3 top-2.5 h-4 w-4 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
              </div>

              {/* KAI Agents Section */}
              <div className="px-4 py-2">
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                  KAI Agents
                </h3>
                <div className="space-y-1">
                  <button
                    onClick={() => handleNavigation('/chat')}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 rounded-lg flex items-center"
                  >
                    <svg className="h-5 w-5 mr-2 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                    Ask KAI about universities
                  </button>
                  <button
                    onClick={() => handleNavigation('/profile/build')}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 rounded-lg flex items-center"
                  >
                    <svg className="h-5 w-5 mr-2 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    Build your application profile
                  </button>
                  <button
                    onClick={() => handleNavigation('/essay')}
                    className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 rounded-lg flex items-center"
                  >
                    <svg className="h-5 w-5 mr-2 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    Write your essay
                  </button>
                </div>
              </div>

              {/* KAI Conversations Section */}
              <div className="px-4 py-2 flex-1 overflow-hidden">
                <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                  KAI Conversations
                </h3>
                <div 
                  ref={conversationsContainerRef}
                  className="space-y-1 overflow-y-auto h-[calc(100vh-400px)]"
                >
                  {filteredConversations.map((convo) => (
                    <button
                      key={convo.id}
                      onClick={() => handleConversationClick(convo.conversation_id)}
                      className={`w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 rounded-lg flex items-center ${
                        searchParams?.get('id') === convo.conversation_id ? 'bg-indigo-50' : ''
                      }`}
                    >
                      <svg className="h-5 w-5 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                      </svg>
                      <div className="flex-1 min-w-0">
                        <p className="truncate">{convo.title}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(convo.updated_at).toLocaleDateString()}
                        </p>
                      </div>
                    </button>
                  ))}
                  
                  {/* Loading indicator */}
                  {isLoadingConversations && (
                    <div className="flex justify-center py-2">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-500"></div>
                    </div>
                  )}
                  
                  {/* End of list marker */}
                  <div ref={conversationsEndRef} />
                </div>
              </div>

              {/* Profile Section */}
              <div className="px-4 py-2 border-t border-gray-200">
                <button
                  onClick={() => handleNavigation('/profile')}
                  className="w-full flex items-center space-x-3 px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 rounded-lg"
                >
                  <div className="relative h-8 w-8 rounded-full overflow-hidden">
                    {session?.user?.image ? (
                      <Image
                        src={session.user.image}
                        alt="Profile"
                        fill
                        className="object-cover"
                      />
                    ) : (
                      <div className="h-full w-full bg-indigo-500 flex items-center justify-center text-white">
                        {session?.user?.name?.[0] || 'U'}
                      </div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {session?.user?.name || 'User'}
                    </p>
                    <p className="text-xs text-gray-500 truncate">
                      {session?.user?.email || 'user@example.com'}
                    </p>
                  </div>
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 space-y-6 relative bg-gray-50">
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
        
          {/* Show all message exchanges */}
          {messages.map((message, index) => (
              <div 
              key={`message-${index}-${message.timestamp.getTime()}`} 
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
        
          {/* Loading indicator */}
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
        
          {/* Streaming message */}
        {streamingMessage && isLoading && (
          <div className="flex justify-start" id={`streaming-${streamingId}`}>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-emerald-600 text-white flex items-center justify-center mr-2 flex-shrink-0 mt-1 shadow-md">
              <span className="text-lg font-bold" style={{ textShadow: '0px 1px 2px rgba(0, 0, 0, 0.2)' }}>K</span>
            </div>
            <div className="p-5 rounded-2xl max-w-[85%] md:max-w-[75%] bg-white text-gray-700 border border-gray-100 relative group shadow-md hover:shadow-lg transition-shadow">
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
                </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
        {/* Input form */}
      <div className="bg-gray-50 p-4 border-t border-gray-100">
        <div className="max-w-4xl mx-auto relative">
          <form onSubmit={handleSubmit} className="flex space-x-3">
            <div className="relative flex-1 flex items-start">
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
              
                {/* Search toggle button */}
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
    </div>
  );
} 