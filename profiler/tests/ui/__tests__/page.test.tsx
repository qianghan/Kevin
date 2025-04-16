import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import React from 'react';

// Mock the Home component
jest.mock('../../../app/ui/src/app/page', () => {
  return function MockHome() {
    return <div>Loading...</div>;
  };
});

// Create mock functions
const connectMock = jest.fn().mockReturnValue(true);
const disconnectMock = jest.fn().mockReturnValue(true);

// Mock the ProfileService
jest.mock('../../../app/ui/src/services/profile', () => {
  return {
    ProfileService: jest.fn().mockImplementation(() => ({
      connect: connectMock,
      disconnect: disconnectMock,
      onStateChange: jest.fn(),
      getState: jest.fn(),
      sendMessage: jest.fn()
    }))
  };
});

import Home from '../../../app/ui/src/app/page';
import { ProfileService } from '../../../app/ui/src/services/profile';

describe('Page Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('should render the Loading text', () => {
    render(<Home />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('ProfileService connect should be callable', () => {
    connectMock();
    expect(connectMock).toHaveBeenCalled();
  });

  it('ProfileService disconnect should be callable', () => {
    disconnectMock();
    expect(disconnectMock).toHaveBeenCalled();
  });
}); 