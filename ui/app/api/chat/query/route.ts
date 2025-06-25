import { NextRequest, NextResponse } from 'next/server';
import { backendApiService } from '@/lib/services/BackendApiService';

/**
 * Handle POST request to chat query endpoint
 */
export async function POST(request: NextRequest) {
  try {
    // Parse the request body
    const body = await request.json();
    
    console.log('API route handler: /api/chat/query received request', { 
      query: body.query, 
      stream: body.stream 
    });

    // Forward the request to the backend using the BackendApiService
    const result = await backendApiService.query(body);
    
    // Return the response directly to match frontend expectations
    return NextResponse.json(result);
  } catch (error) {
    console.error('Error in /api/chat/query:', error instanceof Error ? error.message : String(error));
    
    // Return an error response
    return NextResponse.json(
      { error: 'Error processing chat query', details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
} 