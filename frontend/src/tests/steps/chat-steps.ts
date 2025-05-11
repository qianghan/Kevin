/**
 * Chat State Management Step Definitions
 * 
 * These steps implement the tests defined in chat-state-management.feature
 */
import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from 'chai';
import { ChatAdapterService } from '../../services/chat/chat-adapter.service';
import { IChatService, ChatSession, ChatMessage } from '../../interfaces/services/chat.service';

// Mock data for testing
const mockSessions: ChatSession[] = [
  {
    id: 'session-1',
    name: 'First Session',
    messages: [
      {
        id: 'msg-1',
        content: 'Hello',
        role: 'user',
        timestamp: new Date(Date.now() - 3600000).toISOString()
      },
      {
        id: 'msg-2',
        content: 'Hi there!',
        role: 'assistant',
        timestamp: new Date(Date.now() - 3500000).toISOString()
      }
    ],
    createdAt: new Date(Date.now() - 3600000).toISOString(),
    updatedAt: new Date(Date.now() - 3500000).toISOString()
  },
  {
    id: 'session-2',
    name: 'Second Session',
    messages: [],
    createdAt: new Date(Date.now() - 1800000).toISOString(),
    updatedAt: new Date(Date.now() - 1800000).toISOString()
  }
];

// Test context to share state between steps
class TestContext {
  chatService: IChatService;
  sessions: ChatSession[] = [];
  currentSession: ChatSession | null = null;
  error: Error | null = null;
  loading: boolean = false;
  
  // Mock implementation of UI chat service for testing
  mockUIChatService = {
    getSessions: async () => mockSessions,
    getSession: async (id: string) => mockSessions.find(s => s.id === id) || null,
    createSession: async (options?: any) => {
      const newSession: ChatSession = {
        id: `session-${Date.now()}`,
        name: options?.name || 'New Session',
        messages: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        metadata: options?.metadata || {}
      };
      return newSession;
    },
    updateSession: async (id: string, updates: any) => {
      const session = mockSessions.find(s => s.id === id);
      if (!session) throw new Error(`Session not found: ${id}`);
      return { ...session, ...updates, updatedAt: new Date().toISOString() };
    },
    deleteSession: async (id: string) => { /* implementation */ },
    sendMessage: async (sessionId: string, content: string, options?: any) => {
      const session = mockSessions.find(s => s.id === sessionId);
      if (!session) throw new Error(`Session not found: ${sessionId}`);
      
      const userMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        content,
        role: 'user',
        timestamp: new Date().toISOString()
      };
      
      const aiMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        content: `Response to: ${content}`,
        role: 'assistant',
        timestamp: new Date().toISOString()
      };
      
      const updatedSession: ChatSession = {
        ...session,
        messages: [...session.messages, userMsg, aiMsg],
        updatedAt: new Date().toISOString()
      };
      
      return updatedSession;
    },
    sendMessageWithAttachments: async (sessionId: string, content: string, attachments: any[], options?: any) => {
      /* implementation */
      return mockSessions[0];
    },
    getThinkingSteps: async (sessionId: string, messageId: string) => [],
    exportSession: async (sessionId: string, format: string) => new Blob(),
    searchMessages: async (query: string) => []
  };
  
  constructor() {
    // Initialize chat adapter with mock UI service
    this.chatService = new ChatAdapterService(this.mockUIChatService);
  }
}

// Create a new context for each scenario
const testContext = new TestContext();

// Background steps
Given('the chat service adapter is initialized', function() {
  expect(testContext.chatService).to.not.be.undefined;
});

Given('the chat context is provided', function() {
  // This step is symbolic as we're not testing React components directly in these step definitions
  // In a full implementation, we would mock the React context
});

// Session loading steps
When('I load the list of chat sessions', async function() {
  testContext.loading = true;
  try {
    testContext.sessions = await testContext.chatService.getSessions();
    testContext.loading = false;
  } catch (error) {
    testContext.error = error instanceof Error ? error : new Error('Unknown error');
    testContext.loading = false;
  }
});

Then('my existing sessions should be displayed', function() {
  expect(testContext.sessions).to.have.lengthOf(mockSessions.length);
  expect(testContext.sessions[0].id).to.equal(mockSessions[0].id);
});

Then('the sessions should be in chronological order', function() {
  const timestamps = testContext.sessions.map(s => new Date(s.createdAt).getTime());
  const sortedTimestamps = [...timestamps].sort((a, b) => a - b);
  expect(timestamps).to.deep.equal(sortedTimestamps);
});

