import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { WebSocketService } from '../../../app/ui/src/services/websocket';

interface WebSocketMessage {
    type: string;
    data?: any;
    error?: string;
    timestamp?: string;
}

// Mock WebSocket service
export class MockWebSocketService extends WebSocketService {
    private mockHandlers: Map<string, ((data: any) => void)[]> = new Map();
    private connected = false;

    constructor(userId: string) {
        super(userId);
    }

    connect(): void {
        this.connected = true;
        // Simulate connection success
        setTimeout(() => {
            this.notifyHandlers('connected', { status: 'connected' });
        }, 0);
    }

    sendMessage(type: string, data: any): void {
        if (!this.connected) {
            throw new Error('WebSocket is not connected');
        }
        // Simulate message processing
        setTimeout(() => {
            this.notifyHandlers(`${type}_response`, { ...data, processed: true });
        }, 0);
    }

    disconnect(): void {
        this.connected = false;
        this.mockHandlers.clear();
    }

    // Helper to simulate receiving a message
    simulateMessage(type: string, data: any): void {
        this.notifyHandlers(type, data);
    }

    onMessage(type: string, handler: (data: any) => void): void {
        if (!this.mockHandlers.has(type)) {
            this.mockHandlers.set(type, []);
        }
        this.mockHandlers.get(type)?.push(handler);
    }

    private notifyHandlers(type: string, data: any): void {
        const handlers = this.mockHandlers.get(type);
        if (handlers) {
            handlers.forEach(handler => handler(data));
        }
    }
}

// Test wrapper component
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
    return (
        <React.StrictMode>
            {children}
        </React.StrictMode>
    );
};

// Custom render function with providers
export const renderWithProviders = (
    ui: React.ReactElement,
    { route = '/', ...options } = {}
) => {
    window.history.pushState({}, 'Test page', route);
    return render(ui, {
        wrapper: AllTheProviders,
        ...options,
    });
};

// Custom test utilities
export const waitForWebSocketMessage = async (type: string) => {
    return waitFor(() => {
        const message = screen.getByTestId(`ws-message-${type}`);
        expect(message).toBeInTheDocument();
        return message;
    });
};

export const simulateWebSocketConnection = async (service: MockWebSocketService) => {
    service.connect();
    await waitFor(() => {
        expect(screen.getByText('Successfully connected')).toBeInTheDocument();
    });
};

export const simulateWebSocketError = async (service: MockWebSocketService) => {
    service.simulateMessage('error', {
        error: 'Test error message'
    });
    await waitFor(() => {
        expect(screen.getByText('Test error message')).toBeInTheDocument();
    });
}; 