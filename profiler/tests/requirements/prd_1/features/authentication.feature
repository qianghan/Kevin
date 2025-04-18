Feature: User Authentication
  As a user of the Profiler application
  I want to securely authenticate and manage my session
  So that my data remains private and secure

  Scenario: New user registration
    Given a new user with valid credentials
    When the user registers with the system
    Then the user account should be created
    And the user should be able to authenticate

  Scenario: User authentication with valid credentials
    Given an existing user
    When the user logs in with valid credentials
    Then authentication should succeed
    And a session token should be generated

  Scenario: User authentication with invalid credentials
    Given an existing user
    When the user logs in with invalid credentials
    Then authentication should fail
    And no session token should be generated

  Scenario: User session management
    Given an authenticated user
    When the user's session is created
    Then the session should be retrievable
    And the session can be invalidated
