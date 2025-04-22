Feature: Test Mode Management
  As an admin
  I want to assign test mode to users
  So they can access beta services without affecting production data

  Background:
    Given the following users exist:
      | email           | name         | role    | testMode |
      | admin@test.com  | Admin User   | admin   | false    |
      | test1@test.com  | Test User 1  | student | true     |
      | test2@test.com  | Test User 2  | parent  | true     |
      | normal@test.com | Normal User  | student | false    |
  
  Scenario: Admin enables test mode for a user
    Given I am logged in as "admin@test.com"
    When I set test mode to "enabled" for user "normal@test.com"
    Then the user "normal@test.com" should have test mode enabled
  
  Scenario: Admin disables test mode for a user
    Given I am logged in as "admin@test.com"
    When I set test mode to "disabled" for user "test1@test.com"
    Then the user "test1@test.com" should have test mode disabled
  
  Scenario: Admin views all test mode users
    Given I am logged in as "admin@test.com"
    When I view all test mode users
    Then I should see 2 users in the list
    And I should see "test1@test.com" in the list
    And I should see "test2@test.com" in the list
    But I should not see "normal@test.com" in the list
  
  Scenario: Non-admin user attempts to enable test mode
    Given I am logged in as "normal@test.com"
    When I attempt to set test mode to "enabled" for user "normal@test.com"
    Then I should be denied access
  
  Scenario: Non-admin user attempts to view test mode users
    Given I am logged in as "normal@test.com"
    When I attempt to view all test mode users
    Then I should be denied access 