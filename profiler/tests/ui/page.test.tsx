import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Home from '../../app/ui/src/app/page';
import { ProfileService, ProfileState } from '../../app/ui/src/services/profile';

// Mock the ProfileService
jest.mock('../../app/ui/src/services/profile', () => {
  return {
    ProfileService: jest.fn().mockImplementation(() => ({
      connect: jest.fn(),
      disconnect: jest.fn(),
      onStateChange: jest.fn(),
      getState: jest.fn(),
      sendMessage: jest.fn()
    }))
  };
});

describe('Page Component', () => {
  let mockProfileService: jest.Mocked<ProfileService>;
  
  beforeEach(() => {
    jest.clearAllMocks();
    mockProfileService = new ProfileService('test-user-1') as jest.Mocked<ProfileService>;
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('should show loading state initially', () => {
    render(<Home />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should connect to WebSocket and Profile services on mount', () => {
    render(<Home />);
    expect(mockProfileService.connect).toHaveBeenCalled();
  });

  it('should disconnect from services on unmount', () => {
    const { unmount } = render(<Home />);
    unmount();
    expect(mockProfileService.disconnect).toHaveBeenCalled();
  });

  it('should display profile status when available', () => {
    const mockState: ProfileState = {
      userId: 'test-user-1',
      status: 'processing',
      progress: 50,
      data: null
    };

    mockProfileService.onStateChange.mockImplementation((callback) => {
      callback(mockState);
    });

    render(<Home />);
    expect(screen.getByText('Status: processing')).toBeInTheDocument();
    expect(screen.getByText('Progress: 50%')).toBeInTheDocument();
  });

  it('should display error message when error occurs', () => {
    const mockState: ProfileState = {
      userId: 'test-user-1',
      status: 'error',
      progress: 0,
      error: 'Failed to load profile'
    };

    mockProfileService.onStateChange.mockImplementation((callback) => {
      callback(mockState);
    });

    render(<Home />);
    expect(screen.getByText('Error: Failed to load profile')).toBeInTheDocument();
  });

  it('should display profile data when available', () => {
    const mockState: ProfileState = {
      userId: 'test-user-1',
      status: 'completed',
      progress: 100,
      data: {
        name: 'Test User',
        age: 25
      }
    };

    mockProfileService.onStateChange.mockImplementation((callback) => {
      callback(mockState);
    });

    render(<Home />);
    expect(screen.getByText(/Test User/)).toBeInTheDocument();
    expect(screen.getByText(/25/)).toBeInTheDocument();
  });
}); 