import { z } from 'zod';
import type { WebSocketMessage } from '../../../shared/types';

// Profile state schema
export const profileStateSchema = z.object({
  userId: z.string(),
  status: z.enum(['idle', 'processing', 'completed', 'error']),
  progress: z.number().min(0).max(100),
  data: z.record(z.any()).optional()
});

// Base WebSocket message schema
export const webSocketMessageSchema = z.object({
  type: z.string(),
  data: z.any().optional(),
  error: z.string().optional(),
  timestamp: z.string().optional()
});

// State update message schema
export const stateUpdateMessageSchema = webSocketMessageSchema.extend({
  type: z.literal('state_update'),
  data: profileStateSchema
});

// Connected message schema
export const connectedMessageSchema = webSocketMessageSchema.extend({
  type: z.literal('connected'),
  session_id: z.string(),
  message: z.string()
});

// Error message schema
export const errorMessageSchema = webSocketMessageSchema.extend({
  type: z.literal('error'),
  error: z.string()
});

// Document analysis message schema
export const documentAnalysisMessageSchema = webSocketMessageSchema.extend({
  type: z.literal('analyze_document'),
  data: z.object({
    documentId: z.string(),
    content: z.string().optional(),
    url: z.string().url().optional()
  })
});

// Question message schema
export const questionMessageSchema = webSocketMessageSchema.extend({
  type: z.literal('ask_question'),
  data: z.object({
    question: z.string(),
    context: z.string().optional()
  })
});

// Recommendation message schema
export const recommendationMessageSchema = webSocketMessageSchema.extend({
  type: z.literal('get_recommendations'),
  data: z.object({
    profile_id: z.string().optional(),
    count: z.number().positive().optional()
  })
});

// Map of message types to their schemas
export const messageSchemas: Record<string, z.Schema> = {
  'state_update': stateUpdateMessageSchema,
  'connected': connectedMessageSchema,
  'error': errorMessageSchema,
  'analyze_document': documentAnalysisMessageSchema,
  'ask_question': questionMessageSchema,
  'get_recommendations': recommendationMessageSchema
};

/**
 * Validate a message against its schema
 * @param message The message to validate
 * @param schema The schema to validate against
 * @returns The validated message
 * @throws If validation fails
 */
export const validateMessage = <T>(message: unknown, schema: z.Schema<T>): T => {
  return schema.parse(message);
};

/**
 * Validate a message based on its type
 * @param message The message to validate
 * @returns The validated message
 * @throws If validation fails
 */
export const validateMessageByType = (message: WebSocketMessage): WebSocketMessage => {
  const schema = messageSchemas[message.type];
  if (!schema) {
    throw new Error(`No schema found for message type: ${message.type}`);
  }
  return validateMessage(message, schema);
}; 