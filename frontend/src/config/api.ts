/**
 * API Configuration
 * 
 * This file contains configuration for API endpoints.
 */

// Base API URL - will use the same host in development and relative path in production
export const API_BASE_URL = '/api';

// Chat API endpoints - updated to match the actual FastAPI backend paths
export const API_ENDPOINTS = {
  CHAT: {
    BASE: `${API_BASE_URL}/chat`,
    SESSIONS: `${API_BASE_URL}/chat/conversations`, // Changed from sessions to conversations
    MESSAGES: (sessionId: string) => `${API_BASE_URL}/chat/conversations/${sessionId}`,
    QUERY: `${API_BASE_URL}/chat/query`,
    QUERY_STREAM: `${API_BASE_URL}/chat/query/stream`,
    THINKING: (sessionId: string, messageId: string) => 
      `${API_BASE_URL}/chat/thinking/${messageId}`,
    SEARCH: `${API_BASE_URL}/search`,
    EXPORT: (sessionId: string) => `${API_BASE_URL}/chat/export/${sessionId}`
  },
  AUTH: {
    BASE: `${API_BASE_URL}/auth`,
    LOGIN: `${API_BASE_URL}/auth/login`,
    LOGOUT: `${API_BASE_URL}/auth/logout`,
    REGISTER: `${API_BASE_URL}/auth/register`,
    CURRENT_USER: `${API_BASE_URL}/auth/me`
  },
  HEALTH: {
    CHECK: `${API_BASE_URL}/health`
  }
};

// API request timeouts in milliseconds
export const API_TIMEOUTS = {
  DEFAULT: 30000,
  CHAT: 60000,
  FILE_UPLOAD: 120000
};

export default {
  API_BASE_URL,
  API_ENDPOINTS,
  API_TIMEOUTS
}; 