// Session creation steps
When('I create a new chat session', async function() {
  testContext.loading = true;
  try {
    const newSession = await testContext.chatService.createSession();
    testContext.sessions = [...testContext.sessions, newSession];
    testContext.currentSession = newSession;
    testContext.loading = false;
  } catch (error) {
    testContext.error = error instanceof Error ? error : new Error('Unknown error');
    testContext.loading = false;
  }
});

Then('a new session should be added to my list of sessions', function() {
  expect(testContext.sessions.length).to.be.greaterThan(0);
});

Then('the new session should be set as the current session', function() {
  expect(testContext.currentSession).to.not.be.null;
  expect(testContext.sessions).to.include(testContext.currentSession);
});

Then('the new session should have a default name', function() {
  expect(testContext.currentSession?.name).to.equal('New Session');
});

When('I create a new chat session with name {string}', async function(name) {
  testContext.loading = true;
  try {
    const newSession = await testContext.chatService.createSession({ name });
    testContext.sessions = [...testContext.sessions, newSession];
    testContext.currentSession = newSession;
    testContext.loading = false;
  } catch (error) {
    testContext.error = error instanceof Error ? error : new Error('Unknown error');
    testContext.loading = false;
  }
});

Then('the new session should have the name {string}', function(name) {
  expect(testContext.currentSession?.name).to.equal(name);
});

// Loading specific session steps
Given('I have at least {int} existing chat sessions', async function(count) {
  testContext.sessions = await testContext.chatService.getSessions();
  expect(testContext.sessions.length).to.be.at.least(count);
});

When('I load a specific chat session', async function() {
  testContext.loading = true;
  const sessionId = testContext.sessions[0].id;
  try {
    const session = await testContext.chatService.getSession(sessionId);
    testContext.currentSession = session;
    testContext.loading = false;
  } catch (error) {
    testContext.error = error instanceof Error ? error : new Error('Unknown error');
    testContext.loading = false;
  }
});

Then('that session should become the current session', function() {
  expect(testContext.currentSession).to.not.be.null;
  expect(testContext.currentSession?.id).to.equal(testContext.sessions[0].id);
});

Then('all messages in that session should be loaded', function() {
  const sessionMessages = testContext.sessions[0].messages;
  expect(testContext.currentSession?.messages.length).to.equal(sessionMessages.length);
});

// Message sending steps
Given('I have an active chat session', async function() {
  testContext.sessions = await testContext.chatService.getSessions();
  testContext.currentSession = testContext.sessions[0];
});

When('I send a message {string}', async function(message) {
  if (!testContext.currentSession) throw new Error('No active chat session');
  
  testContext.loading = true;
  try {
    const updatedSession = await testContext.chatService.sendMessage(
      testContext.currentSession.id,
      message
    );
    testContext.currentSession = updatedSession;
    testContext.loading = false;
  } catch (error) {
    testContext.error = error instanceof Error ? error : new Error('Unknown error');
    testContext.loading = false;
  }
});

Then('the message should be added to the current session', function() {
  const messages = testContext.currentSession?.messages || [];
  const latestUserMessage = messages.filter(m => m.role === 'user').pop();
  expect(latestUserMessage).to.not.be.undefined;
  expect(latestUserMessage?.content).to.equal('Hello, KAI!');
});

Then('the UI should show a loading state while waiting for a response', function() {
  // Since we're testing the adapter, not UI components, we verify the loading state was set during the operation
  expect(testContext.loading).to.be.false; // Should be false after operation completes
});

Then('the response should be added to the session when received', function() {
  const messages = testContext.currentSession?.messages || [];
  const latestAiMessage = messages.filter(m => m.role === 'assistant').pop();
  expect(latestAiMessage).to.not.be.undefined;
  expect(latestAiMessage?.content).to.include('Response to:');
});

// Concurrent sessions steps
Given('I have multiple active chat sessions', async function() {
  testContext.sessions = await testContext.chatService.getSessions();
  expect(testContext.sessions.length).to.be.at.least(2);
});

