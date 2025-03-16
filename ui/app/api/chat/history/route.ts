import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth/auth-options';
import { NextResponse } from 'next/server';
import dbConnect from '@/lib/db/connection';
import ChatSession from '@/models/ChatSession';

// Get chat history for a specific conversation
export async function GET(request: Request) {
  try {
    // Ensure the user is authenticated
    const session = await getServerSession(authOptions);
    if (!session) {
      return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
    }

    // Connect to the database
    await dbConnect();

    // Get the conversation_id from the URL
    const url = new URL(request.url);
    const conversation_id = url.searchParams.get('conversation_id');

    // Validate the conversation_id
    if (!conversation_id) {
      console.error('API: Missing conversation_id parameter');
      return NextResponse.json({ error: 'Missing conversation_id parameter' }, { status: 400 });
    }

    console.log(`API: Fetching chat history for conversation_id: ${conversation_id}`);

    // Get the user's ID from the session
    const userId = session.user.id;

    // Find the chat session
    const chatSession = await ChatSession.findOne({
      userId,
      conversationId: conversation_id
    });

    // If no session is found, return an empty message array
    if (!chatSession) {
      console.log(`API: No chat session found for conversation_id: ${conversation_id}`);
      return NextResponse.json({ 
        messages: [],
        title: 'New Chat',
        contextSummary: ''
      });
    }

    console.log(`API: Found chat session with ${chatSession.messages.length} messages`);

    // Return the chat session data
    return NextResponse.json({
      messages: chatSession.messages || [],
      title: chatSession.title || 'Chat History',
      createdAt: chatSession.createdAt,
      updatedAt: chatSession.updatedAt,
      contextSummary: chatSession.contextSummary || ''
    });
  } catch (error) {
    console.error('API: Error fetching chat history', error);
    return NextResponse.json({ error: 'Failed to fetch chat history' }, { status: 500 });
  }
} 