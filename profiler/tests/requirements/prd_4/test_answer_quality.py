import pytest
from unittest.mock import MagicMock, patch

from profiler.services.qa.enhanced_qa_service import EnhancedQAService
from profiler.services.qa.qa_integration_service import QAIntegrationService
from profiler.tests.fixtures.qa_fixtures import mock_qa_repository

class TestAnswerQuality:
    """Tests for answer quality assessment functionality."""
    
    @pytest.fixture
    def enhanced_qa_service(self, mock_qa_repository):
        """Create an enhanced QA service with a mock repository."""
        return EnhancedQAService(mock_qa_repository)
    
    @pytest.fixture
    def qa_integration_service(self, mock_qa_repository):
        """Create a QA integration service with a mock repository."""
        return QAIntegrationService(mock_qa_repository)
    
    @pytest.fixture
    def sample_question(self):
        """Create a sample question for testing."""
        return {
            "id": "q123",
            "text": "What are your technical skills?",
            "category": "skills",
            "importance": 0.8,
            "profile_id": "profile123"
        }
    
    @pytest.fixture
    def sample_answers(self):
        """Create sample answers with varying quality."""
        return {
            "high_quality": {
                "id": "ans1",
                "question_id": "q123",
                "answer_text": "I have 5 years of experience with Python, specializing in Django and Flask frameworks. I'm also proficient in JavaScript (React and Node.js), SQL, and have worked extensively with AWS services including Lambda, S3, and EC2. Recently, I've been learning Rust and contributing to open-source projects.",
                "profile_id": "profile123"
            },
            "medium_quality": {
                "id": "ans2",
                "question_id": "q123",
                "answer_text": "I know Python, JavaScript and some AWS. I've used SQL databases before.",
                "profile_id": "profile123"
            },
            "low_quality": {
                "id": "ans3",
                "question_id": "q123",
                "answer_text": "coding",
                "profile_id": "profile123"
            }
        }

    def test_evaluate_answer_quality(self, enhanced_qa_service, sample_question, sample_answers):
        """Test evaluation of answer quality."""
        # Test with high quality answer
        high_quality_result = enhanced_qa_service.evaluate_answer_quality(
            sample_question, 
            sample_answers["high_quality"]["answer_text"]
        )
        
        # Test with medium quality answer
        medium_quality_result = enhanced_qa_service.evaluate_answer_quality(
            sample_question, 
            sample_answers["medium_quality"]["answer_text"]
        )
        
        # Test with low quality answer
        low_quality_result = enhanced_qa_service.evaluate_answer_quality(
            sample_question, 
            sample_answers["low_quality"]["answer_text"]
        )
        
        # Assertions
        assert "quality_score" in high_quality_result, "Should return quality score"
        assert "extracted_information" in high_quality_result, "Should return extracted information"
        assert "feedback" in high_quality_result, "Should return feedback"
        
        assert high_quality_result["quality_score"] > medium_quality_result["quality_score"], "High quality should score better than medium"
        assert medium_quality_result["quality_score"] > low_quality_result["quality_score"], "Medium quality should score better than low"
        
        # Check extracted information
        assert len(high_quality_result["extracted_information"]) > len(low_quality_result["extracted_information"]), "Should extract more info from high quality"
        
        # Check feedback
        assert len(low_quality_result["feedback"]) > 0, "Should provide feedback for low quality answers"
    
    def test_extract_key_information(self, enhanced_qa_service, sample_question, sample_answers):
        """Test extraction of key information from answers."""
        # Extract from high quality answer
        extracted = enhanced_qa_service._extract_key_information(
            sample_question, 
            sample_answers["high_quality"]["answer_text"]
        )
        
        # Assertions for technical skills question
        assert "skills" in extracted, "Should extract skills"
        assert isinstance(extracted["skills"], list), "Skills should be a list"
        assert "Python" in extracted["skills"], "Should extract Python as a skill"
        assert "JavaScript" in extracted["skills"], "Should extract JavaScript as a skill"
        
        # Check for frameworks if they are extracted
        if "frameworks" in extracted:
            assert isinstance(extracted["frameworks"], list), "Frameworks should be a list"
            assert any(fw for fw in extracted["frameworks"] if "Django" in fw or "React" in fw), "Should extract frameworks"
        
        # Check for experience information
        if "years_experience" in extracted:
            assert extracted["years_experience"] == 5, "Should extract years of experience"
    
    def test_provide_answer_feedback(self, enhanced_qa_service, sample_question, sample_answers):
        """Test feedback generation for answers."""
        # Get feedback for low quality answer
        feedback = enhanced_qa_service._provide_answer_feedback(
            sample_question, 
            sample_answers["low_quality"]["answer_text"],
            quality_score=0.2
        )
        
        # Assertions
        assert isinstance(feedback, list), "Feedback should be a list"
        assert len(feedback) > 0, "Should provide at least one feedback item"
        assert any("specific" in item.lower() for item in feedback), "Should suggest being more specific"
        
        # Get feedback for medium quality answer
        feedback = enhanced_qa_service._provide_answer_feedback(
            sample_question, 
            sample_answers["medium_quality"]["answer_text"],
            quality_score=0.5
        )
        
        # Assertions
        assert len(feedback) > 0, "Should provide feedback for medium quality"
        assert any("detail" in item.lower() for item in feedback), "Should suggest adding more detail"
        
        # Get feedback for high quality answer
        feedback = enhanced_qa_service._provide_answer_feedback(
            sample_question, 
            sample_answers["high_quality"]["answer_text"],
            quality_score=0.9
        )
        
        # High quality might not need feedback
        if len(feedback) > 0:
            assert not any("specific" in item.lower() for item in feedback), "Should not suggest being more specific for high quality"
    
    def test_calculate_profile_completeness(self, qa_integration_service, mock_qa_repository):
        """Test profile completeness calculation based on answer quality."""
        # Mock repository to return questions and answers
        mock_qa_repository.get_questions_for_profile.return_value = [
            {"id": "q1", "category": "professional", "importance": 0.9},
            {"id": "q2", "category": "education", "importance": 0.8},
            {"id": "q3", "category": "skills", "importance": 0.7},
            {"id": "q4", "category": "projects", "importance": 0.6},
            {"id": "q5", "category": "professional", "importance": 0.5}
        ]
        
        mock_qa_repository.get_answers_for_profile.return_value = [
            {"id": "a1", "question_id": "q1", "quality_score": 0.9},  # High quality
            {"id": "a2", "question_id": "q2", "quality_score": 0.7},  # Medium quality
            {"id": "a3", "question_id": "q3", "quality_score": 0.5},  # Medium quality
            # q4 not answered
            {"id": "a5", "question_id": "q5", "quality_score": 0.2}   # Low quality
        ]
        
        # Calculate profile completeness
        profile_id = "test_profile"
        completeness = qa_integration_service.calculate_profile_completeness(profile_id)
        
        # Assertions
        assert "overall_score" in completeness, "Should return overall completeness score"
        assert "category_scores" in completeness, "Should return category scores"
        assert "unanswered_questions" in completeness, "Should return unanswered questions"
        
        # Check overall score (answered 4/5 questions with varying quality)
        # (0.9*0.9 + 0.8*0.7 + 0.7*0.5 + 0*0.6 + 0.5*0.2) / (0.9 + 0.8 + 0.7 + 0.6 + 0.5) = ~0.5
        assert completeness["overall_score"] > 0.4 and completeness["overall_score"] < 0.6, "Overall score should be around 0.5"
        
        # Check category scores
        assert "professional" in completeness["category_scores"], "Should include professional category"
        assert "education" in completeness["category_scores"], "Should include education category"
        assert "skills" in completeness["category_scores"], "Should include skills category"
        assert "projects" in completeness["category_scores"], "Should include projects category"
        
        # Check that professional score is higher than projects (which has no answers)
        assert completeness["category_scores"]["professional"] > completeness["category_scores"]["projects"], "Categories with answers should score higher"
        
        # Check unanswered questions
        assert len(completeness["unanswered_questions"]) == 1, "Should have one unanswered question"
        assert completeness["unanswered_questions"][0] == "q4", "Should identify q4 as unanswered"
    
    def test_identify_profile_gaps(self, qa_integration_service):
        """Test identification of gaps in profile based on answer quality."""
        # Create a mock completeness result
        completeness_result = {
            "overall_score": 0.6,
            "category_scores": {
                "professional": 0.8,
                "education": 0.7,
                "skills": 0.5,
                "projects": 0.3,
                "achievements": 0.2
            },
            "unanswered_questions": ["q7", "q12", "q15"]
        }
        
        # Identify gaps
        gaps = qa_integration_service.identify_profile_gaps(completeness_result)
        
        # Assertions
        assert isinstance(gaps, list), "Should return a list of gaps"
        assert len(gaps) >= 2, "Should identify at least 2 gaps"
        
        # Check if low-scoring categories are identified
        identified_categories = [gap["category"] for gap in gaps if "category" in gap]
        assert "projects" in identified_categories, "Should identify projects as a gap"
        assert "achievements" in identified_categories, "Should identify achievements as a gap"
        assert "professional" not in identified_categories, "Should not identify professional as a gap"
        
        # Check if unanswered questions are identified
        unanswered_gaps = [gap for gap in gaps if gap.get("type") == "unanswered_questions"]
        assert len(unanswered_gaps) > 0, "Should identify unanswered questions as a gap"
    
    @patch("profiler.services.qa.enhanced_qa_service.EnhancedQAService._extract_key_information")
    def test_nlp_information_extraction(self, mock_extract, enhanced_qa_service, sample_question, sample_answers):
        """Test NLP information extraction from answers."""
        # Set up mock return value
        mock_extract.return_value = {
            "skills": ["Python", "JavaScript", "AWS"],
            "years_experience": 5,
            "frameworks": ["Django", "React", "Node.js"]
        }
        
        # Call the evaluate function
        quality_result = enhanced_qa_service.evaluate_answer_quality(
            sample_question, 
            sample_answers["high_quality"]["answer_text"]
        )
        
        # Assertions
        assert mock_extract.called, "Should call extract_key_information"
        assert "extracted_information" in quality_result, "Should include extracted information"
        assert quality_result["extracted_information"]["skills"] == ["Python", "JavaScript", "AWS"], "Should extract skills" 