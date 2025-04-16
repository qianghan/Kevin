import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders, MockWebSocketService, simulateWebSocketConnection } from '../utils/test-utils';
import ProfilePage from '../../../app/ui/src/app/page';

describe('Profile Workflow', () => {
    let mockWebSocket: MockWebSocketService;

    beforeEach(() => {
        mockWebSocket = new MockWebSocketService('test-user-1');
        jest.spyOn(window, 'WebSocket').mockImplementation(() => mockWebSocket as any);
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    test('should connect to WebSocket and display initial state', async () => {
        renderWithProviders(<ProfilePage />);
        
        // Wait for connection
        await simulateWebSocketConnection(mockWebSocket);
        
        // Verify initial state
        expect(screen.getByText('Profile Builder')).toBeInTheDocument();
        expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    test('should handle document upload and analysis', async () => {
        renderWithProviders(<ProfilePage />);
        await simulateWebSocketConnection(mockWebSocket);
        
        // Upload document
        const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
        const uploadInput = screen.getByLabelText(/upload document/i);
        await userEvent.upload(uploadInput, file);
        
        // Simulate analysis response
        mockWebSocket.simulateMessage('document_analysis', {
            summary: 'Test document summary',
            key_points: ['Point 1', 'Point 2']
        });
        
        // Verify analysis results
        await waitFor(() => {
            expect(screen.getByText('Test document summary')).toBeInTheDocument();
            expect(screen.getByText('Point 1')).toBeInTheDocument();
        });
    });

    test('should handle QA interactions', async () => {
        renderWithProviders(<ProfilePage />);
        await simulateWebSocketConnection(mockWebSocket);
        
        // Ask question
        const questionInput = screen.getByPlaceholderText(/ask a question/i);
        await userEvent.type(questionInput, 'What is the main topic?');
        await userEvent.click(screen.getByText('Ask'));
        
        // Simulate QA response
        mockWebSocket.simulateMessage('qa_response', {
            answer: 'The main topic is testing.',
            confidence: 0.95
        });
        
        // Verify answer
        await waitFor(() => {
            expect(screen.getByText('The main topic is testing.')).toBeInTheDocument();
        });
    });

    test('should handle recommendations', async () => {
        renderWithProviders(<ProfilePage />);
        await simulateWebSocketConnection(mockWebSocket);
        
        // Request recommendations
        await userEvent.click(screen.getByText('Get Recommendations'));
        
        // Simulate recommendations
        mockWebSocket.simulateMessage('recommendations', {
            suggestions: [
                { title: 'Suggestion 1', description: 'Description 1' },
                { title: 'Suggestion 2', description: 'Description 2' }
            ]
        });
        
        // Verify recommendations
        await waitFor(() => {
            expect(screen.getByText('Suggestion 1')).toBeInTheDocument();
            expect(screen.getByText('Description 2')).toBeInTheDocument();
        });
    });

    test('should handle errors gracefully', async () => {
        renderWithProviders(<ProfilePage />);
        await simulateWebSocketConnection(mockWebSocket);
        
        // Simulate error
        mockWebSocket.simulateMessage('error', {
            error: 'Test error occurred'
        });
        
        // Verify error handling
        await waitFor(() => {
            expect(screen.getByText('Test error occurred')).toBeInTheDocument();
        });
        
        // Verify error recovery
        await userEvent.click(screen.getByText('Retry'));
        await simulateWebSocketConnection(mockWebSocket);
        expect(screen.getByText('Connected')).toBeInTheDocument();
    });

    test('should handle disconnection and reconnection', async () => {
        renderWithProviders(<ProfilePage />);
        await simulateWebSocketConnection(mockWebSocket);
        
        // Simulate disconnection
        mockWebSocket.disconnect();
        await waitFor(() => {
            expect(screen.getByText('Disconnected')).toBeInTheDocument();
        });
        
        // Verify reconnection
        await userEvent.click(screen.getByText('Reconnect'));
        await simulateWebSocketConnection(mockWebSocket);
        expect(screen.getByText('Connected')).toBeInTheDocument();
    });
}); 