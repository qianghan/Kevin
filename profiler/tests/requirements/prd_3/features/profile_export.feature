Feature: Profile Export
  As a user of the Profiler application
  I want to export my profile in different formats
  So that I can share it, print it, or use it in other applications

  Background:
    Given I have a user account
    And I have a profile with complete information
    
  Scenario: Exporting profile as PDF
    Given I have selected the PDF export format
    When I choose a template for my profile
    And I customize export options
    And I initiate the export process
    Then I should receive a PDF file containing my profile information
    And the PDF should match the selected template
    And the PDF should include all required profile sections
    
  Scenario: Exporting profile as Word document
    Given I have selected the Word document export format
    When I choose a template for my profile
    And I customize export options
    And I initiate the export process
    Then I should receive a Word document containing my profile information
    And the Word document should match the selected template
    And the Word document should include all required profile sections
    
  Scenario: Exporting profile as JSON
    Given I have selected the JSON export format
    When I initiate the export process
    Then I should receive a JSON file containing my profile information
    And the JSON should have the correct schema
    And the JSON should include all profile data
    
  Scenario: Previewing profile before export
    Given I have selected an export format
    And I have chosen a template
    When I request a preview
    Then I should see a preview of my profile
    And the preview should match the selected template
    And the preview should include all required profile sections
    
  Scenario: Sharing profile with other users
    Given I have exported my profile
    When I select sharing options
    And I enter recipient information
    And I set access permissions
    And I initiate the sharing process
    Then the recipients should receive access to my profile
    And the recipients should have the permissions I specified
    
  Scenario: Profile export with custom template
    Given I have created a custom template
    When I select my custom template
    And I initiate the export process
    Then the exported profile should use my custom template
    
  Scenario: Accessing shared profile
    Given another user has shared their profile with me
    When I access the shared profile link
    Then I should be able to view the shared profile
    And the profile should have the format specified by the owner 