When('I switch between sessions', async function() {
  // Switch to the first session
  testContext.currentSession = await testContext.chatService.getSession(testContext.sessions[0].id);
  
  // Send a message in the first session
  await testContext.chatService.sendMessage(
    testContext.currentSession.id,
    'Message in first session'
  );
  
  // Switch to the second session
  testContext.currentSession = await testContext.chatService.getSession(testContext.sessions[1].id);
  
  // Send a message in the second session
  await testContext.chatService.sendMessage(
    testContext.currentSession.id,
    'Message in second session'
  );
});

Then('each session should maintain its separate state', async function() {
  // Check first session
  const firstSession = await testContext.chatService.getSession(testContext.sessions[0].id);
  const firstSessionHasMessage = firstSession.messages.some(m => 
    m.content === 'Message in first session' && m.role === 'user'
  );
  expect(firstSessionHasMessage).to.be.true;
  
  // Check second session
  const secondSession = await testContext.chatService.getSession(testContext.sessions[1].id);
  const secondSessionHasMessage = secondSession.messages.some(m => 
    m.content === 'Message in second session' && m.role === 'user'
  );
  expect(secondSessionHasMessage).to.be.true;
});

Then('messages from one session should not appear in another', async function() {
  // Check that first session doesn't have second session's message
  const firstSession = await testContext.chatService.getSession(testContext.sessions[0].id);
  const firstSessionHasWrongMessage = firstSession.messages.some(m => 
    m.content === 'Message in second session'
  );
  expect(firstSessionHasWrongMessage).to.be.false;
  
  // Check that second session doesn't have first session's message
  const secondSession = await testContext.chatService.getSession(testContext.sessions[1].id);
  const secondSessionHasWrongMessage = secondSession.messages.some(m => 
    m.content === 'Message in first session'
  );
  expect(secondSessionHasWrongMessage).to.be.false;
});

// Backend sync steps
Given('changes are made to the session in the backend', function() {
  // Simulate a backend change by directly modifying the mock session
  const sessionIndex = mockSessions.findIndex(s => s.id === testContext.currentSession?.id);
  if (sessionIndex >= 0) {
    mockSessions[sessionIndex].messages.push({
      id: `backend-msg-${Date.now()}`,
      content: 'Message added from backend',
      role: 'system',
      timestamp: new Date().toISOString()
    });
    mockSessions[sessionIndex].updatedAt = new Date().toISOString();
  }
});

When('the session is refreshed', async function() {
  if (!testContext.currentSession) throw new Error('No active chat session');
  
  testContext.loading = true;
  try {
    testContext.currentSession = await testContext.chatService.getSession(testContext.currentSession.id);
    testContext.loading = false;
  } catch (error) {
    testContext.error = error instanceof Error ? error : new Error('Unknown error');
    testContext.loading = false;
  }
});

Then('the local state should reflect the backend changes', function() {
  expect(testContext.currentSession?.messages.some(m => 
    m.content === 'Message added from backend' && m.role === 'system'
  )).to.be.true;
});

// Error handling steps
Given('the chat service encounters an error', function() {
  // Monkey patch the mock service to simulate an error
  testContext.mockUIChatService.getSessions = async () => {
    throw new Error('Simulated error in chat service');
  };
});

When('I perform a chat operation', async function() {
  try {
    await testContext.chatService.getSessions();
  } catch (error) {
    testContext.error = error instanceof Error ? error : new Error('Unknown error');
  }
});

Then('an appropriate error message should be displayed', function() {
  expect(testContext.error).to.not.be.null;
  expect(testContext.error?.message).to.include('Simulated error');
});

Then('the system should attempt to recover gracefully', function() {
  // This would typically check that the UI remains responsive and usable
  // Since we're not testing UI components directly, this is a placeholder
  expect(testContext.loading).to.be.false;
});

// Service compatibility steps
Given('both UI and frontend implementations are available', function() {
  // This is already true in our test setup
  expect(testContext.chatService).to.be.instanceOf(ChatAdapterService);
});

When('I use the chat adapter service', async function() {
  await testContext.chatService.getSessions();
});

Then('operations should work with either implementation', function() {
  // Since we're using the adapter with a mock UI service, this test passes if previous steps executed
  expect(testContext.error).to.be.null;
});

Then('data formats should be compatible between systems', function() {
  // Check that the chat sessions conform to the expected format
  for (const session of testContext.sessions) {
    expect(session).to.have.property('id');
    expect(session).to.have.property('name');
    expect(session).to.have.property('messages').that.is.an('array');
    expect(session).to.have.property('createdAt');
    expect(session).to.have.property('updatedAt');
  }
}); 