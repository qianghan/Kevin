import { createMocks } from 'node-mocks-http';
import { NextRequest } from 'next/server';
import { GET, POST } from '../../app/api/proxy/[...path]/route';

// Mock fetch
global.fetch = jest.fn();

describe('API Proxy Route', () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it('should proxy GET requests to the backend', async () => {
    // Mock successful response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      status: 200,
      statusText: 'OK',
      headers: new Headers({ 'Content-Type': 'application/json' }),
      json: async () => ({ message: 'Success from backend' }),
      text: async () => JSON.stringify({ message: 'Success from backend' }),
    });

    // Create a mocked request
    const req = new NextRequest('http://localhost:3000/api/proxy/test', {
      method: 'GET',
    });

    // Add params to the request context
    const context = {
      params: { path: ['test'] }
    };

    const response = await GET(req, context);
    
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data).toEqual({ message: 'Success from backend' });
    
    // Verify it called fetch with correct URL
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/test'),
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('should proxy POST requests with JSON body to the backend', async () => {
    // Mock successful response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      status: 201,
      statusText: 'Created',
      headers: new Headers({ 'Content-Type': 'application/json' }),
      json: async () => ({ id: '123', message: 'Created' }),
      text: async () => JSON.stringify({ id: '123', message: 'Created' }),
    });

    // Create a mocked request with a body
    const requestBody = { test: 'data' };
    const req = new NextRequest('http://localhost:3000/api/proxy/resource', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    // Add params to the request context
    const context = {
      params: { path: ['resource'] }
    };

    const response = await POST(req, context);
    
    expect(response.status).toBe(201);
    const data = await response.json();
    expect(data).toEqual({ id: '123', message: 'Created' });
    
    // Verify it called fetch with correct URL and body
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/resource'),
      expect.objectContaining({ 
        method: 'POST',
        body: JSON.stringify(requestBody)
      })
    );
  });

  it('should handle backend errors correctly', async () => {
    // Mock error response
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      status: 500,
      statusText: 'Internal Server Error',
      headers: new Headers({ 'Content-Type': 'application/json' }),
      json: async () => ({ error: 'Backend error' }),
      text: async () => JSON.stringify({ error: 'Backend error' }),
    });

    // Create a mocked request
    const req = new NextRequest('http://localhost:3000/api/proxy/error', {
      method: 'GET',
    });

    // Add params to the request context
    const context = {
      params: { path: ['error'] }
    };

    const response = await GET(req, context);
    
    expect(response.status).toBe(500);
    const data = await response.json();
    expect(data).toEqual({ error: 'Backend error' });
  });

  it('should handle network failures', async () => {
    // Mock network failure
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network failure'));

    // Create a mocked request
    const req = new NextRequest('http://localhost:3000/api/proxy/test', {
      method: 'GET',
    });

    // Add params to the request context
    const context = {
      params: { path: ['test'] }
    };

    const response = await GET(req, context);
    
    expect(response.status).toBe(502);
    const data = await response.json();
    expect(data).toEqual({ error: expect.stringContaining('Network failure') });
  });
}); 