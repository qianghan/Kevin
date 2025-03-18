import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

// Define the base URL for Kevin API
const KEVIN_API_URL = process.env.NEXT_PUBLIC_KEVIN_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Parse the request body
    const body = await request.json();
    
    console.log('API route handler: /api/chat/query received request', { 
      query: body.query, 
      stream: body.stream 
    });

    // Forward the request to the backend
    const response = await axios.post(`${KEVIN_API_URL}/api/chat/query`, body, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Return the response
    return NextResponse.json(response.data);
  } catch (error: any) {
    console.error('Error in /api/chat/query:', error.message);
    
    // Return an error response
    return NextResponse.json(
      { error: 'Error processing chat query', details: error.message },
      { status: 500 }
    );
  }
} 