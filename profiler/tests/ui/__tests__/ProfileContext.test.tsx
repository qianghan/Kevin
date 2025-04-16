import React from 'react';
import { render, screen, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ProfileProvider, useProfile } from '../../../app/ui/src/context/ProfileContext';

// Mock ProfileService
jest.mock('../../../app/ui/src/services/profile', () => {
  const mockOnStateChange = jest.fn();
  const mockConnect = jest.fn();
  const mockDisconnect = jest.fn();
  const mockFetchProfile = jest.fn();
  const mockSendMessage = jest.fn();
  
  return {
    ProfileService: jest.fn().mockImplementation(() => ({
      onStateChange: mockOnStateChange,
      connect: mockConnect,
      disconnect: mockDisconnect,
      fetchProfile: mockFetchProfile,
      sendMessage: mockSendMessage,
      getState: jest.fn().mockReturnValue({
        userId: 'test-user-1',
        status: 'idle',
        progress: 0
      })
    })),
    ProfileState: {
      userId: 'test-user-1',
      status: 'idle',
      progress: 0
    }
  };
});

// Test component that uses the context
const TestComponent = () => {
  const { profileState, loading, error, sendMessage } = useProfile();
  
  return (
    <div>
      {loading && <div data-testid="loading">Loading...</div>}
      {error && <div data-testid="error">{error}</div>}
      {profileState && (
        <div>
          <div data-testid="userId">{profileState.userId}</div>
          <div data-testid="status">{profileState.status}</div>
          <div data-testid="progress">{profileState.progress}</div>
          <button onClick={() => sendMessage('test', { data: 'test' })}>Send Message</button>
        </div>
      )}
    </div>
  );
};

describe('ProfileProvider', () => {
  it('should provide loading state initially', () => {
    render(
      <ProfileProvider userId="test-user-1">
        <TestComponent />
      </ProfileProvider>
    );
    
    expect(screen.getByTestId('loading')).toBeInTheDocument();
  });
  
  it('should initialize ProfileService with the provided userId', () => {
    const { ProfileService } = require('../../../app/ui/src/services/profile');
    
    render(
      <ProfileProvider userId="custom-user-id">
        <TestComponent />
      </ProfileProvider>
    );
    
    expect(ProfileService).toHaveBeenCalledWith('custom-user-id');
  });
  
  it('should connect to the ProfileService on mount', () => {
    const { ProfileService } = require('../../../app/ui/src/services/profile');
    const mockService = ProfileService.mock.results[0].value;
    
    render(
      <ProfileProvider userId="test-user-1">
        <TestComponent />
      </ProfileProvider>
    );
    
    expect(mockService.connect).toHaveBeenCalled();
  });
  
  it('should disconnect from the ProfileService on unmount', () => {
    const { ProfileService } = require('../../../app/ui/src/services/profile');
    const mockService = ProfileService.mock.results[0].value;
    
    const { unmount } = render(
      <ProfileProvider userId="test-user-1">
        <TestComponent />
      </ProfileProvider>
    );
    
    unmount();
    expect(mockService.disconnect).toHaveBeenCalled();
  });
  
  it('should update state when ProfileService calls the state change handler', () => {
    const { ProfileService } = require('../../../app/ui/src/services/profile');
    const mockService = ProfileService.mock.results[0].value;
    
    render(
      <ProfileProvider userId="test-user-1">
        <TestComponent />
      </ProfileProvider>
    );
    
    // Get the callback function that was passed to onStateChange
    const onStateChangeCallback = mockService.onStateChange.mock.calls[0][0];
    
    // Call the callback with mock state data
    act(() => {
      onStateChangeCallback({
        userId: 'test-user-1',
        status: 'processing',
        progress: 50
      });
    });
    
    // Check that the state was updated and rendered
    expect(screen.getByTestId('status')).toHaveTextContent('processing');
    expect(screen.getByTestId('progress')).toHaveTextContent('50');
  });
}); 