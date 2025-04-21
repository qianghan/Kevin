Feature: Interactive Q&A System
  As a user of the profiling system
  I want an interactive Q&A system
  So that I can build my profile through a guided interview process

  Background:
    Given a user with a profile
    And a mock QA repository

  Scenario: Generate questions based on a user's profile
    When the system generates questions based on the profile
    Then the generated questions should be relevant to the profile

  Scenario: Answer processing
    Given a set of predefined questions
    When the user answers a question with "Sample answer"
    Then the system should process the answer correctly

  Scenario: Follow-up questions
    Given a set of predefined questions
    When the user answers a question with "Sample answer that triggers follow-up"
    And the system processes follow-up questions
    Then the system should generate appropriate follow-up questions

  Scenario: Feedback collection
    Given a set of predefined questions
    When the user answers a question with "Sample answer"
    And the user provides feedback on an answer
    Then the feedback should be stored and associated with the answer 