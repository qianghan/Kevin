"""
Tests for the services layer.

This module tests the core services:
- QA Service
- Document Service
- Recommendation Service
"""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock

from app.backend.services.qa_service import QAService
from app.backend.services.document_service import DocumentService
from app.backend.services.recommender_service import RecommendationService


# Tests for QAService
class TestQAService:
    @pytest.mark.asyncio
    async def test_process_input(self, mock_qa_service):
        """Test processing user input and generating responses."""
        # Override internal methods to isolate test
        with patch.object(
            mock_qa_service, '_extract_information', return_value={"gpa": 3.8}
        ), patch.object(
            mock_qa_service, '_generate_follow_up', return_value=["What subjects do you enjoy?"]
        ):
            result = await mock_qa_service.process_input(
                "I have a 3.8 GPA in high school.",
                context={"previous_data": {"name": "John"}}
            )
            
            assert "answer" in result
            assert "extracted_info" in result
            assert "follow_up_questions" in result
            assert "confidence" in result
            assert result["extracted_info"]["gpa"] == 3.8
            assert "What subjects" in result["follow_up_questions"][0]
    
    @pytest.mark.asyncio
    async def test_extract_information(self, mock_qa_service):
        """Test extracting structured information from text."""
        # Mock the DeepSeek client response
        with patch.object(mock_qa_service, '_client') as mock_client:
            mock_client.generate.return_value = {
                "text": json.dumps({
                    "academic": {"gpa": 3.9},
                    "extracurricular": {"activities": ["Debate"]}
                }),
                "confidence": 0.9
            }
            
            extracted = await mock_qa_service._extract_information(
                "I have a 3.9 GPA and participate in Debate club."
            )
            
            assert "academic" in extracted
            assert extracted["academic"]["gpa"] == 3.9
            assert "Debate" in extracted["extracurricular"]["activities"]
    
    @pytest.mark.asyncio
    async def test_generate_follow_up(self, mock_qa_service):
        """Test generating follow-up questions based on context."""
        # Mock the DeepSeek client response
        with patch.object(mock_qa_service, '_client') as mock_client:
            mock_client.generate.return_value = {
                "text": "1. What subjects are you strongest in?\n2. Have you taken any AP courses?",
                "confidence": 0.85
            }
            
            questions = await mock_qa_service._generate_follow_up(
                "I'm a high school student with good grades.",
                context={"academic": {"level": "high school"}}
            )
            
            assert len(questions) >= 2
            assert any("subjects" in q.lower() for q in questions)
            assert any("AP" in q for q in questions)
    
    def test_reset_conversation(self, mock_qa_service):
        """Test resetting the conversation state."""
        # Setup memory with some data
        mock_qa_service.memory.chat_memory.add_user_message("Hello")
        mock_qa_service.memory.chat_memory.add_ai_message("Hi there")
        
        # Reset
        mock_qa_service.reset_conversation()
        
        # Verify memory is cleared
        assert len(mock_qa_service.memory.chat_memory.messages) == 0
    
    @pytest.mark.asyncio
    async def test_get_conversation_summary(self, mock_qa_service):
        """Test summarizing conversation history."""
        # Add some conversation history
        mock_qa_service.memory.chat_memory.add_user_message("I have a 3.9 GPA")
        mock_qa_service.memory.chat_memory.add_ai_message("That's excellent! What subjects do you excel in?")
        mock_qa_service.memory.chat_memory.add_user_message("Math and Physics")
        
        # Mock the client response
        with patch.object(mock_qa_service, '_client') as mock_client:
            mock_client.generate.return_value = {
                "text": json.dumps({
                    "academic": {"gpa": 3.9, "strong_subjects": ["Math", "Physics"]},
                    "summary": "Student has strong academic performance."
                }),
                "confidence": 0.9
            }
            
            summary = await mock_qa_service.get_conversation_summary()
            
            assert "academic" in summary
            assert summary["academic"]["gpa"] == 3.9
            assert "summary" in summary


# Tests for DocumentService
class TestDocumentService:
    @pytest.mark.asyncio
    async def test_analyze_transcript(self, mock_document_service):
        """Test analyzing an academic transcript document."""
        transcript = """
        Student: Jane Doe
        GPA: 3.95
        Courses:
        - AP Calculus BC: A
        - AP Physics: A
        - English Literature: A-
        """
        
        # Mock methods to control test scope
        with patch.object(
            mock_document_service, '_extract_basic_info', return_value={"document_type": "transcript"}
        ), patch.object(
            mock_document_service, '_perform_deep_analysis', return_value={
                "student_name": "Jane Doe",
                "gpa": 3.95,
                "courses": [
                    {"name": "AP Calculus BC", "grade": "A"},
                    {"name": "AP Physics", "grade": "A"},
                    {"name": "English Literature", "grade": "A-"}
                ]
            }
        ):
            result = await mock_document_service.analyze("transcript", transcript)
            
            assert result.content_type == "transcript"
            assert "extracted_info" in result.dict()
            assert result.extracted_info["gpa"] == 3.95
            assert len(result.extracted_info["courses"]) == 3
            assert 0.7 <= result.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_essay(self, mock_document_service):
        """Test analyzing an essay document."""
        essay = """
        My College Application Essay
        
        Throughout high school, I've developed a passion for scientific research...
        """
        
        # Mock methods to control test scope
        with patch.object(
            mock_document_service, '_extract_basic_info', return_value={"document_type": "essay"}
        ), patch.object(
            mock_document_service, '_perform_deep_analysis', return_value={
                "title": "My College Application Essay",
                "themes": ["scientific research", "passion", "academic journey"],
                "tone": "passionate",
                "writing_quality": 0.85
            }
        ):
            result = await mock_document_service.analyze("essay", essay)
            
            assert result.content_type == "essay"
            assert "themes" in result.extracted_info
            assert "tone" in result.extracted_info
            assert "writing_quality" in result.extracted_info
            assert 0.7 <= result.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_with_invalid_type(self, mock_document_service):
        """Test handling invalid document types."""
        with pytest.raises(ValueError) as excinfo:
            await mock_document_service.analyze("invalid_type", "Some content")
        
        assert "Invalid document type" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_extract_basic_info(self, mock_document_service):
        """Test extracting basic document information."""
        # Mock the DeepSeek client
        with patch.object(mock_document_service, '_client') as mock_client:
            mock_client.analyze.return_value = {
                "analysis": {
                    "document_type": "transcript",
                    "length": 500,
                    "format": "structured"
                },
                "confidence": 0.9
            }
            
            info = await mock_document_service._extract_basic_info("transcript", "Document content")
            
            assert info["document_type"] == "transcript"
            assert info["length"] == 500
            assert info["format"] == "structured"
    
    @pytest.mark.asyncio
    async def test_perform_deep_analysis(self, mock_document_service):
        """Test deep analysis of document content."""
        # Mock the DeepSeek client
        with patch.object(mock_document_service, '_client') as mock_client:
            mock_client.analyze.return_value = {
                "analysis": {
                    "student_name": "John Smith",
                    "gpa": 3.8,
                    "courses": [{"name": "Math", "grade": "A"}]
                },
                "confidence": 0.85
            }
            
            analysis = await mock_document_service._perform_deep_analysis(
                "transcript", 
                "John Smith, GPA: 3.8, Math: A"
            )
            
            assert analysis["student_name"] == "John Smith"
            assert analysis["gpa"] == 3.8
            assert len(analysis["courses"]) == 1


