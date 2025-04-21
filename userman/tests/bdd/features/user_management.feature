Feature: User Management
  As a user of the Kevin system
  I want to manage my account and profile
  So that I can personalize my experience and maintain security

  Background:
    Given the user management system is initialized
    And the database is connected

  Scenario: User Registration
    When a user registers with name "John Doe", email "john@example.com", and password "SecurePass123"
    Then the registration should be successful
    And the user should be stored in the database
    And the password should be securely hashed

  Scenario: User Login
    Given a user exists with email "john@example.com" and password "SecurePass123"
    When the user attempts to login with email "john@example.com" and password "SecurePass123"
    Then the login should be successful
    And the user profile should be returned

  Scenario: Failed Login with Incorrect Password
    Given a user exists with email "john@example.com" and password "SecurePass123"
    When the user attempts to login with email "john@example.com" and password "WrongPassword"
    Then the login should fail

  Scenario: Update User Profile
    Given a user is authenticated with ID "user123"
    When the user updates their profile with name "John Updated"
    Then the profile should be updated in the database
    And the updated profile should be returned

  Scenario: Get User Preferences
    Given a user is authenticated with ID "user123"
    When the user requests their preferences
    Then the preferences should be returned

  Scenario: Update User Preferences
    Given a user is authenticated with ID "user123"
    When the user updates their preferences with theme "dark"
    Then the preferences should be updated in the database
    And the updated preferences should be returned

  Scenario: Change Password
    Given a user is authenticated with ID "user123"
    When the user changes their password from "OldPass123" to "NewPass456"
    Then the password change should be successful
    And the new password should be securely hashed

  Scenario: Change Email
    Given a user is authenticated with ID "user123"
    When the user changes their email to "newemail@example.com" with password "SecurePass123"
    Then the email change should be successful
    And the user should have the new email in the database

  Scenario: Link Parent-Student Account
    Given a parent user exists with ID "parent123"
    And a student user exists with ID "student456"
    When the parent links the student account
    Then the accounts should be linked in the database
    And the student should appear in the parent's student list
    And the parent should appear in the student's parent list

  Scenario: Search for Users
    Given multiple users exist in the system
    When a user searches for "john"
    Then the search results should include users with "john" in their name or email
    And the search results should not include the searching user 