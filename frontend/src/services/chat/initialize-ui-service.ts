/**
 * UI Chat Service Initialization
 * 
 * This file initializes the chat service and makes it available globally
 * to enable integration between the frontend and backend chat services.
 */

import { IChatService } from '../../interfaces/services/chat.service';
import axios from 'axios';
import { API_ENDPOINTS, API_TIMEOUTS } from '../../config/api';

// Use the configured API endpoints
const CHAT_API = API_ENDPOINTS.CHAT;
const HEALTH_API = API_ENDPOINTS.HEALTH;

/**
 * Real Chat Service Implementation
 * Connects to the backend API for chat functionality
 */
class RealChatService implements IChatService {
  private axiosInstance = axios.create({
    baseURL: CHAT_API.BASE,
    timeout: API_TIMEOUTS.CHAT
  });

  private conversations = new Map();

  /**
   * Get all chat sessions
   */
  async getSessions() {
    try {
      // Use the query endpoint to get a list of all conversations
      const response = await this.axiosInstance.get(CHAT_API.SESSIONS);
      return response.data;
    } catch (error) {
      console.warn('Failed to get sessions, returning cached conversations:', error);
      // Return cached conversations if API fails
      return Array.from(this.conversations.values());
    }
  }

  /**
   * Get a specific chat session by ID
   */
  async getSession(sessionId: string) {
    try {
      // Try to get from API
      const response = await this.axiosInstance.get(`${CHAT_API.SESSIONS}/${sessionId}`);
      // Cache the conversation
      this.conversations.set(sessionId, response.data);
      return response.data;
    } catch (error) {
      console.warn(`Failed to get session ${sessionId}, using cached if available:`, error);
      // Return from cache if exists
      if (this.conversations.has(sessionId)) {
        return this.conversations.get(sessionId);
      }
      throw error;
    }
  }

  /**
   * Create a new chat session
   */
  async createSession(options?: any) {
    // Initialize a new session with a query
    const initialQuery = options?.initialQuery || "Hello";
    const useWebSearch = options?.useWebSearch || false;
    
    const response = await this.axiosInstance.post(CHAT_API.QUERY, {
      query: initialQuery,
      use_web_search: useWebSearch,
      stream: false
    });
    
    const session = {
      id: response.data.conversation_id,
      name: options?.name || "New Chat",
      messages: [
        {
          role: 'user',
          content: initialQuery
        },
        {
          role: 'assistant',
          content: response.data.answer,
          thinking_steps: response.data.thinking_steps || []
        }
      ],
      created_at: new Date().toISOString()
    };
    
    // Cache the session
    this.conversations.set(session.id, session);
    
    return session;
  }

  /**
   * Update a chat session
   */
  async updateSession(sessionId: string, updates: any) {
    // Get the existing session
    let session = this.conversations.get(sessionId);
    
    if (!session) {
      try {
        session = await this.getSession(sessionId);
      } catch (error) {
        throw new Error(`Session ${sessionId} not found and could not be retrieved`);
      }
    }
    
    // Apply updates
    const updatedSession = {
      ...session,
      ...updates,
      id: sessionId // Ensure ID doesn't change
    };
    
    // Cache the updated session
    this.conversations.set(sessionId, updatedSession);
    
    return updatedSession;
  }

  /**
   * Delete a chat session
   */
  async deleteSession(sessionId: string) {
    // Remove from cache
    this.conversations.delete(sessionId);
    
    // No specific delete endpoint in the API, so we'll just report success
    return true;
  }

  /**
   * Send a message in a chat session
   */
  async sendMessage(sessionId: string, content: string, options?: any) {
    // Get the session if it exists
    let session = this.conversations.get(sessionId);
    
    if (!session) {
      try {
        session = await this.getSession(sessionId);
      } catch (error) {
        console.warn(`Session ${sessionId} not found, will create a new one`);
        // Create a new session
        session = {
          id: sessionId,
          name: "New Chat",
          messages: [],
          created_at: new Date().toISOString()
        };
      }
    }
    
    // Add user message to the session
    session.messages.push({
      role: 'user',
      content: content
    });
    
    // Send the query to the API
    const useWebSearch = options?.useWebSearch || false;
    const enableThinkingSteps = options?.enableThinkingSteps || false;
    
    const response = await this.axiosInstance.post(CHAT_API.QUERY, {
      query: content,
      use_web_search: useWebSearch,
      conversation_id: sessionId,
      stream: false
    });
    
    // Add assistant response to the session
    session.messages.push({
      role: 'assistant',
      content: response.data.answer,
      thinking_steps: enableThinkingSteps ? (response.data.thinking_steps || []) : []
    });
    
    // Update the cache
    this.conversations.set(sessionId, session);
    
    return session;
  }