# Tests for RecommendationService
class TestRecommendationService:
    @pytest.mark.asyncio
    async def test_get_recommendations(self, mock_recommendation_service):
        """Test getting recommendations for a user profile."""
        profile = {
            "user_id": "test123",
            "academic": {
                "gpa": 3.7,
                "courses": ["Biology", "Chemistry"]
            },
            "extracurricular": {
                "activities": ["Science Club"]
            }
        }
        
        # Mock the generate method
        with patch.object(
            mock_recommendation_service, 'generate_recommendations', 
            return_value={
                "academic": ["Consider taking AP Biology", "Add more math courses"],
                "extracurricular": ["Join a research lab"],
                "overall_quality": 0.75
            }
        ):
            recommendations = await mock_recommendation_service.get_recommendations(profile)
            
            assert "recommendations" in recommendations
            assert "academic" in recommendations["recommendations"]
            assert "extracurricular" in recommendations["recommendations"]
            assert "overall_quality" in recommendations
            assert len(recommendations["recommendations"]["academic"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_section_recommendations(self, mock_recommendation_service):
        """Test getting recommendations for a specific profile section."""
        section_data = {
            "gpa": 3.5,
            "courses": ["English", "History"],
            "awards": ["Essay Competition Winner"]
        }
        
        # Mock the DeepSeek client
        with patch.object(mock_recommendation_service, '_client') as mock_client:
            mock_client.generate.return_value = {
                "text": json.dumps({
                    "recommendations": [
                        "Take more advanced English courses",
                        "Consider participating in debate competitions"
                    ],
                    "quality_score": 0.8
                }),
                "confidence": 0.85
            }
            
            result = await mock_recommendation_service.get_section_recommendations(
                "academic", section_data
            )
            
            assert "recommendations" in result
            assert "quality_score" in result
            assert len(result["recommendations"]) == 2
            assert 0 <= result["quality_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_get_profile_summary(self, mock_recommendation_service):
        """Test generating a profile summary."""
        profile = {
            "sections": {
                "academic": {"gpa": 3.9, "courses": ["Math", "Science"]},
                "extracurricular": {"activities": ["Chess Club", "Volunteering"]},
                "personal": {"strengths": ["Problem-solving", "Leadership"]}
            }
        }
        
        # Mock the DeepSeek client
        with patch.object(mock_recommendation_service, '_client') as mock_client:
            mock_client.generate.return_value = {
                "text": json.dumps({
                    "strengths": ["Strong academic record", "Well-rounded activities"],
                    "areas_for_improvement": ["Consider adding more STEM extracurriculars"],
                    "unique_selling_points": ["Combination of academic excellence and leadership"],
                    "overall_quality": 0.85
                }),
                "confidence": 0.9
            }
            
            summary = await mock_recommendation_service.get_profile_summary(profile)
            
            assert "strengths" in summary
            assert "areas_for_improvement" in summary
            assert "unique_selling_points" in summary
            assert "overall_quality" in summary
            assert len(summary["strengths"]) >= 1
            assert 0 <= summary["overall_quality"] <= 1
    
    @pytest.mark.asyncio
    async def test_generate_recommendations(self, mock_recommendation_service):
        """Test the internal recommendation generation process."""
        # Mock the DeepSeek client
        with patch.object(mock_recommendation_service, '_client') as mock_client:
            mock_client.generate.return_value = {
                "text": json.dumps({
                    "academic": ["Recommendation 1", "Recommendation 2"],
                    "extracurricular": ["Recommendation 3"],
                    "overall_quality": 0.7
                }),
                "confidence": 0.8
            }
            
            recommendations = await mock_recommendation_service.generate_recommendations(
                {
                    "academic": {"gpa": 3.5},
                    "extracurricular": {"activities": ["Activity 1"]}
                }
            )
            
            assert "academic" in recommendations
            assert "extracurricular" in recommendations
            assert "overall_quality" in recommendations
            assert len(recommendations["academic"]) == 2
            assert len(recommendations["extracurricular"]) == 1 