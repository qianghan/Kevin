import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth/auth-options';
import dbConnect from '@/lib/db/connection';
import ChatSession from '@/models/ChatSession';
import mongoose from 'mongoose';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
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
    
    const conversationId = params.id;
    
    // Find the chat session by conversationId
    const chatSession = await ChatSession.findOne({ conversationId });
    
    if (!chatSession) {
      return NextResponse.json(
        { 
          conversation_id: conversationId,
          messages: [] 
        },
        { status: 200 }
      );
    }
    
    // Return the messages and conversation details
    return NextResponse.json({
      conversation_id: conversationId,
      messages: chatSession.messages,
      title: chatSession.title,
      created_at: chatSession.createdAt,
      updated_at: chatSession.updatedAt
    });
    
  } catch (error) {
    console.error('Error getting conversation:', error);
    return NextResponse.json(
      { error: 'Failed to get conversation' },
      { status: 500 }
    );
  }
} 