  /**
   * Send a message with attachments in a chat session
   */
  async sendMessageWithAttachments(sessionId: string, content: string, attachments: any[], options?: any) {
    // Not fully implemented in backend yet, so fallback to regular sendMessage
    console.warn('Attachments not yet supported by backend API, sending regular message');
    return this.sendMessage(sessionId, content, options);
  }

  /**
   * Get thinking steps for a message
   */
  async getThinkingSteps(sessionId: string, messageId: string) {
    try {
      // Try to get from API if available
      const response = await this.axiosInstance.get(CHAT_API.THINKING(sessionId, messageId));
      return response.data;
    } catch (error) {
      console.warn(`Failed to get thinking steps for message ${messageId}:`, error);
      // Get from session cache if available
      const session = this.conversations.get(sessionId);
      if (session) {
        const message = session.messages.find(m => m.id === messageId);
        if (message && message.thinking_steps) {
          return message.thinking_steps;
        }
      }
      return []; // Return empty array if not found
    }
  }

  /**
   * Search messages across all sessions
   */
  async searchMessages(query: string) {
    // Use the search endpoint if available
    try {
      const response = await axios.get(CHAT_API.SEARCH, {
        params: { query }
      });
      return response.data;
    } catch (error) {
      console.warn('Search API not available, searching cached sessions:', error);
      
      // Fallback to searching cached sessions
      const results = [];
      this.conversations.forEach(session => {
        session.messages.forEach(message => {
          if (message.content.toLowerCase().includes(query.toLowerCase())) {
            results.push({
              session_id: session.id,
              message: message
            });
          }
        });
      });
      
      return {
        query,
        results,
        count: results.length
      };
    }
  }

  /**
   * Export a session to a specific format
   */
  async exportSession(sessionId: string, format: 'json' | 'text' | 'markdown' | 'pdf') {
    // Get the session
    let session = this.conversations.get(sessionId);
    
    if (!session) {
      try {
        session = await this.getSession(sessionId);
      } catch (error) {
        throw new Error(`Session ${sessionId} not found and could not be retrieved`);
      }
    }
    
    // For now, just return the session data as JSON
    if (format === 'json') {
      return session;
    }
    
    // For text/markdown, format the conversation
    if (format === 'text' || format === 'markdown') {
      let output = `# Conversation: ${session.name}\n\n`;
      
      session.messages.forEach(message => {
        const role = message.role === 'user' ? 'User' : 'Kevin';
        output += `## ${role}\n\n${message.content}\n\n`;
      });
      
      return output;
    }
    
    // PDF not supported yet
    if (format === 'pdf') {
      throw new Error('PDF export not yet supported');
    }
    
    throw new Error(`Unsupported format: ${format}`);
  }
}

/**
 * Initialize the UI Chat Service and register it globally
 */
export function initializeUIChatService() {
  try {
    // Create the service instance
    const chatService = new RealChatService();
    
    // Test connectivity to the API
    checkApiConnectivity(chatService).then(isConnected => {
      if (!isConnected) {
        console.warn('Chat API connectivity check failed - service may not function properly');
      } else {
        console.log('Chat API connectivity check successful');
      }
    });
    
    // Register the service in the global scope
    if (typeof window !== 'undefined') {
      // Create the KAI_UI namespace if it doesn't exist
      (window as any).KAI_UI = (window as any).KAI_UI || {};
      (window as any).KAI_UI.services = (window as any).KAI_UI.services || {};
      
      // Register the chat service globally
      (window as any).KAI_UI.services.chat = chatService;
      
      console.log('UI Chat Service initialized and registered globally');
    }
    
    return chatService;
  } catch (error) {
    console.error('Failed to initialize UI Chat Service:', error);
    throw error;
  }
}

/**
 * Check API connectivity by making a simple request
 */
async function checkApiConnectivity(service: RealChatService): Promise<boolean> {
  try {
    // Try several potential health endpoints
    try {
      // Try the specific API health endpoint
      await axios.get(HEALTH_API.CHECK);
      return true;
    } catch (firstError) {
      try {
        // Try the root API health endpoint
        await axios.get('/api/health');
        return true;
      } catch (secondError) {
        try {
          // Try the chat query endpoint directly
          await service['axiosInstance'].get('/query');
          return true;
        } catch (thirdError) {
          // As a last resort, just check if the API docs are accessible
          await axios.get('/docs');
          return true;
        }
      }
    }
  } catch (error) {
    console.warn('Chat API connectivity check failed:', error);
    return false;
  }
}

export default initializeUIChatService; 