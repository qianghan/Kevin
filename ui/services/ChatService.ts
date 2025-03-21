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
  conversation_id: string;
  answer?: string;
  response?: string;
  sources?: any[];
  thinking_steps?: any[];
  documents?: any[];
  duration_seconds?: number;
  processing_time?: number;
  is_cached?: boolean;
  cache_metadata?: {
    source?: string;
    similarity?: number;
    age?: number;
    lookup_time?: number;
  };
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

// Create a Next.js API client for database interactions
const apiClient = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Structured logging function with sensitive data redaction
const logAction = (methodName: string, params: any, component = 'ChatService') => {
  console.log(`${component}.${methodName} called with:`, 
    JSON.stringify(params, (key, value) => {
      // Truncate long string values and redact any sensitive data
      if (typeof value === 'string') {
        if (key.toLowerCase().includes('password') || 
            key.toLowerCase().includes('token') || 
            key.toLowerCase().includes('secret')) {
          return '***REDACTED***';
        }
        if (value.length > 100) {
          return value.substring(0, 100) + '...';
        }
      }
      return value;
    })
  );
};

// Standardized error handler
const handleError = (error: any, methodName: string): never => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    const status = axiosError.response?.status;
    const data = axiosError.response?.data;
    
    // Create a contextual error message
    const message = `Error in ${methodName}: ${axiosError.message}`;
    
    // Log with detailed context
    console.error(message, {
      timestamp: new Date().toISOString(),
      status,
      url: axiosError.config?.url,
      data: data || 'No response data',
      method: axiosError.config?.method?.toUpperCase(),
    });
    
    throw new ApiRequestError(message, status, data);
  } else {
    const message = `Error in ${methodName}: ${error instanceof Error ? error.message : String(error)}`;
    console.error(message, {
      timestamp: new Date().toISOString(),
      type: error instanceof Error ? error.constructor.name : typeof error
    });
    
    if (message.toLowerCase().includes('database') || message.toLowerCase().includes('db')) {
      throw new DatabaseError(message, error);
    }
    
    throw new ServiceError(message, error);
  }
};

// Add enhanced logging to API client
apiClient.interceptors.request.use(request => {
  console.log(`API Request [${request.method?.toUpperCase()}] ${request.url}`, {
    timestamp: new Date().toISOString(),
    params: request.params,
    // Redact any sensitive data in headers
    headers: { 
      ...request.headers, 
      Authorization: request.headers.Authorization ? '***' : undefined,
      Cookie: request.headers.Cookie ? '***' : undefined 
    }
  });
  return request;
});

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log(`API Response [${response.status}] ${response.config.url}`, {
      timestamp: new Date().toISOString(),
      status: response.status,
      dataSize: JSON.stringify(response.data).length,
    });
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      console.error('API Error Response:', {
        timestamp: new Date().toISOString(),
        url: error.config?.url,
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data,
      });
    } else if (error.request) {
      console.error('API No Response:', {
        timestamp: new Date().toISOString(),
        url: error.config?.url,
        message: error.message,
      });
    } else {
      console.error('API Request Setup Error:', {
        timestamp: new Date().toISOString(),
        message: error.message,
      });
    }
    return Promise.reject(error);
  }
);

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

// Retry mechanism with exponential backoff
const retry = async <T>(
  operation: () => Promise<T>,
  methodName: string,
  retries = MAX_RETRIES,
  delay = RETRY_DELAY
): Promise<T> => {
  try {
    return await operation();
  } catch (error) {
    // Only retry on network or server errors, not on client errors
    if (
      retries > 0 && 
      (
        !axios.isAxiosError(error) || 
        !error.response || 
        error.response.status >= 500 || 
        error.code === 'ECONNABORTED' || 
        error.code === 'ECONNRESET'
      )
    ) {
      console.warn(`Retrying ${methodName} after error: ${error instanceof Error ? error.message : String(error)}. Retries left: ${retries}`, {
        timestamp: new Date().toISOString()
      });
      
      // Wait with exponential backoff
      await new Promise(resolve => setTimeout(resolve, delay));
      
      // Retry with increased delay
      return retry(operation, methodName, retries - 1, delay * 2);
    }
    
    throw error;
  }
};

