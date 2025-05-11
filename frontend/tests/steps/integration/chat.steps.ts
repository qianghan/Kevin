import { Given, When, Then, setDefaultTimeout } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { getPage, navigateTo } from '../support/browser';

// Increase timeout for integration tests
setDefaultTimeout(30000);

// Background steps
Given('I am logged in as a test user', async function() {
  const page = await getPage();
  await navigateTo(page, '/login');
  
  // Fill in login form
  await page.fill('input[name="email"]', 'test@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  // Wait for successful login
  await page.waitForURL('/dashboard');
});

Given('I have an active chat session', async function() {
  const page = await getPage();
  await navigateTo(page, '/chat');
  
  // Start new session or select existing one
  if (await page.isVisible('text="Start New Chat"')) {
    await page.click('text="Start New Chat"');
  } else {
    // Select first chat session if available
    const sessionElement = await page.$('.chat-session-item:first-child');
    if (sessionElement) {
      await sessionElement.click();
    } else {
      // Create new session if none exist
      await page.click('button:has-text("New Chat")');
    }
  }
  
  // Wait for chat interface to load
  await page.waitForSelector('.chat-container');
});

// Basic message sending
When('I type {string} in the chat input', async function(message: string) {
  const page = await getPage();
  await page.fill('.chat-input textarea', message);
  
  // Store message for later verification
  this.currentMessage = message;
});

When('I submit the message', async function() {
  const page = await getPage();
  await page.click('button.send-button');
  
  // Wait for message to appear in history
  await page.waitForSelector(`.user-message:has-text("${this.currentMessage}")`, { timeout: 5000 });
});

Then('I should see my message in the chat history', async function() {
  const page = await getPage();
  const messageVisible = await page.isVisible(`.user-message:has-text("${this.currentMessage}")`);
  expect(messageVisible).toBe(true);
});

Then('I should receive a response from KAI', async function() {
  const page = await getPage();
  // Wait for AI response with timeout
  await page.waitForSelector('.ai-message', { timeout: 10000 });
  const hasResponse = await page.isVisible('.ai-message');
  expect(hasResponse).toBe(true);
});

// Session persistence
When('I send several messages in a chat session', async function() {
  const page = await getPage();
  this.messages = ['Hello there', 'How are you today?', 'Testing message persistence'];
  
  // Send multiple messages
  for (const message of this.messages) {
    await page.fill('.chat-input textarea', message);
    await page.click('button.send-button');
    await page.waitForSelector(`.user-message:has-text("${message}")`, { timeout: 5000 });
  }
});

When('I reload the page', async function() {
  const page = await getPage();
  await page.reload();
  // Wait for chat interface to load after reload
  await page.waitForSelector('.chat-container');
});

Then('I should see my previous messages', async function() {
  const page = await getPage();
  
  // Check all messages are still visible
  for (const message of this.messages) {
    const messageVisible = await page.isVisible(`.user-message:has-text("${message}")`);
    expect(messageVisible).toBe(true);
  }
});

Then('the chat session should maintain continuity', async function() {
  const page = await getPage();
  
  // Check if the chat session title is preserved
  const sessionTitle = await page.textContent('.chat-header h2');
  expect(sessionTitle).not.toBeNull();
  
  // Verify we can still send messages
  const testMessage = 'Testing continuity after reload';
  await page.fill('.chat-input textarea', testMessage);
  await page.click('button.send-button');
  
  // Wait for new message to appear
  await page.waitForSelector(`.user-message:has-text("${testMessage}")`, { timeout: 5000 });
});

// Attachment handling
When('I attach a file to my message', async function() {
  const page = await getPage();
  
  // Click attachment button
  await page.click('button.attachment-button');
  
  // Use file chooser to select a file
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.click('button:has-text("Choose File")')
  ]);
  
  // Select a mock file
  await fileChooser.setFiles({
    name: 'test-file.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from('This is a test file for attachment')
  });
  
  // Store attachment info for verification
  this.attachmentName = 'test-file.txt';
});

