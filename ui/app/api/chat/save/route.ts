import { NextRequest } from 'next/server';
import ChatSessionService from '@/lib/services/db/ChatSessionService';
import { createProtectedHandler, createSuccessResponse } from '@/lib/api/middleware';
import { ChatMessage } from '@/models/ChatSession';

interface SaveRequest {
  conversation_id: string;
  title?: string;
  messages?: ChatMessage[];
  context_summary?: string;
}

/**
 * Handle POST request to save a chat session
 */
async function handleSave(req: NextRequest, params: Record<string, any>) {
  // Parse request body
  const body = await req.json() as SaveRequest;
  const { conversation_id, title, messages, context_summary } = body;
  
  console.log(`API: Save request received for conversation_id: ${conversation_id}, title: ${title}, message count: ${messages?.length || 0}`);

  // Get user ID from session
  const userId = params.user.id;
  
  // Use the ChatSessionService to save the session
  const result = await ChatSessionService.saveSession(
    userId,
    conversation_id,
    title,
    messages,
    context_summary
  );
  
  return createSuccessResponse(result);
}

// Export the handler with middleware protection
export const POST = createProtectedHandler(handleSave); 