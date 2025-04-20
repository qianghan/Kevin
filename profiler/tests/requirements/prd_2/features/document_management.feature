
Feature: Document Management
  As a user of the Profiler application
  I want to manage documents efficiently and securely
  So that I can store, retrieve, and organize my important documents

  Background:
    Given I have a user with id "test_user"
    
  Scenario: Creating and retrieving a document
    Given I have a document titled "Test Document" with content "This is a test document"
    When I save the document to the repository
    And I retrieve the document with id "{document.id}"
    Then the document should be saved successfully
    And I should get the document with title "Test Document"
    
  Scenario: Listing documents
    Given I have a document titled "Document 1" with content "Content 1"
    And I have a document titled "Document 2" with content "Content 2"
    When I save the document to the repository
    And I list all documents
    Then I should get 2 documents
    
  Scenario: Document versioning
    Given I have a document titled "Versioned Document" with content "Original content"
    When I save the document to the repository
    And I create a new version of the document with content "Updated content"
    Then the document should have 1 versions
    
  Scenario: Document deletion
    Given I have a document titled "Temporary Document" with content "Will be deleted"
    When I save the document to the repository
    And I delete the document
    Then the document should not exist
    
  Scenario: Document access control
    Given I have a document titled "Private Document" with content "Confidential information"
    And I have an access control list for the document
    When I save the document to the repository
    And I grant access to user "authorized_user"
    And I check if user "authorized_user" can access the document
    Then user "authorized_user" should be able to access the document
    When I check if user "unauthorized_user" can access the document
    Then user "unauthorized_user" should not be able to access the document
    
  Scenario: Document search
    Given I have a document titled "Searchable Document" with content "Contains specific keywords for searching"
    When I save the document to the repository
    And I search for documents with term "specific keywords"
    Then I should get 1 search results
    
  Scenario: Document backup and restore
    Given I have a document titled "Important Document" with content "Critical information"
    When I save the document to the repository
    And I create a backup of all documents
    Then the backup should be created successfully
    When I restore documents from the backup
    Then the documents should be restored successfully
    