When('I submit the message with the attachment', async function() {
  const page = await getPage();
  await page.fill('.chat-input textarea', 'Here is an attachment');
  await page.click('button.send-button');
});

Then('the attachment should be uploaded successfully', async function() {
  const page = await getPage();
  // Wait for upload success indicator
  await page.waitForSelector('.attachment-success', { timeout: 10000 });
});

Then('the message with attachment should appear in the chat history', async function() {
  const page = await getPage();
  // Check if message with attachment is visible
  await page.waitForSelector(`.user-message:has-text("Here is an attachment")`, { timeout: 5000 });
  
  // Check if attachment is visible
  const attachmentVisible = await page.isVisible(`.attachment-item:has-text("${this.attachmentName}")`);
  expect(attachmentVisible).toBe(true);
});

// Cross-application synchronization
Given('I create a new chat session in the frontend', async function() {
  const page = await getPage();
  await navigateTo(page, '/chat');
  
  // Click new chat button
  await page.click('button:has-text("New Chat")');
  
  // Wait for new chat session to load
  await page.waitForSelector('.chat-container');
  
  // Store session ID for verification
  this.sessionId = await page.getAttribute('.chat-container', 'data-session-id');
  expect(this.sessionId).not.toBeNull();
});

When('I send a message in the frontend', async function() {
  const page = await getPage();
  this.syncMessage = 'This message should sync between apps';
  
  await page.fill('.chat-input textarea', this.syncMessage);
  await page.click('button.send-button');
  
  // Wait for message to appear
  await page.waitForSelector(`.user-message:has-text("${this.syncMessage}")`, { timeout: 5000 });
});

When('I switch to the UI application', async function() {
  const page = await getPage();
  // Navigate to the legacy UI application
  await navigateTo(page, '/ui/chat');
  
  // Wait for UI application to load
  await page.waitForSelector('.ui-chat-container');
});

Then('I should see the same chat session', async function() {
  const page = await getPage();
  // Find session with the same ID
  const sessionElement = await page.$(`.ui-chat-session[data-session-id="${this.sessionId}"]`);
  expect(sessionElement).not.toBeNull();
  
  // Click on the session
  await sessionElement.click();
  
  // Wait for session to load
  await page.waitForSelector('.ui-chat-messages');
});

Then('I should see the message I sent from the frontend', async function() {
  const page = await getPage();
  // Check if the message is visible in the UI application
  const messageVisible = await page.isVisible(`.ui-user-message:has-text("${this.syncMessage}")`);
  expect(messageVisible).toBe(true);
});

// User preference synchronization
Given('I change theme preference in the frontend', async function() {
  const page = await getPage();
  // Navigate to settings
  await navigateTo(page, '/settings');
  
  // Wait for settings page to load
  await page.waitForSelector('.settings-container');
  
  // Get current theme
  const isDarkMode = await page.isChecked('.theme-toggle');
  this.originalTheme = isDarkMode ? 'dark' : 'light';
  this.newTheme = isDarkMode ? 'light' : 'dark';
  
  // Toggle theme
  await page.click('.theme-toggle');
  
  // Wait for theme to update
  await page.waitForSelector(this.newTheme === 'dark' ? '.dark-theme' : '.light-theme');
});

When('I navigate to the UI application', async function() {
  const page = await getPage();
  // Navigate to the UI application
  await navigateTo(page, '/ui');
  
  // Wait for UI application to load
  await page.waitForSelector('.ui-container');
});

Then('the theme setting should be synchronized', async function() {
  const page = await getPage();
  // Check theme setting in UI application
  const isUiDarkMode = await page.isChecked('.ui-theme-toggle');
  const uiTheme = isUiDarkMode ? 'dark' : 'light';
  
  // Theme should match what we set in the frontend
  expect(uiTheme).toBe(this.newTheme);
});

Then('the UI should display with the same theme', async function() {
  const page = await getPage();
  // Check if UI has the correct theme applied
  const hasExpectedTheme = await page.isVisible(this.newTheme === 'dark' ? '.ui-dark-theme' : '.ui-light-theme');
  expect(hasExpectedTheme).toBe(true);
}); 