/**
 * ChatService - A service for interacting with the chat API and database
 */
export class ChatService {
  /**
   * Saves conversation to the database
   */
  async saveConversation(
    conversationId: string, 
    messages: ChatMessage[], 
    contextSummary: string,
    title?: string
  ): Promise<boolean> {
    logAction('saveConversation', { 
      conversationId, 
      messagesCount: messages.length,
      contextSummaryLength: contextSummary?.length || 0,
      title: title || 'Using default title' 
    });
    
    if (!conversationId) {
      console.error('Cannot save conversation: Missing conversation ID');
      return false;
    }
    
    if (!messages || messages.length === 0) {
      console.warn('Cannot save conversation: No messages to save');
      return false;
    }
    
    // Maximum number of retries for version conflicts
    const maxVersionRetries = 3;
    let retryCount = 0;
    
    const save = async (): Promise<boolean> => {
      try {
        // Create a default title from the first user message if none provided
        const derivedTitle = title || this.deriveTitle(messages);
        
        console.log('Attempting to save conversation:', {
          conversationId,
          title: derivedTitle,
          messageCount: messages.length,
          contextSummaryLength: contextSummary?.length || 0
        });
        
        const response = await apiClient.post('/api/chat/save', {
          conversation_id: conversationId,
          title: derivedTitle,
          messages,
          context_summary: contextSummary || ''
        });
        
        console.log('Save conversation response:', {
          status: response.status,
          data: response.data,
          conversationId,
          title: derivedTitle
        });
        
        return response.status === 200;
      } catch (error: any) {
        // Log detailed error information
        console.error('Error saving conversation:', {
          error: error instanceof Error ? error.message : String(error),
          status: error.response?.status,
          data: error.response?.data,
          conversationId,
          messageCount: messages.length,
          requestHeaders: error.config?.headers ? JSON.stringify(error.config.headers).substring(0, 200) : 'No headers',
          requestUrl: error.config?.url,
          requestMethod: error.config?.method,
          stack: error.stack ? error.stack.split('\n').slice(0, 5).join('\n') : 'No stack trace'
        });
        
        // Check if the error is a version conflict error
        const errorMsg = error?.message || String(error);
        const isVersionError = 
          errorMsg.includes('VersionError') || 
          errorMsg.includes('No matching document found for id') ||
          errorMsg.includes('version');
          
        if (isVersionError && retryCount < maxVersionRetries) {
          retryCount++;
          console.warn(`Version conflict detected, retrying save (${retryCount}/${maxVersionRetries})`, {
            timestamp: new Date().toISOString(),
            conversationId,
            error: errorMsg
          });
          
          // Wait before retrying to allow potential concurrent operations to complete
          await new Promise(resolve => setTimeout(resolve, 500 * retryCount));
          return save();
        }
        
        // For other errors or if we've exhausted retries, handle normally
        handleError(error, 'saveConversation');
        return false;
      }
    };
    
    return retry(() => save(), 'saveConversation');
  }
  
  /**
   * Derive a title from messages if none is provided
   */
  private deriveTitle(messages: ChatMessage[]): string {
    // Find the first user message to use as title
    const firstUserMessage = messages.find(msg => msg.role === 'user');
    
    if (firstUserMessage) {
      const content = firstUserMessage.content.trim();
      // Truncate and clean the title
      return content.length > 50 
        ? `${content.substring(0, 47)}...` 
        : content;
    }
    
    return 'New Chat';
  }
  
