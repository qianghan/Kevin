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
    
    // Get search and sort parameters from URL
    const searchParams = request.nextUrl.searchParams;
    const searchQuery = searchParams.get('search');
    const sortBy = searchParams.get('sortBy') || 'updatedAt'; // Default sort by updatedAt
    const sortOrder = searchParams.get('sortOrder') === 'asc' ? 1 : -1; // Default sort order is descending

    // Build the query
    const query: any = { 
      userId: new mongoose.Types.ObjectId(userId),
      isActive: true 
    };

    // Add title search if query parameter is provided
    if (searchQuery) {
      query.title = { $regex: searchQuery, $options: 'i' }; // Case-insensitive search
    }
    
    // Create sort object
    const sort: any = {};
    sort[sortBy === 'createdAt' ? 'createdAt' : 'updatedAt'] = sortOrder;
    
    // Get all active sessions for the user with filtering and sorting
    const chatSessions = await ChatSession.find(query)
      .sort(sort)
      .select('_id title conversationId createdAt updatedAt');
    
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

// PATCH endpoint to update session title
export async function PATCH(request: NextRequest) {
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
    
    // Get request body
    const body = await request.json();
    const { sessionId, title } = body;
    
    if (!sessionId || !title) {
      return NextResponse.json(
        { error: 'Session ID and title are required' },
        { status: 400 }
      );
    }
    
    // Find the session and verify ownership
    const chatSession = await ChatSession.findOne({
      _id: sessionId,
      userId: new mongoose.Types.ObjectId(userId),
      isActive: true
    });
    
    if (!chatSession) {
      return NextResponse.json(
        { error: 'Session not found or access denied' },
        { status: 404 }
      );
    }
    
    // Update the title
    chatSession.title = title;
    await chatSession.save();
    
    return NextResponse.json({
      success: true,
      session: {
        id: chatSession._id,
        title: chatSession.title,
        conversation_id: chatSession.conversationId,
        created_at: chatSession.createdAt,
        updated_at: chatSession.updatedAt
      }
    });
    
  } catch (error) {
    console.error('Error updating chat session:', error);
    return NextResponse.json(
      { error: 'Failed to update chat session' },
      { status: 500 }
    );
  }
}

// DELETE endpoint to soft delete a session
export async function DELETE(request: NextRequest) {
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
    
    // Get sessionId from the URL
    const searchParams = request.nextUrl.searchParams;
    const sessionId = searchParams.get('id');
    
    if (!sessionId) {
      return NextResponse.json(
        { error: 'Session ID is required' },
        { status: 400 }
      );
    }
    
    // Find the session and verify ownership
    const chatSession = await ChatSession.findOne({
      _id: sessionId,
      userId: new mongoose.Types.ObjectId(userId),
      isActive: true
    });
    
    if (!chatSession) {
      return NextResponse.json(
        { error: 'Session not found or access denied' },
        { status: 404 }
      );
    }
    
    // Soft delete by setting isActive to false
    chatSession.isActive = false;
    await chatSession.save();
    
    return NextResponse.json({
      success: true,
      message: 'Session successfully deleted'
    });
    
  } catch (error) {
    console.error('Error deleting chat session:', error);
    return NextResponse.json(
      { error: 'Failed to delete chat session' },
      { status: 500 }
    );
  }
} 