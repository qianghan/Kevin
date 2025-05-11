Feature: Role-Based Access Control
  As an administrator
  I want to control access to features based on user roles
  So that users can only access what they're authorized to see

  Scenario: Admin can access administrative features
    Given I am logged in as an "ADMIN" user
    When I navigate to the admin dashboard
    Then I should see the admin management options

  Scenario: Teacher can access teacher-specific features
    Given I am logged in as a "TEACHER" user
    When I navigate to the course management page
    Then I should see the teaching management options
    And I should not see the admin management options

  Scenario: Student can access student-specific features
    Given I am logged in as a "STUDENT" user
    When I navigate to the learning dashboard
    Then I should see the student learning options
    And I should not see the teaching management options

  Scenario: User roles determine UI element visibility
    Given I am logged in as a "STUDENT" user
    When I view the application header
    Then I should see navigation for "student" permissions
    And I should not see navigation for "admin" permissions

  Scenario: User with multiple roles has combined permissions
    Given I am logged in as a user with roles "TEACHER,STUDENT" 
    When I navigate to the course management page
    Then I should see the teaching management options
    And I should also see student-specific elements

  Scenario: Permission checks work with component-level guards
    Given I am logged in as a "STUDENT" user
    When I attempt to access a protected component
    Then I should be shown an "access denied" message

  Scenario: Admin can manage user roles
    Given I am logged in as an "ADMIN" user
    When I navigate to the user management page
    And I select a user to edit
    Then I should be able to modify their roles 