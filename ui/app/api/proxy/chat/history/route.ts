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
    
    // Get conversation_id from URL params
    const url = new URL(request.url);
    const conversationId = url.searchParams.get('conversation_id');
    
    if (!conversationId) {
      return NextResponse.json(
        { error: 'conversation_id parameter is required' },
        { status: 400 }
      );
    }
    
    console.log(`Proxy: Fetching conversation history for ID ${conversationId}`);
    
    // Find the chat session by conversationId
    const chatSession = await ChatSession.findOne({ conversationId });
    
    if (!chatSession) {
      console.log(`Proxy: No chat session found for conversation ID ${conversationId}`);
      return NextResponse.json(
        { 
          conversation_id: conversationId,
          messages: [] 
        },
        { status: 200 }
      );
    }
    
    console.log(`Proxy: Found chat session with ${chatSession.messages.length} messages`);
    
    // Return the messages and conversation details
    return NextResponse.json({
      conversation_id: conversationId,
      messages: chatSession.messages,
      title: chatSession.title,
      created_at: chatSession.createdAt,
      updated_at: chatSession.updatedAt
    });
    
  } catch (error) {
    console.error('Proxy Error getting conversation history:', error);
    return NextResponse.json(
      { error: 'Failed to get conversation history' },
      { status: 500 }
    );
  }
} 