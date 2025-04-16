import { ProfileService } from '../../app/ui/src/services/profile';
import { WebSocketService } from '../../app/ui/src/services/websocket';
import { MockWebSocketService } from '../ui/utils/test-utils';
import { waitFor } from '@testing-library/react';

// Mock the WebSocketService to isolate the ProfileService
jest.mock('../../app/ui/src/services/websocket', () => {
  return {
    WebSocketService: jest.fn().mockImplementation(() => {
      return new MockWebSocketService('test-user');
    })
  };
});

describe('Profile Service Integration', () => {
  let service: ProfileService;
  let mockWebSocket: MockWebSocketService;
  
  beforeEach(() => {
    // Clear all mocks
    jest.clearAllMocks();
    
    // Create a new service instance
    service = new ProfileService('test-user');
    
    // Get the mock WebSocket instance
    mockWebSocket = WebSocketService as unknown as jest.Mock;
    mockWebSocket = mockWebSocket.mock.results[0].value;
  });
  
  afterEach(() => {
    // Disconnect the service
    service.disconnect();
  });
  
  it('should connect and receive initial state', async () => {
    let receivedState = null;
    
    // Set up state change handler
    service.onStateChange((state) => {
      receivedState = state;
    });
    
    // Connect to the service
    service.connect();
    
    // Simulate a successful connection
    mockWebSocket.simulateMessage('connected', { 
      status: 'connected',
      session_id: 'test-session-123'
    });
    
    // Simulate initial state update
    mockWebSocket.simulateMessage('state_update', {
      userId: 'test-user',
      status: 'idle',
      progress: 0
    });
    
    // Wait for the state to be updated
    await waitFor(() => {
      expect(receivedState).not.toBeNull();
    });
    
    // Verify the state
    expect(receivedState).toEqual({
      userId: 'test-user',
      status: 'idle',
      progress: 0
    });
  });
  
  it('should send a message through WebSocket', async () => {
    // Spy on the sendMessage method
    const sendMessageSpy = jest.spyOn(mockWebSocket, 'sendMessage');
    
    // Connect to the service
    service.connect();
    
    // Send a message
    service.sendMessage('analyze_document', {
      documentId: 'doc-123',
      content: 'Document content'
    });
    
    // Verify that the message was sent
    expect(sendMessageSpy).toHaveBeenCalledWith('analyze_document', {
      documentId: 'doc-123',
      content: 'Document content'
    });
  });
  
  it('should handle errors properly', async () => {
    let error = null;
    
    // Set up error handler
    service.onError((err) => {
      error = err;
    });
    
    // Connect to the service
    service.connect();
    
    // Simulate an error
    mockWebSocket.simulateMessage('error', {
      error: 'Test error message'
    });
    
    // Wait for the error to be handled
    await waitFor(() => {
      expect(error).not.toBeNull();
    });
    
    // Verify the error
    expect(error).toEqual('Test error message');
  });
  
  it('should update state when receiving state updates', async () => {
    const stateUpdates: any[] = [];
    
    // Set up state change handler
    service.onStateChange((state) => {
      stateUpdates.push(state);
    });
    
    // Connect to the service
    service.connect();
    
    // Simulate initial state
    mockWebSocket.simulateMessage('state_update', {
      userId: 'test-user',
      status: 'idle',
      progress: 0
    });
    
    // Simulate progress updates
    mockWebSocket.simulateMessage('state_update', {
      userId: 'test-user',
      status: 'processing',
      progress: 25
    });
    
    mockWebSocket.simulateMessage('state_update', {
      userId: 'test-user',
      status: 'processing',
      progress: 50
    });
    
    mockWebSocket.simulateMessage('state_update', {
      userId: 'test-user',
      status: 'completed',
      progress: 100,
      data: { result: 'success' }
    });
    
    // Wait for all updates to be processed
    await waitFor(() => {
      expect(stateUpdates.length).toBe(4);
    });
    
    // Verify the state updates
    expect(stateUpdates[0]).toEqual({
      userId: 'test-user',
      status: 'idle',
      progress: 0
    });
    
    expect(stateUpdates[1]).toEqual({
      userId: 'test-user',
      status: 'processing',
      progress: 25
    });
    
    expect(stateUpdates[2]).toEqual({
      userId: 'test-user',
      status: 'processing',
      progress: 50
    });
    
    expect(stateUpdates[3]).toEqual({
      userId: 'test-user',
      status: 'completed',
      progress: 100,
      data: { result: 'success' }
    });
  });
  
  it('should fetch profile data from API', async () => {
    // Mock the fetch API
    global.fetch = jest.fn().mockImplementation(() => 
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          userId: 'test-user',
          status: 'completed',
          progress: 100,
          data: { result: 'fetched-data' }
        })
      })
    ) as jest.Mock;
    
    // Connect to the service
    service.connect();
    
    // Fetch the profile
    const profile = await service.fetchProfile();
    
    // Verify the profile
    expect(profile).toEqual({
      userId: 'test-user',
      status: 'completed',
      progress: 100,
      data: { result: 'fetched-data' }
    });
    
    // Verify that fetch was called
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/profiles/test-user'),
      expect.objectContaining({ method: 'GET' })
    );
  });
}); 