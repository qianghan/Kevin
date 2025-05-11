Feature: Account Relationships
  As a user with a specific role
  I want to manage relationships with other users
  So that I can establish appropriate connections and access controls

  Scenario: Parent can link to student accounts
    Given I am logged in as a "PARENT" user for relationship management
    When I navigate to the relationship management page
    Then I should see the option to link to a student account

  Scenario: Parent can send invitation to create a relationship
    Given I am logged in as a "PARENT" user for relationship management
    When I navigate to the relationship management page
    And I initiate linking to a student with email "student@example.com"
    Then an invitation should be sent to the student
    And I should see the pending invitation in my dashboard

  Scenario: Student can accept a parent relationship invitation
    Given I am logged in as a "STUDENT" user for relationship management
    And I have a pending relationship invitation from a parent
    When I view my invitations
    And I accept the parent relationship invitation
    Then the relationship should be established
    And I should see the parent listed in my relationships

  Scenario: Parent can view student information after relationship is established
    Given I am logged in as a "PARENT" user for relationship management
    And I have an established relationship with a student
    When I view the student's profile
    Then I should see the student's academic information
    And I should see the student's progress reports

  Scenario: Admin can manage any relationship
    Given I am logged in as an "ADMIN" user for relationship management
    When I navigate to the relationship management page
    Then I should see all user relationships
    And I should be able to create, edit, or remove relationships

  Scenario: Teacher can view student relationships
    Given I am logged in as a "TEACHER" user for relationship management
    When I view a student's profile
    Then I should see the student's parent relationships

  Scenario: User can remove an established relationship
    Given I am logged in as a "PARENT" user for relationship management
    And I have an established relationship with a student
    When I remove the relationship
    Then the relationship should be deleted
    And I should no longer have access to the student's information 