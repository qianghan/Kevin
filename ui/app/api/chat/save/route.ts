import { NextRequest, NextResponse } from 'next/server';
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
  try {
    // Parse request body
    const body = await req.json() as SaveRequest;
    const { conversation_id, title, messages, context_summary } = body;
    
    console.log('API: Save request received:', {
      conversation_id,
      title,
      message_count: messages?.length || 0,
      context_summary_length: context_summary?.length || 0,
      user_id: params.user?.id,
      headers: Object.fromEntries(req.headers.entries())
    });

    // Validate required fields - conversation_id is now optional
    if (!params.user?.id) {
      console.error('API: Missing user ID in session');
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Log the user session
    console.log('API: User session:', {
      user_id: params.user.id,
      user_email: params.user.email,
      user_role: params.user.role
    });

    // Use the ChatSessionService to save the session
    // conversation_id can be undefined now, and the service will generate one
    console.log('API: Attempting to save session...');
    const result = await ChatSessionService.saveSession(
      params.user.id,
      conversation_id,
      title,
      messages,
      context_summary
    );
    
    console.log('API: Session saved successfully:', result);
    return createSuccessResponse(result);
  } catch (error) {
    console.error('API: Error saving session:', {
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
      user_id: params.user?.id
    });
    return NextResponse.json({ 
      error: 'Failed to save session',
      details: error instanceof Error ? error.message : String(error)
    }, { status: 500 });
  }
}

// Export the handler with middleware protection
export const POST = createProtectedHandler(handleSave); 