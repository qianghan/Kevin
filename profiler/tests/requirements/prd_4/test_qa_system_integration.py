import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
import json
import os
from datetime import datetime

from profiler.services.qa.enhanced_qa_service import EnhancedQAService
from profiler.services.qa.qa_integration_service import QAIntegrationService
from profiler.tests.fixtures.qa_fixtures import qa_test_data, mock_qa_repository
from profiler.tests.fixtures.profile_fixtures import profile_test_data

class TestQAIntegration:
    """Tests for the Q&A integration with other services."""
    
    @pytest.fixture
    def mock_notification_service(self):
        """Create a mock notification service."""
        service = AsyncMock()
        service.send_notification = AsyncMock(return_value={"success": True})
        return service
    
    @pytest.fixture
    def mock_document_service(self):
        """Create a mock document service."""
        service = AsyncMock()
        service.upload_document = AsyncMock(return_value={
            "document_id": "doc123",
            "url": "https://example.com/documents/doc123"
        })
        return service
    
    @pytest.fixture
    def mock_profile_service(self):
        """Create a mock profile service."""
        service = AsyncMock()
        service.get_profile = AsyncMock(return_value={"id": "prof123", "user_id": "user456"})
        service.update_profile = AsyncMock(return_value={"id": "prof123", "updated": True})
        return service
    
    @pytest.fixture
    def mock_analytics_service(self):
        """Create a mock analytics service."""
        service = AsyncMock()
        service.record_event = AsyncMock(return_value={"success": True})
        return service
    
    @pytest.fixture
    def mock_recommendation_service(self):
        """Create a mock recommendation service."""
        service = AsyncMock()
        service.generate_recommendations = AsyncMock(return_value=[
            {"type": "skill", "name": "Learn Python", "description": "Improve your Python skills"},
            {"type": "course", "name": "Advanced Java", "description": "Take an advanced Java course"}
        ])
        return service
    
    @pytest.fixture
    def qa_integration_service(self, mock_qa_repository, mock_notification_service, 
                               mock_document_service, mock_profile_service,
                               mock_analytics_service, mock_recommendation_service):
        """Create a QA integration service with mock dependencies."""
        qa_service = EnhancedQAService(mock_qa_repository)
        return QAIntegrationService(
            qa_service=qa_service,
            notification_service=mock_notification_service,
            document_service=mock_document_service,
            profile_service=mock_profile_service,
            analytics_service=mock_analytics_service,
            recommendation_service=mock_recommendation_service
        )
    
    @pytest.mark.asyncio
    async def test_process_answer_with_notification(self, qa_integration_service):
        """Test processing an answer with notification."""
        answer = "This is a test answer"
        result = await qa_integration_service.process_answer_with_notification("1", answer)
        
        # Verify the answer was processed
        assert result is not None
        assert result.get("answer_text") == answer
        
        # Verify notification was sent
        qa_integration_service.notification_service.send_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_attach_document_to_answer(self, qa_integration_service):
        """Test attaching a document to an answer."""
        # Create a mock file
        mock_file = MagicMock()
        
        result = await qa_integration_service.attach_document_to_answer(
            question_id="1",
            answer_id="answer123",
            document_file=mock_file,
            file_name="test.pdf",
            content_type="application/pdf"
        )
        
        # Verify document was uploaded
        assert result is not None
        assert result.get("document_id") == "doc123"
        
        # Verify document service was called
        qa_integration_service.document_service.upload_document.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_export_qa_session_to_profile(self, qa_integration_service):
        """Test exporting a Q&A session to a profile."""
        result = await qa_integration_service.export_qa_session_to_profile("prof123")
        
        # Verify profile was updated
        assert result is not None
        assert result.get("success") is True
        assert result.get("profile_id") == "prof123"
        
        # Verify profile service was called
        qa_integration_service.profile_service.update_profile.assert_called_once()
        
        # Verify analytics were recorded
        qa_integration_service.analytics_service.record_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_qa_history(self, qa_integration_service):
        """Test tracking Q&A history."""
        result = await qa_integration_service.track_qa_history("prof123")
        
        # Verify history was tracked
        assert result is not None
        assert result.get("profile_id") == "prof123"
        assert "metrics" in result
        assert "history" in result
        
        # Verify analytics were recorded
        qa_integration_service.analytics_service.record_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_qa_analytics(self, qa_integration_service):
        """Test generating Q&A analytics."""
        result = await qa_integration_service.generate_qa_analytics("prof123")
        
        # Verify analytics were generated
        assert result is not None
        assert "total_questions" in result
        assert "answered_questions" in result
        
        # Verify analytics were recorded
        qa_integration_service.analytics_service.record_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_integrate_with_recommendations(self, qa_integration_service):
        """Test integrating with recommendations."""
        result = await qa_integration_service.integrate_with_recommendations("prof123")
        
        # Verify recommendations were generated
        assert result is not None
        assert result.get("success") is True
        assert result.get("profile_id") == "prof123"
        assert result.get("recommendations_generated") == 2
        
        # Verify recommendation service was called
        qa_integration_service.recommendation_service.generate_recommendations.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_extracted_structured_data(self, qa_integration_service):
        """Test extracting structured data from a Q&A session."""
        # Create a mock Q&A session
        qa_session = {
            "profile_id": "prof123",
            "exported_at": datetime.now().isoformat(),
            "questions_count": 3,
            "answered_count": 3,
            "history": [
                {
                    "id": "q1",
                    "category": "professional",
                    "text": "What is your job title?",
                    "answer": {
                        "text": "I am a Software Engineer",
                        "extracted_information": {
                            "job_titles": ["Software Engineer"],
                            "years_of_experience": 5
                        }
                    }
                },
                {
                    "id": "q2",
                    "category": "education",
                    "text": "What degree do you have?",
                    "answer": {
                        "text": "I have a Bachelor of Science in Computer Science from Tech University",
                        "extracted_information": {
                            "degrees": ["Bachelor of Science"],
                            "institutions": ["Tech University"]
                        }
                    }
                },
                {
                    "id": "q3",
                    "category": "skills",
                    "text": "What are your main skills?",
                    "answer": {
                        "text": "Python, Java, and SQL",
                        "extracted_information": {
                            "skills": [
                                {"name": "python", "proficiency": 0.8},
                                {"name": "java", "proficiency": 0.7},
                                {"name": "sql", "proficiency": 0.9}
                            ]
                        }
                    }
                }
            ],
            "analytics": {}
        }
        
        structured_data = qa_integration_service._extract_structured_data_from_session(qa_session)
        
        # Verify structured data
        assert structured_data is not None
        assert "professional" in structured_data
        assert "education" in structured_data
        assert "skills" in structured_data
        
        assert structured_data["professional"].get("job_titles") == ["Software Engineer"]
        assert structured_data["professional"].get("years_experience") == 5
        assert structured_data["education"].get("degrees") == ["Bachelor of Science"]
        assert structured_data["education"].get("institutions") == ["Tech University"]
        assert len(structured_data["skills"]) == 3 