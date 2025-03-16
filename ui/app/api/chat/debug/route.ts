import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth/auth-options';
import dbConnect from '@/lib/db/connection';
import ChatSession from '@/models/ChatSession';

export async function GET(request: NextRequest) {
  try {
    // Get the session and check authentication
    const session = await getServerSession(authOptions);
    
    if (!session || !session.user || !session.user.id) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }
    
    // For security, only allow debug access to specific users
    // Remove this condition to allow any logged-in user to see their own sessions
    // (This is a public debug endpoint but it only shows the current user's sessions)
    
    // Connect to the database
    await dbConnect();
    
    // Get all chat sessions for the current user
    const userId = session.user.id;
    console.log(`Debug: Fetching all chat sessions for user ${userId}`);
    
    const chatSessions = await ChatSession.find({ userId });
    console.log(`Debug: Found ${chatSessions.length} chat sessions`);
    
    // Format sessions for response
    const formattedSessions = chatSessions.map(session => ({
      id: session._id ? session._id.toString() : null,
      conversation_id: session.conversationId,
      title: session.title,
      message_count: session.messages.length,
      is_active: session.isActive,
      created_at: session.createdAt,
      updated_at: session.updatedAt,
    }));
    
    return NextResponse.json({
      user_id: userId,
      session_count: chatSessions.length,
      sessions: formattedSessions
    });
    
  } catch (error) {
    console.error('Debug API Error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch debug information', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
} 