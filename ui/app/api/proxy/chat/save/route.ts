import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth/auth-options';
import dbConnect from '@/lib/db/connection';
import ChatSession, { ChatMessage } from '@/models/ChatSession';
import mongoose from 'mongoose';

// Define the request message structure
interface MessageInput {
  role: string;
  content: string;
  timestamp?: string | Date;
  thinkingSteps?: any[];
  documents?: any[];
}

export async function POST(request: NextRequest) {
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
    
    // Parse request body
    const body = await request.json();
    const { conversation_id, title, messages } = body;
    
    if (!conversation_id) {
      return NextResponse.json(
        { error: 'Conversation ID is required' },
        { status: 400 }
      );
    }
    
    // Get userId from session
    const userId = session.user.id;
    
    console.log(`Proxy: Saving conversation ${conversation_id} for user ${userId}`);
    
    // Check if a session with this conversationId already exists
    let chatSession = await ChatSession.findOne({ conversationId: conversation_id });
    
    if (chatSession) {
      console.log(`Proxy: Updating existing chat session: ${chatSession._id}`);
      // Update existing session
      chatSession.title = title || chatSession.title;
      
      // Only update messages if provided
      if (messages && Array.isArray(messages)) {
        console.log(`Proxy: Updating ${messages.length} messages`);
        chatSession.messages = messages.map((msg: MessageInput) => ({
          role: msg.role as 'user' | 'assistant' | 'system',
          content: msg.content,
          timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
          thinkingSteps: msg.thinkingSteps || [],
          documents: msg.documents || []
        }));
      }
      
      await chatSession.save();
      console.log('Proxy: Chat session updated successfully');
    } else {
      console.log('Proxy: Creating new chat session');
      // Create new session
      chatSession = await ChatSession.create({
        userId: new mongoose.Types.ObjectId(userId),
        conversationId: conversation_id,
        title: title || `Chat ${new Date().toLocaleString()}`,
        messages: messages ? messages.map((msg: MessageInput) => ({
          role: msg.role as 'user' | 'assistant' | 'system',
          content: msg.content,
          timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
          thinkingSteps: msg.thinkingSteps || [],
          documents: msg.documents || []
        })) : [],
        isActive: true
      });
      console.log(`Proxy: New chat session created: ${chatSession._id}`);
    }
    
    return NextResponse.json({
      success: true,
      session_id: chatSession._id,
      conversation_id: chatSession.conversationId
    });
    
  } catch (error) {
    console.error('Proxy Error saving chat session:', error);
    return NextResponse.json(
      { error: 'Failed to save chat session' },
      { status: 500 }
    );
  }
} 