import { NextRequest, NextResponse } from 'next/server';
import { backendApiService } from '@/lib/services/BackendApiService';

/**
 * Streaming chat API route handler
 * This is a passthrough to the backend streaming API
 */
export async function GET(request: NextRequest) {
  try {
    // Get all query parameters from the request URL
    const searchParams = request.nextUrl.searchParams;
    const params: Record<string, string> = {};
    
    // Extract all parameters
    for (const [key, value] of searchParams.entries()) {
      params[key] = value;
    }
    
    // Log the streaming request
    console.log('API route: Streaming request received', {
      query: params.query ? `${params.query.substring(0, 30)}...` : undefined,
      conversation_id: params.conversation_id
    });
    
    // Get the streaming URL from BackendApiService
    const backendUrl = backendApiService.getStreamUrl(params);
    
    // Create the streaming response
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Accept': 'text/event-stream',
      },
    });
    
    // Check if the response is ok
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend streaming error:', response.status, errorText);
      return NextResponse.json(
        { error: 'Backend streaming error', details: errorText },
        { status: response.status }
      );
    }
    
    // Forward the streaming response
    return new NextResponse(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Error in streaming API route:', error instanceof Error ? error.message : String(error));
    
    // Return error as a normal JSON response since we can't stream an error
    return NextResponse.json(
      { error: 'Streaming error', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
} 