/**
 * Session Management Tests
 * 
 * This file contains BDD tests for session management functionality.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import { SessionProvider } from '../../../contexts/SessionContext';
import SessionBrowser from '../../../components/chat/SessionBrowser';
import { 
  ChatSession,
  ChatSessionService,
  ExportFormat,
  ExportResult
} from '../../../interfaces/services/chat.session';
import { ChatMessage } from '../../../interfaces/services/chat.service';

// Mock data
const mockSessions: ChatSession[] = [
  {
    id: 'session-1',
    name: 'First Test Session',
    createdAt: '2023-01-01T12:00:00Z',
    updatedAt: '2023-01-01T14:30:00Z',
    messageCount: 5,
    preview: 'This is a preview of the first session',
    tags: ['test', 'important'],
    starred: true
  },
  {
    id: 'session-2',
    name: 'Second Test Session',
    createdAt: '2023-01-02T10:00:00Z',
    updatedAt: '2023-01-02T11:45:00Z',
    messageCount: 3,
    preview: 'This is a preview of the second session',
    tags: ['test']
  },
  {
    id: 'session-3',
    name: 'Third Test Session',
    createdAt: '2023-01-03T09:00:00Z',
    updatedAt: '2023-01-03T16:20:00Z',
    messageCount: 8,
    preview: 'This is a preview of the third session'
  }
];

const mockMessages: ChatMessage[] = [
  {
    id: 'msg-1',
    content: 'Hello, this is a test message',
    role: 'user',
    timestamp: '2023-01-01T12:00:00Z'
  },
  {
    id: 'msg-2',
    content: 'This is a response to the test message',
    role: 'assistant',
    timestamp: '2023-01-01T12:01:00Z'
  }
];

// Mock session service
class MockSessionService implements ChatSessionService {
  private sessions: ChatSession[] = [...mockSessions];
  
  async getSessions(): Promise<ChatSession[]> {
    return [...this.sessions];
  }
  
  async getSession(sessionId: string): Promise<ChatSession> {
    const session = this.sessions.find(s => s.id === sessionId);
    if (!session) throw new Error(`Session not found: ${sessionId}`);
    return { ...session };
  }
  
  async createSession(name: string = 'New Chat'): Promise<ChatSession> {
    const newSession: ChatSession = {
      id: `session-${Date.now()}`,
      name,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      messageCount: 0
    };
    
    this.sessions.unshift(newSession);
    return { ...newSession };
  }
  
  async updateSession(sessionId: string, updates: Partial<ChatSession>): Promise<ChatSession> {
    const index = this.sessions.findIndex(s => s.id === sessionId);
    if (index === -1) throw new Error(`Session not found: ${sessionId}`);
    
    const updatedSession = {
      ...this.sessions[index],
      ...updates,
      updatedAt: new Date().toISOString()
    };
    
    this.sessions[index] = updatedSession;
    return { ...updatedSession };
  }
  
  async deleteSession(sessionId: string): Promise<void> {
    const index = this.sessions.findIndex(s => s.id === sessionId);
    if (index === -1) throw new Error(`Session not found: ${sessionId}`);
    
    this.sessions.splice(index, 1);
  }
  
  async getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
    return [...mockMessages];
  }
  
  async searchSessions(query: string): Promise<ChatSession[]> {
    return this.sessions.filter(session => 
      session.name.toLowerCase().includes(query.toLowerCase())
    );
  }
  
  async exportSession(sessionId: string, format: ExportFormat): Promise<ExportResult> {
    return {
      data: 'Mock exported data',
      filename: `session_${sessionId}.${format}`,
      mimeType: 'text/plain'
    };
  }
}

// Test wrapper with providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const mockService = new MockSessionService();
  
  return (
    <ChakraProvider>
      <SessionProvider sessionService={mockService}>
        {children}
      </SessionProvider>
    </ChakraProvider>
  );
};

// Mocks for window methods
const mockAlert = jest.fn();
const mockConfirm = jest.fn();
const mockPrompt = jest.fn();

// Setup and cleanup
beforeEach(() => {
  // Setup window method mocks
  window.alert = mockAlert;
  window.confirm = mockConfirm;
  window.prompt = mockPrompt;
  
  // Reset mocks
  mockAlert.mockReset();
  mockConfirm.mockReset();
  mockPrompt.mockReset();
  
  // Default returns
  mockConfirm.mockReturnValue(true);
  mockPrompt.mockReturnValue('Updated Name');
  
  // Mock URL.createObjectURL
  global.URL.createObjectURL = jest.fn(() => 'mock-url');
  global.URL.revokeObjectURL = jest.fn();
});

describe('Session Management', () => {
  describe('SessionBrowser Component', () => {
    it('should display a list of chat sessions', async () => {
      render(
        <TestWrapper>
          <SessionBrowser />
        </TestWrapper>
      );
      
      await waitFor(() => {
        expect(screen.getByText('First Test Session')).toBeInTheDocument();
        expect(screen.getByText('Second Test Session')).toBeInTheDocument();
        expect(screen.getByText('Third Test Session')).toBeInTheDocument();
      });
    });
    
    it('should display session metadata including tags and timestamp', async () => {
      render(
        <TestWrapper>
          <SessionBrowser />
        </TestWrapper>
      );
      
      await waitFor(() => {
        // Check for preview text
        expect(screen.getByText('This is a preview of the first session')).toBeInTheDocument();
        
        // Check for tags
        const tags = screen.getAllByText(/test|important/);
        expect(tags.length).toBeGreaterThanOrEqual(2);
        
        // Check for timestamps (implementation may vary)
        const timestamps = screen.getAllByText(/\d+\/\d+\/\d+/);
        expect(timestamps.length).toBeGreaterThanOrEqual(3);
      });
    });
    
    it('should allow creating a new session', async () => {
      const onSessionSelect = jest.fn();
      
      render(
        <TestWrapper>
          <SessionBrowser onSessionSelect={onSessionSelect} />
        </TestWrapper>
      );
      
      // Click the new session button
      fireEvent.click(screen.getByTestId('new-session-button'));
      
      // Wait for the new session to be created and callback to be called
      await waitFor(() => {
        expect(onSessionSelect).toHaveBeenCalled();
      });
    });
    
    it('should allow searching for sessions', async () => {
      render(
        <TestWrapper>
          <SessionBrowser />
        </TestWrapper>
      );
      
      // Wait for sessions to load
      await waitFor(() => {
        expect(screen.getByText('First Test Session')).toBeInTheDocument();
      });
      
      // Enter search query
      const searchInput = screen.getByTestId('session-search-input');
      fireEvent.change(searchInput, { target: { value: 'First' } });
      
      // Wait for filtered results
      await waitFor(() => {
        expect(screen.getByText('First Test Session')).toBeInTheDocument();
        expect(screen.queryByText('Second Test Session')).not.toBeInTheDocument();
        expect(screen.queryByText('Third Test Session')).not.toBeInTheDocument();
      });
    });
    
    it('should allow filtering by starred sessions', async () => {
      render(
        <TestWrapper>
          <SessionBrowser />
        </TestWrapper>
      );
      
      // Wait for sessions to load
      await waitFor(() => {
        expect(screen.getByText('First Test Session')).toBeInTheDocument();
      });
      
      // Click the starred filter button
      fireEvent.click(screen.getByTestId('starred-filter-button'));
      
      // Wait for filtered results - only the starred session should be visible
      await waitFor(() => {
        expect(screen.getByText('First Test Session')).toBeInTheDocument();
        expect(screen.queryByText('Second Test Session')).not.toBeInTheDocument();
        expect(screen.queryByText('Third Test Session')).not.toBeInTheDocument();
      });
    });
  });
  
  describe('Session Context', () => {
    it('should provide session management functionality to components', async () => {
      const onSessionSelect = jest.fn();
      
      render(
        <TestWrapper>
          <SessionBrowser onSessionSelect={onSessionSelect} />
        </TestWrapper>
      );
      
      // Wait for sessions to load
      await waitFor(() => {
        expect(screen.getByText('First Test Session')).toBeInTheDocument();
      });
      
      // Select a session
      fireEvent.click(screen.getByText('Second Test Session'));
      
      // Verify callback was called with correct session ID
      await waitFor(() => {
        expect(onSessionSelect).toHaveBeenCalledWith('session-2');
      });
    });
  });
  
  describe('Session Operations', () => {
    it('should allow renaming a session', async () => {
      render(
        <TestWrapper>
          <SessionBrowser />
        </TestWrapper>
      );
      
      // Wait for sessions to load
      await waitFor(() => {
        expect(screen.getByText('First Test Session')).toBeInTheDocument();
      });
      
      // Open menu for the first session and click rename
      const menuButtons = screen.getAllByLabelText('Session options');
      fireEvent.click(menuButtons[0]); // Open first session's menu
      
      // Click rename option
      await waitFor(() => {
        fireEvent.click(screen.getByText('Rename'));
      });
      
      // Verify prompt was shown and session was renamed
      expect(mockPrompt).toHaveBeenCalled();
      
      // Wait for UI to update with new name
      await waitFor(() => {
        expect(screen.getByText('Updated Name')).toBeInTheDocument();
      });
    });
    
    it('should allow deleting a session', async () => {
      render(
        <TestWrapper>
          <SessionBrowser />
        </TestWrapper>
      );
      
      // Wait for sessions to load
      await waitFor(() => {
        expect(screen.getByText('First Test Session')).toBeInTheDocument();
      });
      
      // Count initial sessions
      const initialSessionCount = screen.getAllByText(/Test Session/).length;
      
      // Open menu for the first session and click delete
      const menuButtons = screen.getAllByLabelText('Session options');
      fireEvent.click(menuButtons[0]); // Open first session's menu
      
      // Click delete option
      await waitFor(() => {
        fireEvent.click(screen.getByText('Delete'));
      });
      
      // Verify confirm was shown
      expect(mockConfirm).toHaveBeenCalled();
      
      // Wait for UI to update with session removed
      await waitFor(() => {
        const newSessionCount = screen.getAllByText(/Test Session/).length;
        expect(newSessionCount).toBe(initialSessionCount - 1);
      });
    });
  });
  
  describe('Session Export', () => {
    it('should allow exporting a session in different formats', async () => {
      // Mock createElement and appendChild
      const mockAnchor = { click: jest.fn(), href: '', download: '' };
      const originalCreateElement = document.createElement;
      document.createElement = jest.fn(() => mockAnchor) as any;
      document.body.appendChild = jest.fn();
      document.body.removeChild = jest.fn();
      
      render(
        <TestWrapper>
          <SessionBrowser />
        </TestWrapper>
      );
      
      // Wait for sessions to load
      await waitFor(() => {
        expect(screen.getByText('First Test Session')).toBeInTheDocument();
      });
      
      // Open menu for the first session and click export
      const menuButtons = screen.getAllByLabelText('Session options');
      fireEvent.click(menuButtons[0]); // Open first session's menu
      
      // Click export option
      await waitFor(() => {
        fireEvent.click(screen.getByText('Export as JSON'));
      });
      
      // Verify download was triggered
      expect(mockAnchor.click).toHaveBeenCalled();
      
      // Restore original createElement
      document.createElement = originalCreateElement;
    });
  });
}); 