  /**
   * Retrieves a conversation by ID
   */
  async getConversation(conversationId: string): Promise<{
    messages: ChatMessage[];
    title: string;
    contextSummary: string;
    createdAt?: Date;
    updatedAt?: Date;
  } | null> {
    logAction('getConversation', { conversationId });
    
    try {
      const operation = async () => {
        const response = await apiClient.get(`/api/chat/history?conversation_id=${encodeURIComponent(conversationId)}`);
        
        // Check if the response data is a string (needs parsing)
        let data = response.data;
        if (typeof data === 'string') {
          try {
            data = JSON.parse(data);
          } catch (e) {
            console.error('Failed to parse response data string:', e);
          }
        }

        // Find the actual conversation data which might be nested
        let conversation;
        if (data?.data) {
          // Handle { success: true, data: { ... } } format
          conversation = data.data;
        } else if (data?.messages) {
          // Handle direct conversation object format
          conversation = data;
        } else if (typeof data === 'object' && !Array.isArray(data)) {
          // Just use the data object itself
          conversation = data;
        } else {
          console.warn('Unexpected response format from history endpoint:', {
            data: typeof data === 'object' ? JSON.stringify(data).substring(0, 200) : typeof data
          });
          return null;
        }

        // Ensure the messages property is an array
        if (!conversation.messages || !Array.isArray(conversation.messages)) {
          console.warn('Conversation has no messages or messages is not an array:', {
            messagesType: typeof conversation.messages
          });
          conversation.messages = [];
        }

        // Map the messages to ensure consistent format
        conversation.messages = conversation.messages.map((msg: any) => ({
          role: msg.role || 'assistant',
          content: msg.content || '',
          timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
          thinkingSteps: msg.thinkingSteps || [],
          documents: msg.documents || []
        }));
        
        console.log('Conversation retrieved successfully', {
          timestamp: new Date().toISOString(),
          conversationId,
          messagesCount: conversation.messages?.length || 0,
          title: conversation.title,
          // Log more details for debugging
          messageSample: conversation.messages.length > 0 ? 
            `${conversation.messages[0].role}: ${conversation.messages[0].content.substring(0, 50)}...` : 
            'No messages'
        });
        
        return {
          messages: conversation.messages,
          title: conversation.title || 'Untitled Chat',
          contextSummary: conversation.contextSummary || '',
          createdAt: conversation.createdAt ? new Date(conversation.createdAt) : undefined,
          updatedAt: conversation.updatedAt ? new Date(conversation.updatedAt) : undefined
        };
      };
      
      return await retry(operation, 'getConversation');
    } catch (error) {
      console.error('Failed to retrieve conversation', {
        timestamp: new Date().toISOString(),
        conversationId,
        error: error instanceof Error ? error.message : String(error)
      });
      
      // Return null so the UI can handle missing conversations gracefully
      return null;
    }
  }
  
