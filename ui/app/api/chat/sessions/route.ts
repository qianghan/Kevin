import { NextRequest } from 'next/server';
import ChatSessionService from '@/lib/services/db/ChatSessionService';
import { 
  createProtectedHandler, 
  createSuccessResponse, 
  createErrorResponse 
} from '@/lib/api/middleware';

/**
 * Handle GET request to list chat sessions
 */
async function handleListSessions(req: NextRequest, params: Record<string, any>) {
  // Get user ID from session
  const userId = params.user.id;
  
  // Get search and sort parameters from query
  const searchQuery = params.query.search;
  const sortBy = params.query.sortBy || 'updatedAt'; // Default sort by updatedAt
  const sortOrder = params.query.sortOrder === 'asc' ? 'asc' : 'desc'; // Default sort order is descending
  
  // Use the ChatSessionService to list conversations
  const sessionsFromDb = await ChatSessionService.listConversations(
    userId,
    {
      search: searchQuery,
      sortBy,
      sortOrder
    }
  );
  
  // Transform sessions to ensure consistent structure
  const sessions = sessionsFromDb.map((session: any) => {
    // Handle ObjectId conversion to string
    const id = session._id?.toString() || session.id?.toString() || '';
    
    // Handle conversation ID field which might be in different formats
    const conversation_id = session.conversationId?.toString() || session.conversation_id?.toString() || '';
    
    // Handle dates in ISO format
    let created_at, updated_at;
    
    try {
      created_at = session.createdAt instanceof Date ? 
        session.createdAt.toISOString() : 
        new Date(session.createdAt || session.created_at).toISOString();
    } catch (e) {
      created_at = new Date().toISOString();
    }
    
    try {
      updated_at = session.updatedAt instanceof Date ? 
        session.updatedAt.toISOString() : 
        new Date(session.updatedAt || session.updated_at).toISOString();
    } catch (e) {
      updated_at = new Date().toISOString();
    }
    
    return {
      id,
      title: session.title || 'Untitled Chat',
      conversation_id,
      created_at,
      updated_at
    };
  });
  
  // Return with consistent response structure
  return createSuccessResponse({ sessions });
}

/**
 * Handle DELETE request to delete a chat session
 */
async function handleDeleteSession(req: NextRequest, params: Record<string, any>) {
  // Get session ID from query parameters
  const sessionId = params.query.id;
  
  // Validate session ID
  if (!sessionId) {
    return createErrorResponse('Missing session ID', 400);
  }
  
  // Get user ID from session
  const userId = params.user.id;
  
  // Use the ChatSessionService to delete the conversation
  const result = await ChatSessionService.deleteConversation(userId, sessionId);
  
  if (!result.success) {
    return createErrorResponse(result.message, 404);
  }
  
  return createSuccessResponse({ message: result.message });
}

/**
 * Handle PATCH request to update a chat session title
 */
async function handleUpdateSession(req: NextRequest, params: Record<string, any>) {
  // Parse request body
  const body = await req.json();
  const { sessionId, title } = body;
  
  // Validate required parameters
  if (!sessionId || !title) {
    return createErrorResponse('Missing required parameters: sessionId and title', 400);
  }
  
  // Get user ID from session
  const userId = params.user.id;
  
  // Use the ChatSessionService to update the title
  const result = await ChatSessionService.updateConversationTitle(
    userId,
    sessionId,
    title
  );
  
  if (!result.success) {
    return createErrorResponse(result.message, 404);
  }
  
  return createSuccessResponse({ success: true, message: result.message });
}

// Export the handlers with middleware protection
export const GET = createProtectedHandler(handleListSessions);
export const DELETE = createProtectedHandler(handleDeleteSession);
export const PATCH = createProtectedHandler(handleUpdateSession); 