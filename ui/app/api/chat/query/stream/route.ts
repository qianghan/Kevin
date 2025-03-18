import { NextRequest } from 'next/server';

// Define the base URL for Kevin API
const KEVIN_API_URL = process.env.NEXT_PUBLIC_KEVIN_API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    // Get query parameters
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('query');
    const use_web_search = searchParams.get('use_web_search') === 'true';
    const conversation_id = searchParams.get('conversation_id');
    const context_summary = searchParams.get('context_summary');
    
    console.log('API route handler: /api/chat/query/stream received request', { 
      query,
      use_web_search,
      conversation_id
    });

    // Construct the backend URL
    const params = new URLSearchParams();
    if (query) params.append('query', query);
    if (use_web_search) params.append('use_web_search', 'true');
    if (conversation_id) params.append('conversation_id', conversation_id);
    if (context_summary) params.append('context_summary', context_summary);

    const backendUrl = `${KEVIN_API_URL}/api/chat/query/stream?${params.toString()}`;
    
    // Set up headers for server-sent events
    const headers = {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    };

    // Create a fetch request to the backend
    const backendResponse = await fetch(backendUrl, {
      headers: {
        'Accept': 'text/event-stream',
      },
    });

    // Return the response as a stream
    return new Response(backendResponse.body, {
      headers,
      status: backendResponse.status,
    });
  } catch (error: any) {
    console.error('Error in /api/chat/query/stream:', error.message);
    
    // Return an error response as SSE
    const errorStream = new ReadableStream({
      start(controller) {
        controller.enqueue(`event: error\ndata: ${JSON.stringify({ error: error.message })}\n\n`);
        controller.close();
      },
    });
    
    return new Response(errorStream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  }
} 