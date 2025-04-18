import React from 'react';
import { render, screen, act, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ProfileProvider, useProfile } from '../../../app/ui/lib/contexts/ProfileContext';
import { ProfileSection } from '../../../app/ui/lib/services/types';

// Create a direct test for navigateToSection function
const mockSwitchSection = jest.fn();

// Mock the serviceFactory 
jest.mock('../../../app/ui/lib/services', () => {
  // Create EventEmitter for mock
  class MockEventEmitter {
    private events: Record<string, Function[]> = {};
    
    on(event: string, listener: Function): this {
      if (!this.events[event]) {
        this.events[event] = [];
      }
      this.events[event].push(listener);
      return this;
    }
    
    emit(event: string, ...args: any[]): this {
      if (this.events[event]) {
        this.events[event].forEach(listener => listener(...args));
      }
      return this;
    }
  }
  
  // Mock implementations of services
  const mockProfileService = {
    connect: jest.fn().mockResolvedValue(undefined),
    disconnect: jest.fn(),
    getConnectionStatus: jest.fn().mockReturnValue('connected'),
    sendMessage: jest.fn(),
    sendAnswer: jest.fn(),
    switchSection: mockSwitchSection, // Use the exported mock for easier access
    onConnect: jest.fn(),
    onMessage: jest.fn(),
    onStateUpdate: jest.fn(),
    onError: jest.fn(),
    onDisconnect: jest.fn(),
    on: jest.fn(),
    emit: jest.fn(),
  };

  // Add EventEmitter methods to the mock service
  Object.setPrototypeOf(mockProfileService, MockEventEmitter.prototype);

  const mockDocumentService = {
    uploadFile: jest.fn().mockResolvedValue({}),
    uploadDocument: jest.fn().mockResolvedValue(''),
    analyzeDocument: jest.fn().mockResolvedValue({}),
    getUploadStatus: jest.fn().mockReturnValue({ status: 'idle', progress: 0 }),
    onStatusChange: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
  };

  const mockRecommendationService = {
    getRecommendations: jest.fn().mockResolvedValue([]),
    getProfileSummary: jest.fn().mockResolvedValue({}),
    filterRecommendations: jest.fn().mockResolvedValue([]),
    onRecommendationsUpdated: jest.fn(),
  };

  return {
    serviceFactory: {
      getProfileService: jest.fn().mockReturnValue(mockProfileService),
      getDocumentService: jest.fn().mockReturnValue(mockDocumentService),
      getRecommendationService: jest.fn().mockReturnValue(mockRecommendationService),
    },
  };
});

// Create a simple test component with navigation
const TestSectionNavigation = () => {
  const { navigateToSection, state, connectionStatus } = useProfile();
  
  const handleSectionClick = (section: ProfileSection) => {
    navigateToSection(section);
  };
  
  return (
    <div>
      <div data-testid="connection-status">{connectionStatus}</div>
      <div data-testid="current-section">{state?.current_section || 'none'}</div>
      
      <button data-testid="academic-button" onClick={() => handleSectionClick('academic')}>
        Academic
      </button>
      <button data-testid="extracurricular-button" onClick={() => handleSectionClick('extracurricular')}>
        Extracurricular
      </button>
      <button data-testid="personal-button" onClick={() => handleSectionClick('personal')}>
        Personal
      </button>
      <button data-testid="essays-button" onClick={() => handleSectionClick('essays')}>
        Essays
      </button>
    </div>
  );
};

