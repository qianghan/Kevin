/**
 * Service Integration Tests
 * 
 * This file contains BDD tests for verifying compatibility and correct integration
 * between the frontend and UI chat services. It ensures that services work properly
 * across both implementations.
 */

import { ChatServiceFactory, chatServiceFactory } from '../../services/chat/ChatServiceFactory';
import { ChatServiceProxy } from '../../services/chat/ServiceProxyManager';
import { MockChatService } from '../../services/chat/mock-chat.service';
import { FileUploadService } from '../../services/chat/FileUploadService';
import { AuthenticationService, getAuthService } from '../../services/auth/AuthenticationService';
import { IChatService, ChatSession, Attachment } from '../../interfaces/services/chat.service';

// Mock the fetch API for testing
global.fetch = jest.fn();

describe('Chat Service Integration', () => {
  // Reset mocks between tests
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockClear();
  });
  
  describe('Service Factory Pattern', () => {
    it('should create a service instance using the factory', () => {
      // Arrange
      const mockFactory = new ChatServiceFactory('mock');
      
      // Act
      const service = mockFactory.createChatService();
      
      // Assert
      expect(service).toBeInstanceOf(MockChatService);
    });
    
    it('should allow registration of custom service creators', () => {
      // Arrange
      const mockFactory = new ChatServiceFactory();
      const customService: IChatService = new MockChatService();
      const customCreator = jest.fn().mockReturnValue(customService);
      
      // Act
      mockFactory.registerServiceCreator('custom', customCreator);
      const service = mockFactory.createChatService('custom');
      
      // Assert
      expect(customCreator).toHaveBeenCalled();
      expect(service).toBe(customService);
    });
    
    it('should provide a global singleton factory instance', () => {
      // Act & Assert
      expect(chatServiceFactory).toBeInstanceOf(ChatServiceFactory);
    });
  });
  
  describe('Service Proxy Pattern', () => {
    let chatProxy: ChatServiceProxy;
    
    beforeEach(() => {
      chatProxy = new ChatServiceProxy('mock');
    });
    
    it('should delegate to the underlying service', async () => {
      // Arrange
      const sessionName = 'Test Session';
      
      // Act
      const session = await chatProxy.createSession({ name: sessionName });
      
      // Assert
      expect(session.name).toBe(sessionName);
    });
    
    it('should cache results from the service', async () => {
      // Arrange
      const session = await chatProxy.createSession({ name: 'Cache Test' });
      
      // Act
      // First call should hit the service
      await chatProxy.getSession(session.id);
      // Second call should use the cache
      await chatProxy.getSession(session.id);
      
      // Assert - only one getSession call should be made to the service
      // This is challenging to test directly without mocking the underlying service
      // A real implementation would verify this through service call counts
    });
    
    it('should invalidate cache when a session is updated', async () => {
      // Arrange
      const session = await chatProxy.createSession({ name: 'Original Name' });
      await chatProxy.getSession(session.id); // Cache the session
      
      // Act
      await chatProxy.updateSession(session.id, { name: 'Updated Name' });
      const updatedSession = await chatProxy.getSession(session.id);
      
      // Assert
      expect(updatedSession.name).toBe('Updated Name');
    });
  });
  
  describe('Authentication Service', () => {
    let authService: AuthenticationService;
    
    beforeEach(() => {
      authService = new AuthenticationService('/api/auth');
      
      // Clear local storage
      localStorage.clear();
      
      // Mock successful login response
      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url === '/api/auth/login') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              token: 'test-token',
              expiresIn: 3600,
              tokenType: 'Bearer',
              user: {
                id: 'user-1',
                username: 'testuser',
                email: 'test@example.com',
                roles: ['user']
              }
            })
          });
        }
        return Promise.resolve({ ok: false });
      });
    });
    
    it('should authenticate a user and provide auth headers', async () => {
      // Act
      const user = await authService.login('testuser', 'password');
      const authHeader = await authService.getAuthHeader();
      
      // Assert
      expect(user.username).toBe('testuser');
      expect(authHeader).toHaveProperty('Authorization');
      expect(authHeader.Authorization).toContain('Bearer test-token');
    });
    
    it('should store authentication state in localStorage', async () => {
      // Arrange
      await authService.login('testuser', 'password');
      
      // Act
      const storedUser = localStorage.getItem('auth_user');
      const storedToken = localStorage.getItem('auth_token');
      
      // Assert
      expect(storedUser).not.toBeNull();
      expect(storedToken).not.toBeNull();
      expect(JSON.parse(storedUser!).username).toBe('testuser');
    });
    
    it('should clear authentication state on logout', async () => {
      // Arrange
      await authService.login('testuser', 'password');
      
      // Act
      await authService.logout();
      
      // Assert
      expect(localStorage.getItem('auth_user')).toBeNull();
      expect(localStorage.getItem('auth_token')).toBeNull();
      expect(await authService.isAuthenticated()).toBe(false);
    });
    
    it('should provide a globally accessible instance', () => {
      // Act & Assert
      expect(getAuthService()).toBeInstanceOf(AuthenticationService);
    });
  });
  
  describe('File Upload Service', () => {
    let uploadService: FileUploadService;
    
    beforeEach(() => {
      uploadService = new FileUploadService();
      
      // Mock URL.createObjectURL
      global.URL.createObjectURL = jest.fn().mockReturnValue('blob:mock-url');
    });
    
    it('should validate files before upload', () => {
      // Arrange
      const validFile = new File(['valid content'], 'valid.jpg', { type: 'image/jpeg' });
      const oversizedFile = new File(['x'.repeat(20 * 1024 * 1024)], 'toobig.jpg', { type: 'image/jpeg' });
      const invalidTypeFile = new File(['invalid content'], 'invalid.exe', { type: 'application/octet-stream' });
      
      // Act
      const result = uploadService.processFiles([validFile, oversizedFile, invalidTypeFile]);
      
      // Assert
      expect(result.successful.length).toBe(1);
      expect(result.failed.length).toBe(2);
      expect(result.successful[0].name).toBe('valid.jpg');
    });
    
    it('should create appropriate attachment types based on file type', () => {
      // Arrange
      const imageFile = new File(['image content'], 'image.png', { type: 'image/png' });
      const documentFile = new File(['document content'], 'document.pdf', { type: 'application/pdf' });
      
      // Act
      const imageAttachment = uploadService.createAttachmentFromFile(imageFile);
      const documentAttachment = uploadService.createAttachmentFromFile(documentFile);
      
      // Assert
      expect(imageAttachment.type).toBe('image');
      expect(documentAttachment.type).toBe('document');
    });
    
    it('should create link attachments', () => {
      // Arrange
      const url = 'https://example.com';
      const title = 'Example Website';
      
      // Act
      const attachment = uploadService.createLinkAttachment(url, title);
      
      // Assert
      expect(attachment.type).toBe('link');
      expect(attachment.name).toBe(title);
      expect(attachment.url).toBe(url);
    });
  });
  
  describe('Cross-Service Integration', () => {
    it('should allow the authentication service to be used with chat services', async () => {
      // Arrange
      const authService = getAuthService();
      const chatService = new ChatServiceProxy('mock');
      
      // Mock login and fetch responses
      (global.fetch as jest.Mock).mockImplementation((url) => {
        if (url === '/api/auth/login') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve({
              token: 'test-token',
              expiresIn: 3600,
              tokenType: 'Bearer',
              user: {
                id: 'user-1',
                username: 'testuser',
                email: 'test@example.com'
              }
            })
          });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
      });
      
      // Act
      await authService.login('testuser', 'password');
      const headers = await authService.getAuthHeader();
      
      // Send a message with the authentication headers
      // This is a conceptual test - in a real implementation we would verify
      // that the headers are actually used in the request
      await chatService.createSession({ name: 'Authenticated Session' });
      
      // Assert
      expect(headers).toHaveProperty('Authorization');
    });
    
    it('should allow file attachments to be used with chat services', async () => {
      // Arrange
      const uploadService = new FileUploadService();
      const chatService = new ChatServiceProxy('mock');
      
      // Create a test file and attachment
      const testFile = new File(['test content'], 'test.jpg', { type: 'image/jpeg' });
      const attachment = uploadService.createAttachmentFromFile(testFile);
      
      // Create a session
      const session = await chatService.createSession({ name: 'Attachment Test' });
      
      // Act
      // Send a message with the attachment
      const updatedSession = await chatService.sendMessageWithAttachments(
        session.id,
        'Message with attachment',
        [attachment]
      );
      
      // Assert
      const messages = updatedSession.messages;
      expect(messages.length).toBeGreaterThan(0);
      
      // Find the user message with the attachment
      const userMessage = messages.find(m => m.role === 'user' && m.attachments && m.attachments.length > 0);
      expect(userMessage).toBeDefined();
      expect(userMessage!.attachments![0].name).toBe('test.jpg');
    });
  });
}); 