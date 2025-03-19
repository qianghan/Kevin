import { backendApiService } from '@/lib/services/BackendApiService';

// Re-export the ChatRequest and ChatResponse types for compatibility
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

// Custom error types
export class ApiError extends Error {
  status?: number;
  data?: any;
  
  constructor(message: string, status?: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export class NetworkError extends ApiError {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

export class AuthorizationError extends ApiError {
  constructor(message: string, status?: number, data?: any) {
    super(message, status, data);
    this.name = 'AuthorizationError';
  }
}

// Structured logging function
const logRequest = (methodName: string, params: any) => {
  console.log(`ApiChatService.${methodName} called with:`, 
    JSON.stringify(params, (key, value) => 
      // Truncate long string values in logs
      typeof value === 'string' && value.length > 100 
        ? value.substring(0, 100) + '...' 
        : value
    )
  );
};

/**
 * ApiChatService - A service for directly communicating with the FastAPI backend
 */
export class ApiChatService {
  /**
   * Send a direct query to the FastAPI backend
   */
  async query(request: ChatRequest): Promise<ChatResponse> {
    logRequest('query', { 
      query: request.query, 
      conversation_id: request.conversation_id,
      stream: request.stream,
      use_web_search: request.use_web_search
    });
    
    try {
      return await backendApiService.query({
        query: request.query,
        use_web_search: request.use_web_search || false,
        conversation_id: request.conversation_id,
        stream: request.stream || false,
        debug_mode: request.debug_mode || false,
        context_summary: request.context_summary || '',
        prefer_cache: request.prefer_cache,
        query_type: request.query_type || 'complex'
      });
    } catch (error) {
      console.error('ApiChatService.query error:', error);
      
      if (error instanceof Error) {
        throw new ApiError(`Query failed: ${error.message}`);
      }
      
      throw new ApiError('Query failed: Unknown error');
    }
  }
  
  /**
   * Get streaming URL directly from the backend
   */
  getBackendStreamUrl(request: ChatRequest): string {
    logRequest('getBackendStreamUrl', { 
      query: request.query, 
      conversation_id: request.conversation_id
    });
    
    try {
      return backendApiService.getStreamUrl({
        query: request.query,
        conversation_id: request.conversation_id,
        use_web_search: request.use_web_search,
        debug_mode: request.debug_mode,
        prefer_cache: request.prefer_cache,
        query_type: request.query_type,
        context_summary: request.context_summary
      });
    } catch (error) {
      console.error('Error generating stream URL:', error);
      throw new ApiError(`Failed to generate stream URL: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  
  /**
   * Get cache statistics from the backend
   */
  async getCacheStats(): Promise<any> {
    logRequest('getCacheStats', {});
    
    try {
      return await backendApiService.getCacheStats();
    } catch (error) {
      console.error('ApiChatService.getCacheStats error:', error);
      throw new ApiError(`Failed to get cache stats: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  
  /**
   * Clear the cache on the backend
   */
  async clearCache(): Promise<any> {
    logRequest('clearCache', {});
    
    try {
      return await backendApiService.clearCache();
    } catch (error) {
      console.error('ApiChatService.clearCache error:', error);
      throw new ApiError(`Failed to clear cache: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
  
  /**
   * Test connection to the backend API
   */
  async testBackendConnection(): Promise<{
    success: boolean;
    message: string;
  }> {
    logRequest('testBackendConnection', {});
    
    try {
      return await backendApiService.testConnection();
    } catch (error) {
      console.error('ApiChatService.testBackendConnection error:', error);
      return {
        success: false,
        message: `Connection test failed: ${error instanceof Error ? error.message : String(error)}`
      };
    }
  }
}

// Export a singleton instance
export const apiChatService = new ApiChatService(); 