describe('Section Switching', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('should call switchSection when a section button is clicked', async () => {
    // Reset mock counts
    mockSwitchSection.mockClear();
    
    const { serviceFactory } = require('../../../app/ui/lib/services');
    const mockProfileService = serviceFactory.getProfileService();
    
    // Set up necessary mock behaviors
    mockProfileService.getConnectionStatus.mockReturnValue('connected');
    
    // Set up state update handler
    mockProfileService.onStateUpdate.mockImplementation((callback: (state: any) => void) => {
      // Store the callback for later use
      mockProfileService.stateUpdateCallback = callback;
    });
    
    // Render the test component
    render(
      <ProfileProvider userId="test-user-1">
        <TestSectionNavigation />
      </ProfileProvider>
    );
    
    // Wait for component to be rendered
    await waitFor(() => {
      expect(screen.getByTestId('current-section')).toBeInTheDocument();
    });
    
    // Simulate a state update to set the initial section
    await act(async () => {
      if (mockProfileService.stateUpdateCallback) {
        mockProfileService.stateUpdateCallback({
          user_id: 'test-user-1',
          current_section: 'academic',
          sections: {
            academic: { status: 'in_progress' },
            extracurricular: { status: 'not_started' },
            personal: { status: 'not_started' },
            essays: { status: 'not_started' }
          },
          current_questions: [],
          current_answer: null,
          interaction_count: 0
        });
      }
      
      // Need to wait for React state update
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    // Check that the current section is displayed
    expect(screen.getByTestId('current-section')).toHaveTextContent('academic');
    
    // Click on a different section button
    await act(async () => {
      fireEvent.click(screen.getByTestId('personal-button'));
      // Need to wait for React state update
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    // Check that the switchSection method was called with the correct section
    expect(mockSwitchSection).toHaveBeenCalledWith('personal');
  });
  
  it('should navigate from academic to all other sections successfully', async () => {
    // Reset mock counts
    mockSwitchSection.mockClear();
    
    const { serviceFactory } = require('../../../app/ui/lib/services');
    const mockProfileService = serviceFactory.getProfileService();
    
    // Set up necessary mock behaviors
    mockProfileService.getConnectionStatus.mockReturnValue('connected');
    
    // Set up state update handler
    mockProfileService.onStateUpdate.mockImplementation((callback: (state: any) => void) => {
      // Store the callback for later use
      mockProfileService.stateUpdateCallback = callback;
    });
    
    // Render the test component
    render(
      <ProfileProvider userId="test-user-1">
        <TestSectionNavigation />
      </ProfileProvider>
    );
    
    // Wait for component to be rendered
    await waitFor(() => {
      expect(screen.getByTestId('current-section')).toBeInTheDocument();
    });
    
    // Simulate initial state
    await act(async () => {
      if (mockProfileService.stateUpdateCallback) {
        mockProfileService.stateUpdateCallback({
          user_id: 'test-user-1',
          current_section: 'academic',
          sections: {
            academic: { status: 'in_progress' },
            extracurricular: { status: 'not_started' },
            personal: { status: 'not_started' },
            essays: { status: 'not_started' }
          },
          current_questions: [],
          current_answer: null,
          interaction_count: 0
        });
      }
      
      // Need to wait for React state update
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    // Test switching to extracurricular
    await act(async () => {
      fireEvent.click(screen.getByTestId('extracurricular-button'));
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    expect(mockSwitchSection).toHaveBeenCalledWith('extracurricular');
    
    // Simulate server response
    await act(async () => {
      if (mockProfileService.stateUpdateCallback) {
        mockProfileService.stateUpdateCallback({
          user_id: 'test-user-1',
          current_section: 'extracurricular',
          sections: {
            academic: { status: 'in_progress' },
            extracurricular: { status: 'in_progress' },
            personal: { status: 'not_started' },
            essays: { status: 'not_started' }
          },
          current_questions: [],
          current_answer: null,
          interaction_count: 1
        });
      }
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    expect(screen.getByTestId('current-section')).toHaveTextContent('extracurricular');
    
    // Test switching to personal
    await act(async () => {
      fireEvent.click(screen.getByTestId('personal-button'));
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    expect(mockSwitchSection).toHaveBeenCalledWith('personal');
    
    // Simulate server response
    await act(async () => {
      if (mockProfileService.stateUpdateCallback) {
        mockProfileService.stateUpdateCallback({
          user_id: 'test-user-1',
          current_section: 'personal',
          sections: {
            academic: { status: 'in_progress' },
            extracurricular: { status: 'in_progress' },
            personal: { status: 'in_progress' },
            essays: { status: 'not_started' }
          },
          current_questions: [],
          current_answer: null,
          interaction_count: 2
        });
      }
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    expect(screen.getByTestId('current-section')).toHaveTextContent('personal');
    
    // Test switching to essays
    await act(async () => {
      fireEvent.click(screen.getByTestId('essays-button'));
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    expect(mockSwitchSection).toHaveBeenCalledWith('essays');
    
    // Simulate server response
    await act(async () => {
      if (mockProfileService.stateUpdateCallback) {
        mockProfileService.stateUpdateCallback({
          user_id: 'test-user-1',
          current_section: 'essays',
          sections: {
            academic: { status: 'in_progress' },
            extracurricular: { status: 'in_progress' },
            personal: { status: 'in_progress' },
            essays: { status: 'in_progress' }
          },
          current_questions: [],
          current_answer: null,
          interaction_count: 3
        });
      }
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    expect(screen.getByTestId('current-section')).toHaveTextContent('essays');
    
    // Test switching back to academic
    await act(async () => {
      fireEvent.click(screen.getByTestId('academic-button'));
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    expect(mockSwitchSection).toHaveBeenCalledWith('academic');
    
    // Simulate server response
    await act(async () => {
      if (mockProfileService.stateUpdateCallback) {
        mockProfileService.stateUpdateCallback({
          user_id: 'test-user-1',
          current_section: 'academic',
          sections: {
            academic: { status: 'in_progress' },
            extracurricular: { status: 'in_progress' },
            personal: { status: 'in_progress' },
            essays: { status: 'in_progress' }
          },
          current_questions: [],
          current_answer: null,
          interaction_count: 4
        });
      }
      await new Promise(resolve => setTimeout(resolve, 0));
    });
    
    expect(screen.getByTestId('current-section')).toHaveTextContent('academic');
  });
}); 