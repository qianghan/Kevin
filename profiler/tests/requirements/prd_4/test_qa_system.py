import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import MagicMock, patch

# Import test fixtures
from profiler.tests.fixtures.qa_fixtures import qa_test_data, mock_qa_repository
from profiler.tests.fixtures.profile_fixtures import profile_test_data

# Import the service interfaces that will be implemented
from profiler.services.qa.qa_service_interface import QAServiceInterface
from profiler.services.qa.qa_service import QAService

# Define the feature file location
scenarios('features/qa_system.feature')

# Given steps
@given("a user with a profile")
def user_with_profile(profile_test_data):
    return profile_test_data

@given("a set of predefined questions")
def predefined_questions(qa_test_data):
    return qa_test_data.get('predefined_questions')

@given("a mock QA repository")
def mock_repository(mock_qa_repository):
    return mock_qa_repository

# When steps
@when("the system generates questions based on the profile")
def system_generates_questions(user_with_profile, mock_repository):
    qa_service = QAService(mock_repository)
    return qa_service.generate_questions(user_with_profile)

@when(parsers.parse("the user answers a question with \"{answer}\""))
def user_answers_question(mock_repository, answer):
    qa_service = QAService(mock_repository)
    question_id = mock_repository.get_latest_question_id()
    return qa_service.process_answer(question_id, answer)

@when("the system processes follow-up questions")
def system_processes_followup(mock_repository, user_with_profile):
    qa_service = QAService(mock_repository)
    return qa_service.generate_followup_questions(user_with_profile)

@when("the user provides feedback on an answer")
def user_provides_feedback(mock_repository):
    qa_service = QAService(mock_repository)
    question_id = mock_repository.get_latest_question_id()
    return qa_service.process_feedback(question_id, "This was helpful")

# Then steps
@then("the generated questions should be relevant to the profile")
def verify_relevant_questions(mock_repository, user_with_profile):
    qa_service = QAService(mock_repository)
    questions = qa_service.generate_questions(user_with_profile)
    assert len(questions) > 0
    # Additional assertions to check relevance would go here

@then("the system should process the answer correctly")
def verify_answer_processing(mock_repository):
    qa_service = QAService(mock_repository)
    question_id = mock_repository.get_latest_question_id()
    processed_answer = mock_repository.get_processed_answer(question_id)
    assert processed_answer is not None
    
@then("the system should generate appropriate follow-up questions")
def verify_followup_questions(mock_repository, user_with_profile):
    qa_service = QAService(mock_repository)
    followups = qa_service.generate_followup_questions(user_with_profile)
    assert len(followups) > 0
    
@then("the feedback should be stored and associated with the answer")
def verify_feedback_storage(mock_repository):
    qa_service = QAService(mock_repository)
    question_id = mock_repository.get_latest_question_id()
    feedback = mock_repository.get_feedback(question_id)
    assert feedback is not None 