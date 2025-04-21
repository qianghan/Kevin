"""Q&A test fixtures."""

import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_qa_repository():
    """Create a mock QA repository for testing."""
    mock_repo = MagicMock()
    
    # Configure mock methods
    mock_repo.get_questions_for_profile.return_value = [
        {"id": "q1", "text": "Tell me about your technical skills", "category": "skills", "importance": 0.9},
        {"id": "q2", "text": "Describe your work experience", "category": "professional", "importance": 0.8},
        {"id": "q3", "text": "What education do you have?", "category": "education", "importance": 0.7}
    ]
    
    mock_repo.get_answers_for_profile.return_value = [
        {"id": "a1", "question_id": "q1", "answer_text": "I know Python, JavaScript, and React", "quality_score": 0.7},
        {"id": "a2", "question_id": "q2", "answer_text": "I worked at Company X for 5 years", "quality_score": 0.8}
    ]
    
    return mock_repo

@pytest.fixture
def qa_test_data():
    """Provide test data for Q&A tests."""
    return {
        "questions": [
            {
                "id": "q1",
                "text": "Tell me about your technical skills",
                "category": "skills",
                "importance": 0.9
            },
            {
                "id": "q2",
                "text": "Describe your work experience",
                "category": "professional",
                "importance": 0.8
            },
            {
                "id": "q3",
                "text": "What education do you have?",
                "category": "education",
                "importance": 0.7
            }
        ],
        "answers": [
            {
                "id": "a1",
                "question_id": "q1",
                "answer_text": "I know Python, JavaScript, and React",
                "quality_score": 0.7
            },
            {
                "id": "a2",
                "question_id": "q2",
                "answer_text": "I worked at Company X for 5 years",
                "quality_score": 0.8
            }
        ],
        "profiles": [
            {
                "id": "p1",
                "name": "Test User",
                "email": "test@example.com",
                "skills": ["Python", "JavaScript", "React"],
                "experience": [{"company": "Company X", "years": 5}],
                "education": [{"degree": "Bachelor's", "field": "Computer Science"}]
            }
        ]
    } 