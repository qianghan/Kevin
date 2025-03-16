import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth/auth-options';
import dbConnect from '@/lib/db/connection';
import ChatSession from '@/models/ChatSession';
import mongoose from 'mongoose';

export async function GET(request: NextRequest) {
  try {
    // Get the session and check authentication
    const session = await getServerSession(authOptions);
    
    if (!session || !session.user) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }
    
    // Connect to the database
    await dbConnect();
    
    // Get userId from session
    const userId = session.user.id;
    
    // Get all active sessions for the user
    const chatSessions = await ChatSession.find({ 
      userId: new mongoose.Types.ObjectId(userId),
      isActive: true 
    })
    .sort({ updatedAt: -1 }) // Sort by most recent first
    .select('_id title conversationId createdAt updatedAt'); // Only select needed fields
    
    // Format the response
    const formattedSessions = chatSessions.map(session => ({
      id: session._id,
      title: session.title,
      conversation_id: session.conversationId,
      created_at: session.createdAt,
      updated_at: session.updatedAt
    }));
    
    return NextResponse.json({
      sessions: formattedSessions
    });
    
  } catch (error) {
    console.error('Error listing chat sessions:', error);
    return NextResponse.json(
      { error: 'Failed to list chat sessions' },
      { status: 500 }
    );
  }
} 