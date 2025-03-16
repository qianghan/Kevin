import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/auth-options';
import { NextResponse } from 'next/server';
import dbConnect from '@/lib/db/connection';
import ChatSession, { ChatMessage } from '@/models/ChatSession';
import mongoose from 'mongoose';

// Define the request message structure
interface MessageInput {
  role: string;
  content: string;
  timestamp?: Date | string;
  thinkingSteps?: any[];
  documents?: any[];
  context_summary?: string;
}

// Save chat session to database
export async function POST(request: Request) {
  // Check if user is authenticated
  const session = await getServerSession(authOptions);

  if (!session) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
  }

  try {
    // Connect to database
    await dbConnect();

    // Parse request body
    const body = await request.json();
    const { conversation_id, title, messages, context_summary } = body;
    
    console.log(`API: Save request received for conversation_id: ${conversation_id}, title: ${title}, message count: ${messages?.length || 0}`);

    // Validate conversation_id
    if (!conversation_id) {
      console.error('API: Missing conversation_id parameter');
      return NextResponse.json({ error: 'Missing conversation_id parameter' }, { status: 400 });
    }

    // Get user ID from session
    const userId = session.user.id;
    
    // Check if chat session already exists
    let chatSession = await ChatSession.findOne({
      userId: userId,
      conversationId: conversation_id
    });
    
    // Update existing chat session or create new one
    if (chatSession) {
      console.log(`API: Updating existing chat session for conversation_id: ${conversation_id}`);
      chatSession.title = title || chatSession.title;
      
      // Update context summary if provided
      if (context_summary) {
        chatSession.contextSummary = context_summary;
      }
      
      // Update messages if provided
      if (messages) {
        chatSession.messages = messages.map((msg: MessageInput) => ({
          role: msg.role as 'user' | 'assistant' | 'system',
          content: msg.content,
          timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
          thinkingSteps: msg.thinkingSteps || [],
          documents: msg.documents || []
        }));
      }
      
      // Save updated chat session
      await chatSession.save();
      console.log(`API: Chat session updated: ${chatSession._id}`);
    } else {
      console.log(`API: Creating new chat session for conversation_id: ${conversation_id}`);
      // Create new chat session
      chatSession = await ChatSession.create({
        userId: new mongoose.Types.ObjectId(userId),
        conversationId: conversation_id,
        title: title || 'New Chat',
        messages: messages ? messages.map((msg: MessageInput) => ({
          role: msg.role as 'user' | 'assistant' | 'system',
          content: msg.content,
          timestamp: msg.timestamp ? new Date(msg.timestamp) : new Date(),
          thinkingSteps: msg.thinkingSteps || [],
          documents: msg.documents || []
        })) : [],
        isActive: true,
        contextSummary: context_summary || ''
      });
      console.log(`API: New chat session created: ${chatSession._id}`);
    }
    
    // Return success response
    return NextResponse.json({
      success: true,
      sessionId: chatSession._id.toString(),
      conversationId: conversation_id
    });
  } catch (error) {
    console.error('API: Error saving chat session', error);
    return NextResponse.json({ error: 'Failed to save chat session' }, { status: 500 });
  }
} 