  /**
   * List all conversations
   */
  async listConversations(options?: {
    search?: string;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
  }): Promise<Array<{
    id: string;
    title: string;
    conversation_id: string;
    created_at: Date;
    updated_at: Date;
  }>> {
    logAction('listConversations', { options });
    
    try {
      const operation = async () => {
        // Build query parameters
        const params = new URLSearchParams();
        if (options?.search) params.append('search', options.search);
        if (options?.sortBy) params.append('sortBy', options.sortBy);
        if (options?.sortOrder) params.append('sortOrder', options.sortOrder);
        
        const queryString = params.toString();
        const url = queryString ? `/api/chat/sessions?${queryString}` : '/api/chat/sessions';
        
        console.log(`Making API request to ${url}`);
        const response = await apiClient.get(url);
        
        // Check if the response data is a string (needs parsing)
        let data = response.data;
        if (typeof data === 'string') {
          try {
            data = JSON.parse(data);
          } catch (e) {
            console.error('Failed to parse response data string:', e);
          }
        }

        // Get the sessions array from the response
        let sessionsArray;
        if (data?.data?.sessions) {
          // Handle nested structure: { success: true, data: { sessions: [...] } }
          sessionsArray = data.data.sessions;
        } else if (data?.sessions) {
          // Handle structure: { sessions: [...] }
          sessionsArray = data.sessions;
        } else if (Array.isArray(data)) {
          // Handle direct array response
          sessionsArray = data;
        } else {
          console.warn('Unexpected response format from sessions endpoint:', {
            data: typeof response.data === 'object' ? JSON.stringify(response.data).substring(0, 200) : typeof response.data
          });
          return [];
        }
        
        if (!Array.isArray(sessionsArray)) {
          console.warn('Sessions data is not an array:', {
            sessionsType: typeof sessionsArray
          });
          return [];
        }
        
        // Process the sessions to ensure consistent format and field names
        const processedSessions = sessionsArray
          .map(session => {
            // Ensure we have an object to work with
            if (typeof session === 'string') {
              try {
                session = JSON.parse(session);
              } catch (e) {
                console.warn('Failed to parse session string:', e);
                return null;
              }
            }
            
            if (!session) return null;
            
            // MongoDB returns _id, we map it to id
            const id = session.id || session._id || '';
            
            // MongoDB uses conversationId, we need conversation_id
            const conversation_id = session.conversation_id || session.conversationId || '';
            
            // Handle dates - ensure they are proper Date objects
            let created_at, updated_at;
            
            try {
              created_at = new Date(session.created_at || session.createdAt || new Date());
            } catch (e) {
              created_at = new Date();
            }
            
            try {
              updated_at = new Date(session.updated_at || session.updatedAt || new Date());
            } catch (e) {
              updated_at = new Date();
            }
            
            // Return a standardized object
            return {
              id: typeof id === 'object' && id.toString ? id.toString() : String(id),
              title: session.title || 'Untitled Chat',
              conversation_id: typeof conversation_id === 'object' && conversation_id.toString ? 
                conversation_id.toString() : String(conversation_id),
              created_at,
              updated_at
            };
          })
          .filter((session): session is {
            id: string;
            title: string;
            conversation_id: string;
            created_at: Date;
            updated_at: Date;
          } => session !== null); // Use type predicate to filter out null values
        
        console.log('Processed sessions:', {
          count: processedSessions.length,
          sample: processedSessions.length > 0 ? JSON.stringify(processedSessions[0]).substring(0, 100) : null
        });
        
        return processedSessions;
      };
      
      return await retry(operation, 'listConversations');
    } catch (error) {
      console.error('Failed to list conversations', {
        timestamp: new Date().toISOString(),
        options,
        error: error instanceof Error ? error.message : String(error)
      });
      
      // Return empty array for graceful UI handling
      return [];
    }
  }
  
  /**
   * Deletes a conversation
   */
  async deleteConversation(conversationId: string): Promise<boolean> {
    logAction('deleteConversation', { conversationId });
    
    try {
      const operation = async () => {
        const response = await apiClient.delete(`/api/chat/sessions?id=${conversationId}`);
        
        console.log('Conversation deleted successfully', {
          timestamp: new Date().toISOString(),
          conversationId,
          status: response.status
        });
        
        return response.status === 200;
      };
      
      return await retry(operation, 'deleteConversation');
    } catch (error) {
      console.error('Failed to delete conversation', {
        timestamp: new Date().toISOString(),
        conversationId,
        error: error instanceof Error ? error.message : String(error)
      });
      
      // Return false for graceful UI handling
      return false;
    }
  }
  
