Feature: Chat Integration
  As a user of the KAI application
  I want to send messages in a chat session
  So that I can interact with the AI assistant

  Background:
    Given I am logged in as a test user
    And I have an active chat session

  Scenario: Send a message using the frontend
    When I type "Hello KAI" in the chat input
    And I submit the message
    Then I should see my message in the chat history
    And I should receive a response from KAI

  Scenario: Chat session persists between page reloads
    When I send several messages in a chat session
    And I reload the page
    Then I should see my previous messages
    And the chat session should maintain continuity

  Scenario: Attachments are properly handled
    When I attach a file to my message
    And I submit the message with the attachment
    Then the attachment should be uploaded successfully
    And the message with attachment should appear in the chat history

  Scenario: Chat sessions are synchronized across UI and frontend
    Given I create a new chat session in the frontend
    When I send a message in the frontend
    And I switch to the UI application
    Then I should see the same chat session
    And I should see the message I sent from the frontend

  Scenario: User preferences are synchronized between services
    Given I change theme preference in the frontend
    When I navigate to the UI application
    Then the theme setting should be synchronized
    And the UI should display with the same theme 