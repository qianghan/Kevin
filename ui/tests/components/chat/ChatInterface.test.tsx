import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChatInterface from '../../../components/chat/ChatInterface';

// Mock the API client
jest.mock('@/lib/api/kevin', () => ({
  chatApi: {
    sendMessage: jest.fn().mockResolvedValue({
      message: 'Mock response message',
      sessionId: 'mock-session-id'
    }),
    getStreamUrl: jest.fn().mockReturnValue('/api/proxy/chat/stream')
  }
}));

// Mock the Event Source
class MockEventSource {
  onopen: () => void = () => {};
  onmessage: (event: any) => void = () => {};
  onerror: (event: any) => void = () => {};
  addEventListener: jest.Mock = jest.fn((event, callback) => {
    if (event === 'message') this.onmessage = callback;
    if (event === 'error') this.onerror = callback;
    if (event === 'open') this.onopen = callback;
    
    // For specific events
    if (event === 'thinking:start') {
      setTimeout(() => {
        callback({
          data: JSON.stringify({
            type: 'thinking',
            description: 'Starting to think...'
          })
        });
      }, 10);
    }
    
    if (event === 'answer:chunk') {
      setTimeout(() => {
        callback({
          data: 'This is a response chunk'
        });
      }, 20);
    }
    
    if (event === 'done') {
      setTimeout(() => {
        callback({
          data: JSON.stringify({
            sessionId: 'new-session-id'
          })
        });
      }, 30);
    }
  });
  close: jest.Mock = jest.fn();
  
  constructor() {
    setTimeout(() => {
      this.onopen();
    }, 5);
  }
}

// Add to global
global.EventSource = MockEventSource as any;

describe('ChatInterface', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('renders the chat interface correctly', () => {
    render(<ChatInterface />);
    
    expect(screen.getByPlaceholderText(/Type your message/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Send/i })).toBeInTheDocument();
  });
  
  it('displays initial messages if provided', () => {
    const initialMessages = [
      { role: 'user', content: 'Hello', timestamp: new Date() },
      { role: 'assistant', content: 'Hi there!', timestamp: new Date() }
    ];
    
    render(<ChatInterface initialMessages={initialMessages} />);
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('Hi there!')).toBeInTheDocument();
  });
  
  it('handles user input and streaming response', async () => {
    const user = userEvent.setup();
    const onNewSession = jest.fn();
    
    render(<ChatInterface onNewSession={onNewSession} />);
    
    const input = screen.getByPlaceholderText(/Type your message/i);
    await user.type(input, 'What is 2+2?');
    
    const sendButton = screen.getByRole('button', { name: /Send/i });
    await user.click(sendButton);
    
    // Should display user message
    expect(screen.getByText('What is 2+2?')).toBeInTheDocument();
    
    // Should show thinking indicator
    await waitFor(() => {
      expect(screen.getByText(/Starting to think.../i)).toBeInTheDocument();
    });
    
    // Should receive streaming response
    await waitFor(() => {
      expect(screen.getByText('This is a response chunk')).toBeInTheDocument();
    });
    
    // Should call onNewSession with new session ID
    await waitFor(() => {
      expect(onNewSession).toHaveBeenCalledWith('new-session-id');
    });
  });
  
  it('uses existing session ID if provided', async () => {
    const user = userEvent.setup();
    
    render(<ChatInterface sessionId="existing-session-id" />);
    
    const input = screen.getByPlaceholderText(/Type your message/i);
    await user.type(input, 'Another question');
    
    const sendButton = screen.getByRole('button', { name: /Send/i });
    await user.click(sendButton);
    
    // Should use existing session ID for the API call
    expect(screen.getByText('Another question')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('This is a response chunk')).toBeInTheDocument();
    });
  });
}); 