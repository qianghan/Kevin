Feature: Authentication Workflows
  As a user
  I want to be able to authenticate with the system
  So that I can access protected resources

  Scenario: User logs in with valid credentials
    Given I am on the login page
    When I enter valid credentials
    And I click the login button
    Then I should be redirected to the dashboard

  Scenario: User sees error with invalid credentials
    Given I am on the login page
    When I enter invalid credentials
    And I click the login button
    Then I should see an error message

  Scenario: User can register a new account
    Given I am on the registration page
    When I fill in the registration form with valid data
    And I click the register button
    Then I should see a success message
    And I should receive a verification email

  Scenario: User can request a password reset
    Given I am on the password reset page
    When I enter my email address
    And I click the reset password button
    Then I should see a confirmation message
    And I should receive a password reset email

  Scenario: User can verify their email
    Given I have received a verification email
    When I click the verification link
    Then I should be redirected to the email verified page
    And my account should be marked as verified

  Scenario: User can reset their password with a token
    Given I have received a password reset email
    When I click the password reset link
    And I enter a new password
    And I click the submit button
    Then I should be redirected to the login page
    And I should be able to login with my new password 