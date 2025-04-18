import { ConnectionManager } from '../../../app/backend/api/websocket';
import { WebSocketMessageRouter } from '../../../app/backend/api/websocket_handler';
import { datetime } from 'datetime';

// Mock dependencies
jest.mock('../../../app/backend/utils/logging', () => ({
  get_logger: jest.fn().mockReturnValue({
    debug: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
    error: jest.fn()
  })
}));

jest.mock('datetime', () => ({
  datetime: {
    now: jest.fn().mockReturnValue({
      isoformat: jest.fn().mockReturnValue('2023-01-01T00:00:00Z')
    })
  }
}));

describe('Switch Section Message Handling', () => {
  // Test for the _update_state method
  it('should update state.current_section when handling switch_section message', async () => {
    // Create a ConnectionManager instance
    const connectionManager = new ConnectionManager();
    
    // Create a mock state
    const mockState = {
      user_id: 'test-user',
      current_section: 'academic',
      sections: {
        academic: { status: 'in_progress' },
        extracurricular: { status: 'not_started' },
        personal: { status: 'not_started' },
        essays: { status: 'not_started' }
      },
      current_questions: [],
      current_answer: null,
      interaction_count: 0,
      last_updated: '2023-01-01T00:00:00Z'
    };
    
    // Create a mock message
    const messageType = 'switch_section';
    const messageData = { section: 'personal' };
    const rawData = {
      type: 'switch_section',
      data: { section: 'personal' }
    };
    
    // Call the _update_state method
    const updatedState = await connectionManager._update_state(
      mockState,
      messageType,
      messageData,
      rawData
    );
    
    // Verify the state was updated correctly
    expect(updatedState.current_section).toBe('personal');
    expect(updatedState.interaction_count).toBe(1);
    expect(updatedState.last_updated).toBe('2023-01-01T00:00:00Z');
  });
  
  // Test when the section is missing
  it('should throw error when section is missing', async () => {
    // Create a ConnectionManager instance
    const connectionManager = new ConnectionManager();
    
    // Create a mock state
    const mockState = {
      user_id: 'test-user',
      current_section: 'academic',
      sections: {
        academic: { status: 'in_progress' },
        extracurricular: { status: 'not_started' },
        personal: { status: 'not_started' },
        essays: { status: 'not_started' }
      },
      current_questions: [],
      current_answer: null,
      interaction_count: 0,
      last_updated: '2023-01-01T00:00:00Z'
    };
    
    // Create a mock message with missing section
    const messageType = 'switch_section';
    const messageData = {}; // Missing section
    const rawData = {
      type: 'switch_section',
      data: {} // Missing section
    };
    
    // Call the _update_state method should throw
    await expect(async () => {
      await connectionManager._update_state(
        mockState,
        messageType,
        messageData,
        rawData
      );
    }).rejects.toThrow('Invalid section switch data');
  });
  
  // Test for all section types
  it('should handle switching to all section types', async () => {
    // Create a ConnectionManager instance
    const connectionManager = new ConnectionManager();
    
    // Create a mock state
    const mockState = {
      user_id: 'test-user',
      current_section: 'academic',
      sections: {
        academic: { status: 'in_progress' },
        extracurricular: { status: 'not_started' },
        personal: { status: 'not_started' },
        essays: { status: 'not_started' }
      },
      current_questions: [],
      current_answer: null,
      interaction_count: 0,
      last_updated: '2023-01-01T00:00:00Z'
    };
    
    // Test each section type
    const sectionTypes = ['academic', 'extracurricular', 'personal', 'essays'];
    
    for (const section of sectionTypes) {
      // Create mock message for this section
      const messageType = 'switch_section';
      const messageData = { section };
      const rawData = {
        type: 'switch_section',
        data: { section }
      };
      
      // Call the _update_state method
      const updatedState = await connectionManager._update_state(
        mockState,
        messageType,
        messageData,
        rawData
      );
      
      // Verify the section was updated correctly
      expect(updatedState.current_section).toBe(section);
    }
  });
}); 