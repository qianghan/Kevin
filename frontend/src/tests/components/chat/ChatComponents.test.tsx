/**
 * Chat Components Tests
 * 
 * This file contains BDD-style tests for the chat-related components
 * using the behavior-driven development approach.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import ChatContainer from '../../../components/chat/ChatContainer';
import ChatHeader from '../../../components/chat/ChatHeader';
import ChatMessageList from '../../../components/chat/ChatMessageList';
import UserMessage from '../../../components/chat/UserMessage';
import AIMessage from '../../../components/chat/AIMessage';
import StreamingMessage from '../../../components/chat/StreamingMessage';
import ThinkingSteps from '../../../components/chat/ThinkingSteps';
import ChatInput from '../../../components/chat/ChatInput';
import { ThinkingStep } from '../../../interfaces/services/chat.service';

// Test wrapper with Chakra provider
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <ChakraProvider>{children}</ChakraProvider>
);

// Mock data
const mockSession = {
  id: 'session-1',
  name: 'Test Session',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  messageCount: 5
};

const mockUserMessage = {
  id: 'msg-1',
  content: 'This is a user message',
  role: 'user',
  timestamp: new Date().toISOString(),
};

const mockAIMessage = {
  id: 'msg-2',
  content: 'This is an AI response',
  role: 'assistant',
  timestamp: new Date().toISOString(),
};

const mockThinkingSteps: ThinkingStep[] = [
  {
    id: 'step-1',
    messageId: 'msg-2',
    content: 'First I need to analyze the question',
    timestamp: new Date().toISOString()
  },
  {
    id: 'step-2',
    messageId: 'msg-2',
    content: 'Then I'll formulate a comprehensive response',
    timestamp: new Date().toISOString()
  }
];

describe('Chat Components', () => {
  // ChatContainer Tests
  describe('ChatContainer', () => {
    it('should render children content', () => {
      render(
        <TestWrapper>
          <ChatContainer>
            <div data-testid="child-content">Content</div>
          </ChatContainer>
        </TestWrapper>
      );
      
      expect(screen.getByTestId('child-content')).toBeInTheDocument();
    });
    
    it('should display a loading indicator when isLoading is true', () => {
      render(
        <TestWrapper>
          <ChatContainer isLoading={true}>
            <div>Content</div>
          </ChatContainer>
        </TestWrapper>
      );
      
      // Check for loading indicator (the specific implementation might vary)
      const loadingIndicator = screen.getByRole('presentation');
      expect(loadingIndicator).toBeInTheDocument();
    });
  });
  
  // ChatHeader Tests
  describe('ChatHeader', () => {
    it('should display the session name', () => {
      render(
        <TestWrapper>
          <ChatHeader 
            session={mockSession}
          />
        </TestWrapper>
      );
      
      expect(screen.getByText('Test Session')).toBeInTheDocument();
    });
    
    it('should call onRenameSession when rename option is clicked', async () => {
      const onRenameSession = jest.fn();
      
      render(
        <TestWrapper>
          <ChatHeader 
            session={mockSession}
            onRenameSession={onRenameSession}
          />
        </TestWrapper>
      );
      
      // Open the menu and click rename
      fireEvent.click(screen.getByTestId('chat-options-button'));
      fireEvent.click(screen.getByTestId('rename-chat-option'));
      
      expect(onRenameSession).toHaveBeenCalled();
    });
  });
  
  // ChatMessageList Tests
  describe('ChatMessageList', () => {
    it('should render user and AI messages', () => {
      render(
        <TestWrapper>
          <ChatMessageList 
            messages={[mockUserMessage, mockAIMessage]}
          />
        </TestWrapper>
      );
      
      expect(screen.getByText('This is a user message')).toBeInTheDocument();
      expect(screen.getByText('This is an AI response')).toBeInTheDocument();
    });
    
    it('should display empty state message when no messages', () => {
      render(
        <TestWrapper>
          <ChatMessageList 
            messages={[]}
            emptyStateMessage="No messages yet"
          />
        </TestWrapper>
      );
      
      expect(screen.getByText('No messages yet')).toBeInTheDocument();
    });
  });
  
  // UserMessage Tests
  describe('UserMessage', () => {
    it('should render user message content', () => {
      render(
        <TestWrapper>
          <UserMessage message={mockUserMessage} />
        </TestWrapper>
      );
      
      expect(screen.getByText('This is a user message')).toBeInTheDocument();
    });
    
    it('should show timestamp when showTimestamp is true', () => {
      render(
        <TestWrapper>
          <UserMessage 
            message={mockUserMessage} 
            showTimestamp={true}
          />
        </TestWrapper>
      );
      
      // The specific format might vary, but we should find some time text
      const timestamp = screen.getByText(/\d+:\d+/); // Matches time format like 10:30
      expect(timestamp).toBeInTheDocument();
    });
  });
  
  // AIMessage Tests
  describe('AIMessage', () => {
    it('should render AI message content', () => {
      render(
        <TestWrapper>
          <AIMessage message={mockAIMessage} />
        </TestWrapper>
      );
      
      expect(screen.getByText('This is an AI response')).toBeInTheDocument();
    });
    
    it('should show thinking steps when expanded', async () => {
      render(
        <TestWrapper>
          <AIMessage 
            message={mockAIMessage}
            showThinkingSteps={true}
            thinkingSteps={mockThinkingSteps}
          />
        </TestWrapper>
      );
      
      // Click to expand thinking steps
      fireEvent.click(screen.getByText('Thinking Steps'));
      
      // Wait for thinking steps to appear
      await waitFor(() => {
        expect(screen.getByText('First I need to analyze the question')).toBeInTheDocument();
      });
    });
  });
  
  // StreamingMessage Tests
  describe('StreamingMessage', () => {
    it('should render streaming content', () => {
      render(
        <TestWrapper>
          <StreamingMessage content="This is streaming" />
        </TestWrapper>
      );
      
      expect(screen.getByText('This is streaming')).toBeInTheDocument();
    });
    
    it('should show cursor when not complete', () => {
      render(
        <TestWrapper>
          <StreamingMessage 
            content="This is streaming" 
            isComplete={false}
          />
        </TestWrapper>
      );
      
      // Check if cursor element exists (implementation-specific)
      const cursor = screen.getByTestId('streaming-message').querySelector('span');
      expect(cursor).toBeInTheDocument();
    });
  });
  
  // ThinkingSteps Tests
  describe('ThinkingSteps', () => {
    it('should render thinking steps', () => {
      render(
        <TestWrapper>
          <ThinkingSteps steps={mockThinkingSteps} />
        </TestWrapper>
      );
      
      expect(screen.getByText(/Step 1/)).toBeInTheDocument();
      expect(screen.getByText(/Step 2/)).toBeInTheDocument();
    });
    
    it('should show loading state when isLoading is true', () => {
      render(
        <TestWrapper>
          <ThinkingSteps steps={[]} isLoading={true} />
        </TestWrapper>
      );
      
      expect(screen.getByText('Loading thinking steps...')).toBeInTheDocument();
    });
  });
  
  // ChatInput Tests
  describe('ChatInput', () => {
    it('should allow typing messages', () => {
      render(
        <TestWrapper>
          <ChatInput 
            onSendMessage={jest.fn()}
            placeholder="Type here..."
          />
        </TestWrapper>
      );
      
      const input = screen.getByPlaceholderText('Type here...');
      fireEvent.change(input, { target: { value: 'Hello world' } });
      
      expect(input).toHaveValue('Hello world');
    });
    
    it('should call onSendMessage when send button is clicked', () => {
      const onSendMessage = jest.fn();
      
      render(
        <TestWrapper>
          <ChatInput 
            onSendMessage={onSendMessage}
          />
        </TestWrapper>
      );
      
      // Type a message
      const input = screen.getByRole('textbox');
      fireEvent.change(input, { target: { value: 'Test message' } });
      
      // Click send button
      fireEvent.click(screen.getByText('Send'));
      
      expect(onSendMessage).toHaveBeenCalledWith('Test message', expect.anything());
    });
    
    it('should support file attachments when onSendAttachments is provided', () => {
      render(
        <TestWrapper>
          <ChatInput 
            onSendMessage={jest.fn()}
            onSendAttachments={jest.fn()}
          />
        </TestWrapper>
      );
      
      // Check if attachment button exists
      const attachButton = screen.getByLabelText('Attach files');
      expect(attachButton).toBeInTheDocument();
    });
  });
}); 