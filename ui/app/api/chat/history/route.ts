import { NextRequest } from 'next/server';
import ChatSessionService from '@/lib/services/db/ChatSessionService';
import { createProtectedHandler, createSuccessResponse, createErrorResponse } from '@/lib/api/middleware';
import { ChatMessage } from '@/models/ChatSession';

/**
 * Handle GET request to retrieve chat history
 */
async function handleGetHistory(req: NextRequest, params: Record<string, any>) {
  // Get conversation ID from query parameters
  const conversationId = params.query.conversation_id;

  // Validate conversation ID
  if (!conversationId) {
    return createErrorResponse('Missing conversation_id parameter', 400);
  }

  // Get user ID from session
  const userId = params.user.id;
  
  console.log(`API: Retrieving conversation history for ID: ${conversationId}, user: ${userId}`);
  
  // Use the ChatSessionService to get the conversation
  const conversation = await ChatSessionService.getConversation(userId, conversationId);
  
  // If conversation not found, return 404
  if (!conversation) {
    console.log(`API: Conversation not found for ID: ${conversationId}`);
    return createErrorResponse('Conversation not found', 404);
  }
  
  // Format messages to ensure consistent structure
  const formattedMessages: ChatMessage[] = conversation.messages.map(msg => ({
    role: msg.role || 'assistant',
    content: msg.content || '',
    timestamp: msg.timestamp || new Date(),
    thinkingSteps: msg.thinkingSteps || [],
    documents: msg.documents || []
  }));
  
  // Create a properly formatted response
  const responseData = {
    messages: formattedMessages,
    title: conversation.title || 'Untitled Chat',
    contextSummary: conversation.contextSummary || '',
    createdAt: conversation.createdAt,
    updatedAt: conversation.updatedAt
  };
  
  console.log(`API: Successfully retrieved conversation with title: "${responseData.title}", ${responseData.messages.length} messages`);
  
  return createSuccessResponse(responseData);
}

// Export the handler with middleware protection
export const GET = createProtectedHandler(handleGetHistory); 