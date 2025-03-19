import { NextRequest } from 'next/server';
import { backendApiService } from '@/lib/services/BackendApiService';
import { createSuccessResponse, createErrorResponse } from '@/lib/api/middleware';

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
    
    // Return the response
    return createSuccessResponse(result);
  } catch (error) {
    console.error('Error in /api/chat/query:', error instanceof Error ? error.message : String(error));
    
    // Return an error response
    return createErrorResponse(
      'Error processing chat query', 
      500, 
      { details: error instanceof Error ? error.message : String(error) }
    );
  }
} 