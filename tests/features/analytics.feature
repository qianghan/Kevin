Feature: User Analytics and Reporting
  As an administrator or teacher
  I want to track and analyze user activity and engagement
  So that I can make data-driven decisions and improve user experience

  Scenario: Admin can view user activity dashboard
    Given I am logged in as an "ADMIN" user
    When I navigate to the analytics dashboard
    Then I should see user activity metrics
    And I should see active user counts
    And I should see usage trends

  Scenario: Admin can view engagement metrics
    Given I am logged in as an "ADMIN" user
    When I view the engagement metrics page
    Then I should see session duration statistics
    And I should see feature usage statistics
    And I should see user retention data

  Scenario: Admin can generate user reports
    Given I am logged in as an "ADMIN" user
    When I access the reporting interface
    And I select a report type "user_activity"
    And I set the date range for the report
    Then I should be able to generate the report
    And I should see the report preview

  Scenario: Teacher can view student engagement
    Given I am logged in as a "TEACHER" user
    When I view the student analytics page
    Then I should see student engagement metrics
    And I should see learning progress data

  Scenario: Export analytics data with privacy controls
    Given I am logged in as an "ADMIN" user
    When I export analytics data
    Then the exported data should be anonymized
    And sensitive information should be redacted

  Scenario: Analytics data respects user privacy settings
    Given a user has disabled analytics tracking
    When analytics data is collected
    Then that user's data should not be included
    And their privacy preferences should be respected

  Scenario: Switch between different analytics providers
    Given I am logged in as an "ADMIN" user
    When I switch the analytics provider to "mock_provider"
    Then the analytics data should still be available
    And the interface should remain consistent 