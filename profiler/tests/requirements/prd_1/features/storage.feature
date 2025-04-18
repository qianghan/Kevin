Feature: Persistent Storage
  As a developer of the Profiler application
  I want to store and retrieve user profiles securely
  So that user data persists across sessions

  Background:
    Given a user named "testuser"

  Scenario: Creating a new profile
    When I create a profile with name "Test Profile"
    Then the profile "Test Profile" should exist

  Scenario: Updating a profile
    Given a profile with name "Update Test"
    When I update the profile "Update Test" with data "bio" = "Updated biography"
    Then the profile "Update Test" should have data "bio" = "Updated biography"

  Scenario: Retrieving a profile
    Given a profile with name "Retrieve Test"
    When I retrieve the profile "Retrieve Test"
    Then the profile "Retrieve Test" should exist

  Scenario: Deleting a profile
    Given a profile with name "Delete Test"
    When I delete the profile "Delete Test"
    Then the profile "Delete Test" should not exist

  Scenario: Listing user profiles
    Given a profile with name "List Test 1"
    And a profile with name "List Test 2"
    When I list profiles for user "testuser"
    Then I should get 2 profiles
    And all profiles should belong to user "testuser"

  Scenario: Listing all profiles
    Given a profile with name "ListTest1"
    And a profile with name "ListTest2"
    When I list all profiles
    Then I should get at least 2 profiles

  Scenario: Profile ownership
    Given a user named "alice"
    And a user named "bob"
    When I create a profile with name "AliceProfile1"
    And I create a profile with name "AliceProfile2"
    And I list profiles for user "alice"
    Then I should get 2 profiles
    And all profiles should belong to user "alice"
    And user "bob" should have 0 profiles
    
  Scenario: Multiple users with profiles
    Given a user named "user1"
    And a user named "user2"
    When I create a profile with name "User1Profile"
    And I create a profile with name "User1ProfileSecond"
    Then user "user1" should have 2 profiles
    And user "user2" should have 0 profiles 