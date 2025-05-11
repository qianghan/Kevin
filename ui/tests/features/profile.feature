Feature: User Profile Management
  As a user
  I want to be able to manage my profile information
  So that I can keep my personal details up to date

  Scenario: User can view their profile information
    Given I am logged in as a user
    When I navigate to the profile page
    Then I should see my profile information

  Scenario: User can update their profile information
    Given I am logged in as a user
    When I navigate to the profile page
    And I update my profile information
    And I save my changes
    Then my profile should be updated successfully

  Scenario: User can change their profile picture
    Given I am logged in as a user
    When I navigate to the profile page
    And I upload a new profile picture
    Then my profile picture should be updated

  Scenario: User can see profile completeness indicator
    Given I am logged in as a user
    When I navigate to the profile page
    Then I should see my profile completeness indicator

  Scenario: User can change their email address
    Given I am logged in as a user
    When I navigate to the profile page
    And I change my email address
    Then I should receive a profile email verification
    And my email should be updated after verification

  Scenario: User can change their theme preferences
    Given I am logged in as a user
    When I navigate to the preferences page
    And I change my theme preference
    Then my theme settings should be updated

  Scenario: User can export their profile data
    Given I am logged in as a user
    When I navigate to the profile page
    And I request a profile data export
    Then I should receive my profile data in the requested format 