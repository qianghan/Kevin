Feature: Theme System
  As a user
  I want the application to have consistent theming
  So that I can have a pleasant visual experience

  Scenario: Default theme matches KAI branding
    Given I load the application
    Then the primary color should be "#4FDBA9"
    And the background color should be "#0A1723"
    
  Scenario: Theme switching works correctly
    Given I load the application
    When I switch to "dark" theme
    Then the background color should be "#0A1723"
    When I switch to "light" theme
    Then the background color should be "#FFFFFF"

  Scenario: Theme respects accessibility guidelines
    Given I load the application
    Then all text should have sufficient contrast ratio
    And interactive elements should have visible focus states 