Feature: Chat State Management
  As a user of the KAI application
  I want to have a reliable chat state management system
  So that I can have coherent and persistent conversations

  Background:
    Given the chat service adapter is initialized
    And the chat context is provided

  Scenario: Loading existing chat sessions
    When I load the list of chat sessions
    Then my existing sessions should be displayed
    And the sessions should be in chronological order

  Scenario: Creating a new chat session
    When I create a new chat session
    Then a new session should be added to my list of sessions
    And the new session should be set as the current session
    And the new session should have a default name

  Scenario: Creating a named chat session
    When I create a new chat session with name "Test Session"
    Then a new session should be added to my list of sessions
    And the new session should have the name "Test Session"

  Scenario: Loading a specific chat session
    Given I have at least 2 existing chat sessions
    When I load a specific chat session
    Then that session should become the current session
    And all messages in that session should be loaded

  Scenario: Sending a message in a chat session
    Given I have an active chat session
    When I send a message "Hello, KAI!"
    Then the message should be added to the current session
    And the UI should show a loading state while waiting for a response
    And the response should be added to the session when received

  Scenario: Handling concurrent sessions
    Given I have multiple active chat sessions
    When I switch between sessions
    Then each session should maintain its separate state
    And messages from one session should not appear in another

  Scenario: Syncing with backend state
    Given I have an active chat session
    And changes are made to the session in the backend
    When the session is refreshed
    Then the local state should reflect the backend changes

  Scenario: Handling errors in chat operations
    Given the chat service encounters an error
    When I perform a chat operation
    Then an appropriate error message should be displayed
    And the system should attempt to recover gracefully

  Scenario: Service compatibility with UI implementation
    Given both UI and frontend implementations are available
    When I use the chat adapter service
    Then operations should work with either implementation
    And data formats should be compatible between systems 