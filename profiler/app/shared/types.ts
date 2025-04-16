/**
 * Shared type definitions for frontend and backend communication
 */

// Base WebSocket message interface
export interface WebSocketMessage {
  type: string;
  data?: any;
  error?: string;
  timestamp?: string;
}

// Profile state specific message
export interface ProfileStateMessage extends WebSocketMessage {
  type: 'state_update';
  data: ProfileState;
}

// Profile state interface
export interface ProfileState {
  userId: string;
  status: 'idle' | 'processing' | 'completed' | 'error';
  progress: number;
  data?: Record<string, any>;
}

// Connection message
export interface ConnectedMessage extends WebSocketMessage {
  type: 'connected';
  session_id: string;
  message: string;
}

// Error message
export interface ErrorMessage extends WebSocketMessage {
  type: 'error';
  error: string;
}

// Document analysis message
export interface DocumentAnalysisMessage extends WebSocketMessage {
  type: 'analyze_document';
  data: {
    documentId: string;
    content?: string;
    url?: string;
  };
}

// Question message
export interface QuestionMessage extends WebSocketMessage {
  type: 'ask_question';
  data: {
    question: string;
    context?: string;
  };
}

// Recommendation message
export interface RecommendationMessage extends WebSocketMessage {
  type: 'get_recommendations';
  data: {
    profile_id?: string;
    count?: number;
  };
} 