import { ChatMessage } from '@/models/ChatSession';
import axios, { AxiosError, AxiosResponse } from 'axios';

// Define types for chat requests and responses
export interface ChatRequest {
  query: string;
  use_web_search?: boolean;
  conversation_id?: string;
  context_summary?: string;
  stream?: boolean;
  debug_mode?: boolean;
  prefer_cache?: boolean;
  query_type?: 'factual' | 'complex';
}

export interface ChatResponse {
  answer: string;
  conversation_id: string;
  thinking_steps?: any[];
  documents?: any[];
  context_summary?: string;
  duration_seconds?: number;
}

// Error types for more detailed error handling
export class ServiceError extends Error {
  details?: any;
  
  constructor(message: string, details?: any) {
    super(message);
    this.name = 'ServiceError';
    this.details = details;
  }
}

export class DatabaseError extends ServiceError {
  constructor(message: string, details?: any) {
    super(message, details);
    this.name = 'DatabaseError';
  }
}

export class ApiRequestError extends ServiceError {
  status?: number;
  
  constructor(message: string, status?: number, details?: any) {
    super(message, details);
    this.name = 'ApiRequestError';
    this.status = status;
  }
}

// Create an axios instance with default config
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Helper function to log actions
const logAction = (action: string, data?: any) => {
  console.log(`ChatService.${action}`, data);
};

// Helper function to handle errors
const handleError = (error: any, action: string) => {
  console.error(`ChatService.${action} error:`, error);
  throw error;
};

// Helper function to retry operations
async function retry<T>(operation: () => Promise<T>, action: string, maxRetries = 3): Promise<T> {
  let lastError: any;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      console.warn(`Retry ${i + 1}/${maxRetries} for ${action} failed:`, error);
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
    }
  }
  
  throw lastError;
}

/**
 * ChatService - A service for interacting with the chat API and database
 */
export class ChatService {
  /**
   * Get URL for streaming chat
   */
  getStreamUrl(params: {
    query: string;
    conversation_id?: string;
    stream?: boolean;
    use_web_search?: boolean;
  }): string {
    // Create query string from params
    const queryParams = new URLSearchParams();
    
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        // Convert boolean to string
        if (typeof value === 'boolean') {
          queryParams.append(key, value.toString());
        } else if (typeof value === 'string') {
          queryParams.append(key, value);
        } else {
          // JSON stringify objects, arrays, etc.
          queryParams.append(key, JSON.stringify(value));
        }
      }
    }
    
    const queryString = queryParams.toString();
    const url = `/api/chat/query/stream${queryString ? `?${queryString}` : ''}`;
    
    console.log('Generated stream URL:', url);
    return url;
  }

  /**
   * Saves conversation to the database
   */
  static async saveConversation(
    conversationId: string,
    messages: ChatMessage[],
    contextSummary: string = '',
    title: string = 'New Chat'
  ): Promise<boolean> {
    logAction('saveConversation', { conversationId, messageCount: messages.length });
    
    try {
      const response = await apiClient.post('/chat/save', {
        conversation_id: conversationId,
        messages,
        context_summary: contextSummary,
        title
      });
      
      return response.data?.success || false;
    } catch (error) {
      handleError(error, 'saveConversation');
      return false;
    }
  }

  /**
   * Retrieves a conversation by ID
   */
  static async getConversation(conversationId: string): Promise<{
    messages: ChatMessage[];
    title: string;
    contextSummary: string;
    createdAt?: Date;
    updatedAt?: Date;
  } | null> {
    logAction('getConversation', { conversationId });
    
    try {
      const response = await apiClient.get(`/chat/history?conversation_id=${encodeURIComponent(conversationId)}`);
      
      if (!response.data || !response.data.data) {
        console.warn('No data in response from history endpoint');
        return null;
      }

      const conversation = response.data.data;
      
      // Ensure the messages property is an array
      if (!conversation.messages || !Array.isArray(conversation.messages)) {
        console.warn('Conversation has no messages or messages is not an array');
        conversation.messages = [];
      }

      // Map the messages to ensure consistent format
      const formattedMessages = conversation.messages.map((msg: any) => ({
        role: msg.role || 'assistant',
        content: msg.content || '',
        timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
        thinkingSteps: msg.thinkingSteps || [],
        documents: msg.documents || []
      }));
      
      return {
        messages: formattedMessages,
        title: conversation.title || 'Untitled Chat',
        contextSummary: conversation.contextSummary || '',
        createdAt: conversation.createdAt ? new Date(conversation.createdAt) : undefined,
        updatedAt: conversation.updatedAt ? new Date(conversation.updatedAt) : undefined
      };
    } catch (error) {
      handleError(error, 'getConversation');
      return null;
    }
  }

  /**
   * Send a non-streaming chat query to the backend
   */
  static async query(params: {
    query: string;
    conversation_id?: string;
    stream?: boolean;
  }): Promise<{
    answer: string;
    conversation_id: string;
    thinking_steps?: any[];
    documents?: any[];
    context_summary?: string;
  }> {
    logAction('query', params);
    
    try {
      const response = await apiClient.post('/chat/query', params);
      
      // The response is already in the correct format
      const data = response.data;
      
      if (!data) {
        throw new Error('Invalid response format from chat query');
      }
      
      // Validate required fields
      if (!data.answer || !data.conversation_id) {
        throw new Error('Missing required fields in chat response');
      }

      return data;
    } catch (error) {
      handleError(error, 'query');
      throw error;
    }
  }

  /**
   * Helper function to derive a title from messages
   */
  private static deriveTitle(messages: ChatMessage[]): string {
    // Find the first user message
    const firstUserMessage = messages.find(msg => msg.role === 'user');
    if (firstUserMessage) {
      // Use the first 50 characters of the first user message as the title
      return firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '');
    }
    return 'New Chat';
  }

  /**
   * List all conversations with optional search and sorting
   */
  static async listConversations(options?: {
    search?: string;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
    page?: number;
    limit?: number;
  }): Promise<{
    id: string;
    title: string;
    conversation_id: string;
    created_at: Date;
    updated_at: Date;
  }[]> {
    logAction('listConversations', options);
    
    try {
      const response = await apiClient.get('/chat/sessions', {
        params: {
          search: options?.search,
          sortBy: options?.sortBy || 'updated_at',
          sortOrder: options?.sortOrder || 'desc',
          page: options?.page || 1,
          limit: options?.limit || 20
        }
      });
      
      console.log('Raw response from sessions endpoint:', response.data);
      
      // Check if response has data
      if (!response.data) {
        console.warn('No data in response from sessions endpoint');
        return [];
      }

      // Handle the response structure from the backend
      const sessions = response.data.sessions || response.data.data?.sessions || [];

      if (!Array.isArray(sessions)) {
        console.warn('Sessions data is not an array:', sessions);
        return [];
      }

      const formattedSessions = sessions.map((session: any) => {
        console.log('Processing session:', session);
        return {
          id: session.id || session._id || '',
          title: session.title || 'Untitled Chat',
          conversation_id: session.conversation_id || session.conversationId || session.id || '',
          created_at: session.created_at ? new Date(session.created_at) : new Date(),
          updated_at: session.updated_at ? new Date(session.updated_at) : new Date()
        };
      });

      console.log('Formatted sessions:', formattedSessions);
      return formattedSessions;
    } catch (error) {
      console.error('Error in listConversations:', error);
      if (error instanceof Error) {
        console.error('Error details:', error.message);
      }
      handleError(error, 'listConversations');
      return [];
    }
  }
}

// Export a singleton instance
export const chatService = new ChatService(); 