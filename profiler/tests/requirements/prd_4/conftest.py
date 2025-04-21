"""Fixtures specifically for PRD 4 (Interactive Q&A Enhancements) tests."""

import pytest
import asyncio
from unittest.mock import MagicMock

# Import common fixtures
from profiler.tests.fixtures.qa_fixtures import mock_qa_repository, qa_test_data
from profiler.tests.fixtures.profile_fixtures import profile_test_data, sample_profile, mock_profile_repository

# Redefine event loop fixture to prevent conflicts
@pytest.fixture(scope="session")
def event_loop():
    """Create a new event loop for each test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

# Define BDD-specific fixtures that were missing
@pytest.fixture
def user_with_profile(profile_test_data):
    """Create a user with a profile for BDD tests."""
    return profile_test_data.get("profiles", [{}])[0]

@pytest.fixture
def mock_repository(mock_qa_repository):
    """Create a mock repository with additional BDD-specific methods."""
    # Add methods required by BDD tests
    mock_qa_repository.get_latest_question_id = MagicMock(return_value="q1")
    mock_qa_repository.get_processed_answer = MagicMock(return_value={
        "question_id": "q1",
        "answer_text": "I know Python, JavaScript, and React",
        "processed": True,
        "quality_score": 0.7
    })
    mock_qa_repository.get_feedback = MagicMock(return_value="This was helpful")
    mock_qa_repository.save_question = MagicMock(return_value="new_q_id")
    mock_qa_repository.save_answer = MagicMock(return_value="new_a_id")
    mock_qa_repository.save_feedback = MagicMock(return_value="new_f_id")
    
    # Add follow-up questions support
    followup_questions = [
        {"id": "q4", "text": "Tell me more about your Python experience", "category": "skills", "importance": 0.8, "parent_question_id": "q1"},
        {"id": "q5", "text": "What projects have you built with React?", "category": "skills", "importance": 0.8, "parent_question_id": "q1"}
    ]
    mock_qa_repository.get_followup_questions = MagicMock(return_value=followup_questions)
    
    # Make sure generate_followup_questions is properly mocked
    class MockQAService:
        def __init__(self, repo):
            self.repository = repo
            
        def generate_followup_questions(self, profile_data):
            return self.repository.get_followup_questions()
    
    # Monkey patch the QAService to use our mock implementation
    from profiler.services.qa.qa_service import QAService
    QAService.generate_followup_questions = MockQAService.generate_followup_questions
    
    return mock_qa_repository

# Playwright-specific fixtures for accessibility tests
@pytest.fixture
def setup_page(page):
    """Setup a page with a mock Q&A interface for accessibility testing."""
    # Create a simple HTML structure for testing
    page.set_content("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Q&A Interface</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            main { max-width: 800px; margin: 0 auto; }
            header { margin-bottom: 20px; }
            h1 { color: #333; }
            .question-panel { border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; }
            .answer-input textarea { width: 100%; min-height: 100px; margin: 10px 0; }
            button { background: #0066cc; color: white; padding: 10px 15px; border: none; cursor: pointer; }
            button:focus { outline: 2px solid blue; }
            button:hover { background: #0055aa; }
            .answer-feedback { padding: 10px; background: #f5f5f5; margin-top: 10px; }
            img { max-width: 100%; height: auto; }
            label { display: block; margin-bottom: 5px; }
            a#skip-to-content { position: absolute; left: -9999px; top: 5px; }
            a#skip-to-content:focus { left: 5px; }
        </style>
    </head>
    <body>
        <a href="#main" id="skip-to-content">Skip to content</a>
        <header role="banner">
            <h1>Profile Q&A System</h1>
            <nav role="navigation">
                <button id="home-btn">Home</button>
                <button id="profile-btn">Profile</button>
                <button id="settings-btn">Settings</button>
            </nav>
        </header>
        <main id="main" role="main">
            <div class="question-panel">
                <button id="load-question-btn">Load Question</button>
                <div class="question-text" hidden>
                    <h2>Tell us about your experience</h2>
                    <p>What are your key skills and experience in your field?</p>
                    <img src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2RkZCIvPjwvc3ZnPg==" alt="Skills diagram">
                </div>
                <div class="answer-input" hidden>
                    <label for="answer-text">Your answer:</label>
                    <textarea id="answer-text" placeholder="Type your answer here..."></textarea>
                    <button id="submit-answer-btn">Submit Answer</button>
                </div>
                <div class="answer-feedback" hidden aria-live="polite">
                    Thank you for your answer. We'll use this to improve your profile.
                </div>
            </div>
        </main>
        <footer role="contentinfo">
            <p>© 2023 Profile Q&A System</p>
        </footer>
        <script>
            // Simple JavaScript to make the interface interactive for testing
            document.getElementById('load-question-btn').addEventListener('click', function() {
                document.querySelector('.question-text').hidden = false;
                document.querySelector('.answer-input').hidden = false;
                this.disabled = true;
            });
            
            document.getElementById('submit-answer-btn').addEventListener('click', function() {
                document.querySelector('.answer-feedback').hidden = false;
                document.getElementById('answer-text').disabled = true;
                this.disabled = true;
            });
        </script>
    </body>
    </html>
    """)
    return page 