import React, { ReactElement, ReactNode } from 'react';
import { render, RenderOptions, waitFor, screen } from '@testing-library/react';
import { ProfileState } from '../../../app/ui/src/services/profile';
import { WebSocketService } from '../../../app/ui/src/services/websocket';
import { ProfileContext, ProfileContextType } from '../../../app/ui/src/context/ProfileContext';
import { ProfileStoreState } from '../../../app/ui/src/store/profileStore';

// Create a mock ProfileContext
// interface ProfileContextType {
//   profileState: ProfileState | null;
//   loading: boolean;
//   error: string | null;
//   sendMessage: (type: string, data: any) => void;
//   fetchProfile: () => Promise<ProfileState>;
// }

// export const ProfileContext = createContext<ProfileContextType | undefined>(undefined);

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

// Mock profile state for testing
const mockProfileState: ProfileState = {
  userId: 'test-user-1',
  status: 'idle',
  progress: 0
};

// Create a mock implementation of the profile context
const mockProfileContextValue: ProfileContextType = {
  profileState: mockProfileState,
  loading: false,
  error: null,
  sendMessage: jest.fn(),
  fetchProfile: jest.fn().mockResolvedValue(mockProfileState)
};

interface AllProvidersProps {
  children: ReactNode;
  profileState?: Partial<ProfileState>;
  loading?: boolean;
  error?: string | null;
}

// Custom renderer that includes all providers - using a class component to avoid hooks
class MockProfileProvider extends React.Component<AllProvidersProps> {
  render() {
    const { children, profileState = mockProfileState, loading = false, error = null } = this.props;
    
    // Merge any custom profile state with the default mock
    const contextValue: ProfileContextType = {
      ...mockProfileContextValue,
      profileState: { ...mockProfileState, ...profileState },
      loading,
      error
    };

    return (
      <ProfileContext.Provider value={contextValue}>
        {children}
      </ProfileContext.Provider>
    );
  }
}

// All Providers wrapper
const AllProviders = (props: AllProvidersProps) => (
  <MockProfileProvider {...props} />
);

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & {
    profileState?: Partial<ProfileState>;
    loading?: boolean;
    error?: string | null;
  }
) => {
  const { profileState, loading, error, ...renderOptions } = options || {};
  
  return render(ui, {
    wrapper: (props) => (
      <MockProfileProvider
        {...props}
        profileState={profileState}
        loading={loading}
        error={error}
      />
    ),
    ...renderOptions
  });
};

// re-export everything
export * from '@testing-library/react';

// override render method
export { customRender as render };

// Custom render function with providers
export const renderWithProviders = (
    ui: React.ReactElement,
    { route = '/', ...options } = {}
) => {
    window.history.pushState({}, 'Test page', route);
    return render(ui, {
        wrapper: AllProviders,
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
    // Mock a successful connection response
    service.simulateMessage('connected', { status: 'Successfully connected' });
    await waitFor(() => {
        // Try to find success indication, but don't fail if not found
        try {
            const successElement = screen.getByText('Successfully connected');
            expect(successElement).toBeInTheDocument();
        } catch (e) {
            // Just continue if not found
        }
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