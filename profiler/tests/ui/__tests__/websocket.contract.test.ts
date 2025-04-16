import '@testing-library/jest-dom';
import { 
  profileStateSchema, 
  validateMessage, 
  webSocketMessageSchema
} from '../../../app/ui/src/services/validation';
import { MockWebSocketService } from '../utils/test-utils';
import { ZodError } from 'zod';

describe('WebSocket Contract Tests', () => {
  let mockService: MockWebSocketService;

  beforeEach(() => {
    mockService = new MockWebSocketService('test-user');
  });

  afterEach(() => {
    mockService.disconnect();
  });

  it('should validate base message structure', () => {
    const validMessage = {
      type: 'test',
      data: { foo: 'bar' },
      timestamp: new Date().toISOString()
    };

    expect(() => validateMessage(validMessage, webSocketMessageSchema)).not.toThrow();
  });

  it('should reject malformed messages', () => {
    const invalidMessage = {
      foo: 'bar' // Missing required 'type' field
    };

    expect(() => validateMessage(invalidMessage, webSocketMessageSchema)).toThrow(ZodError);
  });

  it('should validate state_update messages', () => {
    let receivedMessage: any = null;
    
    mockService.onMessage('state_update', (data) => {
      receivedMessage = data;
    });
    
    const validProfileState = {
      userId: 'test-user',
      status: 'processing',
      progress: 50,
      data: { foo: 'bar' }
    };
    
    mockService.simulateMessage('state_update', validProfileState);
    
    expect(receivedMessage).not.toBeNull();
    expect(() => profileStateSchema.parse(receivedMessage)).not.toThrow();
  });

  it('should reject invalid profile state messages', () => {
    const invalidProfileState = {
      userId: 'test-user',
      status: 'invalid-status', // Not a valid status
      progress: 50
    };
    
    expect(() => profileStateSchema.parse(invalidProfileState)).toThrow(ZodError);
  });

  it('should reject profile state with invalid progress', () => {
    const invalidProgress = {
      userId: 'test-user',
      status: 'processing',
      progress: 150 // Progress must be between 0-100
    };
    
    expect(() => profileStateSchema.parse(invalidProgress)).toThrow(ZodError);
  });

  it('should validate connected messages', () => {
    let receivedMessage: any = null;
    
    mockService.onMessage('connected', (data) => {
      receivedMessage = data;
    });
    
    mockService.simulateMessage('connected', {
      status: 'connected',
      session_id: 'test-session-123'
    });
    
    expect(receivedMessage).not.toBeNull();
    expect(receivedMessage.status).toBe('connected');
  });

  it('should validate document analysis messages', () => {
    const validDocumentMessage = {
      type: 'analyze_document',
      data: {
        documentId: 'doc-123',
        content: 'Document content here'
      }
    };
    
    expect(() => validateMessage(validDocumentMessage, webSocketMessageSchema)).not.toThrow();
  });
}); 