  /**
   * Updates the title of a conversation
   */
  async updateConversationTitle(sessionId: string, title: string): Promise<boolean> {
    logAction('updateConversationTitle', { sessionId, title });
    
    try {
      const operation = async () => {
        const response = await apiClient.patch('/api/chat/sessions', {
          sessionId,
          title: title.trim() || 'Untitled Chat'
        });
        
        console.log('Conversation title updated successfully', {
          timestamp: new Date().toISOString(),
          sessionId,
          title,
          status: response.status
        });
        
        return response.data.success === true;
      };
      
      return await retry(operation, 'updateConversationTitle');
    } catch (error) {
      console.error('Failed to update conversation title', {
        timestamp: new Date().toISOString(),
        sessionId,
        title,
        error: error instanceof Error ? error.message : String(error)
      });
      
      // Return false for graceful UI handling
      return false;
    }
  }
  
  /**
   * Send a non-streaming chat query to the backend
   */
  async query(request: ChatRequest): Promise<ChatResponse> {
    logAction('query', {
      query: request.query,
      conversation_id: request.conversation_id,
      use_web_search: request.use_web_search,
      prefer_cache: request.prefer_cache,
      query_type: request.query_type
    });
    
    try {
      const operation = async () => {
        const startTime = Date.now();
        
        const response = await apiClient.post('/api/chat/query', {
          query: request.query,
          use_web_search: request.use_web_search || false,
          conversation_id: request.conversation_id,
          context_summary: request.context_summary || '',
          stream: false,
          prefer_cache: request.prefer_cache,
          query_type: request.query_type || 'complex'
        });
        
        const duration = Date.now() - startTime;
        
        console.log('Chat query completed', {
          timestamp: new Date().toISOString(),
          duration: `${duration}ms`,
          isCached: response.data.is_cached,
          conversationId: response.data.conversation_id
        });
        
        return response.data;
      };
      
      return await retry(operation, 'query');
    } catch (error) {
      // For chat queries, propagate the error so it can be handled by the UI
      return handleError(error, 'query');
    }
  }

  /**
   * Get URL for streaming chat
   */
  getStreamUrl(request: ChatRequest): string {
    logAction('getStreamUrl', {
      query: request.query && request.query.length > 30 ? 
        `${request.query.substring(0, 30)}...` : request.query,
      conversation_id: request.conversation_id
    });
    
    try {
      const baseUrl = '/api/chat/query/stream';
      const params = new URLSearchParams();
      
      if (request.query) {
        params.append('query', request.query);
      }
      
      if (request.conversation_id) {
        params.append('conversation_id', request.conversation_id);
      }
      
      if (request.use_web_search !== undefined) {
        params.append('use_web_search', request.use_web_search.toString());
      }
      
      if (request.query_type) {
        params.append('query_type', request.query_type);
      }
      
      if (request.prefer_cache !== undefined) {
        params.append('prefer_cache', request.prefer_cache.toString());
      }
      
      if (request.context_summary) {
        params.append('context_summary', request.context_summary);
      }
      
      if (request.debug_mode !== undefined) {
        params.append('debug_mode', request.debug_mode.toString());
      }
      
      const queryString = params.toString();
      const url = queryString ? `${baseUrl}?${queryString}` : baseUrl;
      
      console.log('Generated stream URL', {
        timestamp: new Date().toISOString(),
        url
      });
      
      return url;
    } catch (error) {
      console.error('Error generating stream URL', {
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : String(error),
        request
      });
      
      // Throw as this is a critical error
      throw new ServiceError(`Failed to generate stream URL: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  
  /**
   * Check the health of the chat service
   */
  async checkHealth(): Promise<{ 
    status: 'ok' | 'degraded' | 'down';
    message: string;
    details?: any;
  }> {
    logAction('checkHealth', {});
    
    try {
      const response = await apiClient.get('/api/health');
      return {
        status: 'ok',
        message: 'Chat service is healthy',
        details: response.data
      };
    } catch (error) {
      console.error('Health check failed', {
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : String(error)
      });
      
      return {
        status: 'down',
        message: `Chat service is unavailable: ${error instanceof Error ? error.message : String(error)}`
      };
    }
  }
}

// Export a singleton instance
export const chatService = new ChatService(); 