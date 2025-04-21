import pytest
import json
from unittest.mock import MagicMock, patch
import os
import random

from profiler.services.qa.enhanced_qa_service import EnhancedQAService
from profiler.tests.fixtures.qa_fixtures import mock_qa_repository
from profiler.services.qa.question_generation_service import QuestionGenerationService
from profiler.models.profile import Profile
from profiler.models.question import Question
from profiler.tests.fixtures.profile_fixtures import sample_profile, incomplete_profile

class TestQuestionGeneration:
    """Tests for question generation algorithms."""
    
    @pytest.fixture
    def enhanced_qa_service(self, mock_qa_repository):
        """Create an enhanced QA service with a mock repository."""
        return EnhancedQAService(mock_qa_repository)
    
    @pytest.fixture
    def sample_profile(self):
        """Create a sample profile for testing."""
        return {
            "id": "test123",
            "name": "Test User",
            "professional_info": {
                "title": "Software Engineer",
                "company": "Tech Co"
            },
            "education": [{
                "degree": "Bachelor of Science",
                "institution": "Test University",
                "field": "Computer Science"
            }],
            "skills": ["Python", "JavaScript", "SQL"],
            "projects": []
        }
    
    @pytest.fixture
    def empty_profile(self):
        """Create an empty profile for testing."""
        return {
            "id": "empty123",
            "name": "Empty User"
        }
    
    def test_generate_questions_with_complete_profile(self, enhanced_qa_service, sample_profile):
        """Test question generation with a relatively complete profile."""
        questions = enhanced_qa_service.generate_questions(sample_profile)
        
        # Assertions
        assert len(questions) >= 5, "Should generate at least 5 questions"
        
        # Check if questions are diverse
        categories = set([q.get("category") for q in questions])
        assert len(categories) >= 2, "Should generate questions from at least 2 categories"
        
        # Check if questions have required attributes
        for question in questions:
            assert "id" in question, "Question should have an ID"
            assert "text" in question, "Question should have text"
            assert "category" in question, "Question should have a category"
            assert "importance" in question, "Question should have importance"
    
    def test_generate_questions_with_empty_profile(self, enhanced_qa_service, empty_profile):
        """Test question generation with an empty profile."""
        questions = enhanced_qa_service.generate_questions(empty_profile)
        
        # Assertions
        assert len(questions) >= 5, "Should generate at least 5 questions for empty profiles"
        
        # Check categories 
        categories = [q.get("category") for q in questions]
        assert "professional" in categories, "Should include professional questions for empty profiles"
        assert "education" in categories, "Should include education questions for empty profiles"
        assert "skills" in categories, "Should include skills questions for empty profiles"
    
    def test_analyze_profile_completion(self, enhanced_qa_service, sample_profile, empty_profile):
        """Test profile completion analysis."""
        # For sample profile
        categories = enhanced_qa_service._analyze_profile_completion(sample_profile)
        assert "projects" in categories, "Should identify missing projects"
        assert "professional" not in categories, "Should not suggest professional for complete section"
        
        # For empty profile
        categories = enhanced_qa_service._analyze_profile_completion(empty_profile)
        assert len(categories) >= 3, "Should identify multiple missing sections"
        assert "professional" in categories, "Should identify missing professional info"
        assert "education" in categories, "Should identify missing education"
        assert "skills" in categories, "Should identify missing skills"
    
    def test_customize_question(self, enhanced_qa_service, sample_profile):
        """Test question customization based on profile data."""
        # Test with name placeholder
        question = enhanced_qa_service._customize_question(
            "Hello {name}, what is your current job title?", 
            sample_profile
        )
        assert "Hello Test User" in question, "Should replace name placeholder"
        
        # Test with job placeholder
        question = enhanced_qa_service._customize_question(
            "How long have you been a {current_job}?", 
            sample_profile
        )
        assert "How long have you been a Software Engineer" in question, "Should replace job placeholder"
        
        # Test with unknown placeholders
        question = enhanced_qa_service._customize_question(
            "Do you enjoy working at {company}?", 
            sample_profile
        )
        assert "Do you enjoy working at Tech Co" in question, "Should replace company placeholder"
        
        # Test with placeholder that doesn't exist in the profile
        question = enhanced_qa_service._customize_question(
            "How do you like {unknown_field}?", 
            sample_profile
        )
        assert "How do you like " in question, "Should remove unknown placeholders"
        assert "{unknown_field}" not in question, "Should not contain placeholder markers"
    
    def test_load_question_bank(self, enhanced_qa_service, tmp_path):
        """Test loading questions from a question bank file."""
        # Create a temporary question bank file
        test_bank = {
            "test_category": [
                {"text": "Test question 1", "importance": 0.7},
                {"text": "Test question 2", "importance": 0.8}
            ]
        }
        
        bank_path = tmp_path / "test_question_bank.json"
        with open(bank_path, "w") as f:
            json.dump(test_bank, f)
        
        # Load the question bank
        bank = enhanced_qa_service._load_question_bank(str(bank_path))
        
        # Assertions
        assert "test_category" in bank, "Should load custom categories"
        assert len(bank["test_category"]) == 2, "Should load correct number of questions"
        assert bank["test_category"][0]["text"] == "Test question 1", "Should load question text"
        
        # Test with invalid file
        invalid_path = tmp_path / "nonexistent.json"
        bank = enhanced_qa_service._load_question_bank(str(invalid_path))
        
        # Should fall back to default bank
        assert "professional" in bank, "Should load default bank if file not found"
        assert "education" in bank, "Should load default bank if file not found"
        assert "skills" in bank, "Should load default bank if file not found"
    
    def test_generate_follow_up_questions(self, enhanced_qa_service):
        """Test generating follow-up questions based on answers."""
        # Create a test question and answer
        question = {
            "id": "q123",
            "text": "What is your current job title?",
            "category": "professional",
            "profile_id": "prof123"
        }
        
        answer = {
            "answer_text": "I am a Senior Software Engineer with 7 years of experience",
            "extracted_information": {
                "job_titles": ["Senior Software Engineer"],
                "years_of_experience": 7
            },
            "quality_score": 0.8
        }
        
        # Generate follow-up questions
        follow_ups = enhanced_qa_service._generate_follow_up_questions(question, answer)
        
        # Assertions
        assert len(follow_ups) >= 1, "Should generate at least one follow-up question"
        
        # Check if follow-ups reference parent question
        for follow_up in follow_ups:
            assert follow_up.get("parent_question_id") == "q123", "Should reference parent question"
            assert follow_up.get("profile_id") == "prof123", "Should maintain profile ID"
            assert follow_up.get("category") == "professional", "Should match parent category"
            assert "id" in follow_up, "Should have an ID"
            assert "text" in follow_up, "Should have text"
            assert "importance" in follow_up, "Should have importance"
            
    def test_follow_up_questions_for_low_quality_answers(self, enhanced_qa_service):
        """Test follow-up questions generated for low quality answers."""
        # Create a test question and low quality answer
        question = {
            "id": "q123",
            "text": "What are your main skills?",
            "category": "skills",
            "profile_id": "prof123"
        }
        
        low_quality_answer = {
            "answer_text": "coding",  # Very short, low quality
            "extracted_information": {},
            "quality_score": 0.2
        }
        
        # Generate follow-up questions
        follow_ups = enhanced_qa_service._generate_follow_up_questions(question, low_quality_answer)
        
        # Assertions
        assert len(follow_ups) >= 1, "Should generate at least one follow-up for low quality answers"
        
        # Check if at least one follow-up asks for elaboration
        elaboration_questions = [
            q for q in follow_ups 
            if "elaborate" in q.get("text", "").lower() or 
               "more detail" in q.get("text", "").lower() or
               "tell me more" in q.get("text", "").lower()
        ]
        
        assert len(elaboration_questions) >= 1, "Should ask for elaboration on low quality answers"

    @pytest.fixture
    def question_service(self):
        """Create a question generation service with mocked dependencies."""
        # Mock any external dependencies
        with patch('profiler.services.qa.question_generation_service.NLPProcessor') as mock_nlp:
            # Configure the mock as needed
            mock_nlp_instance = MagicMock()
            mock_nlp_instance.analyze_text.return_value = {
                "entities": ["skill", "experience", "education"],
                "keywords": ["python", "javascript", "react"]
            }
            mock_nlp.return_value = mock_nlp_instance
            
            # Create and return the service
            service = QuestionGenerationService()
            return service
    
    def test_question_generation_from_profile_gaps(self, question_service, incomplete_profile):
        """Test generating questions based on profile gaps."""
        # Generate questions based on profile gaps
        questions = question_service.generate_gap_questions(incomplete_profile)
        
        # Check that questions were generated
        assert len(questions) > 0, "Should generate at least one question for incomplete profile"
        
        # Check that questions target missing fields
        missing_fields = incomplete_profile.get_incomplete_fields()
        question_targets = [q.target_field for q in questions]
        
        assert set(question_targets).issubset(set(missing_fields)), \
            "Questions should target missing fields in the profile"
        
        # Check question structure
        for question in questions:
            assert question.text, "Question should have text"
            assert question.type, "Question should have a type"
            assert question.target_field, "Question should have a target field"
    
    def test_contextual_question_generation(self, question_service, sample_profile):
        """Test generating contextual follow-up questions based on existing profile data."""
        # Generate contextual questions
        questions = question_service.generate_contextual_questions(sample_profile)
        
        # Check that questions were generated
        assert len(questions) > 0, "Should generate at least one contextual question"
        
        # Check that questions reference existing profile data
        profile_data = sample_profile.to_dict()
        
        # At least some questions should reference existing profile data
        reference_found = False
        for question in questions:
            for field, value in profile_data.items():
                if isinstance(value, str) and value and len(value) > 3:
                    if value.lower() in question.text.lower():
                        reference_found = True
                        break
            if reference_found:
                break
        
        assert reference_found, "At least one question should reference existing profile data"
    
    def test_skill_verification_questions(self, question_service, sample_profile):
        """Test generating questions that verify claimed skills."""
        # Assuming sample_profile has skills
        if not hasattr(sample_profile, 'skills') or not sample_profile.skills:
            pytest.skip("Profile needs skills for this test")
        
        # Generate skill verification questions
        questions = question_service.generate_skill_verification_questions(sample_profile)
        
        # Check that questions were generated
        assert len(questions) > 0, "Should generate at least one skill verification question"
        
        # Check that questions target skills in the profile
        skills = [skill.name.lower() for skill in sample_profile.skills]
        
        skill_mentions = 0
        for question in questions:
            for skill in skills:
                if skill.lower() in question.text.lower():
                    skill_mentions += 1
                    break
        
        assert skill_mentions > 0, "Questions should mention skills from the profile"
        
        # Check question properties
        for question in questions:
            assert question.text, "Question should have text"
            assert question.type == "skill_verification", "Question should be of type skill_verification"
            assert hasattr(question, 'expected_evidence'), "Skill verification questions should have expected evidence"
    
    def test_experience_deep_dive_questions(self, question_service, sample_profile):
        """Test generating questions that explore experiences in depth."""
        # Assuming sample_profile has experience entries
        if not hasattr(sample_profile, 'experiences') or not sample_profile.experiences:
            pytest.skip("Profile needs experiences for this test")
        
        # Generate experience deep dive questions
        questions = question_service.generate_experience_deep_dive_questions(sample_profile)
        
        # Check that questions were generated
        assert len(questions) > 0, "Should generate at least one experience deep dive question"
        
        # Check question targets
        for question in questions:
            assert question.text, "Question should have text"
            assert question.type == "experience_deep_dive", "Question should be of type experience_deep_dive"
            assert hasattr(question, 'experience_id'), "Experience deep dive questions should reference an experience ID"
            
            # Verify that the referenced experience exists
            experience_exists = False
            for experience in sample_profile.experiences:
                if experience.id == question.experience_id:
                    experience_exists = True
                    break
            
            assert experience_exists, f"Referenced experience {question.experience_id} should exist in the profile"
    
    def test_consistency_check_questions(self, question_service, sample_profile):
        """Test generating questions that check for consistency across the profile."""
        # Generate consistency check questions
        questions = question_service.generate_consistency_check_questions(sample_profile)
        
        # Check that questions were generated
        assert len(questions) > 0, "Should generate at least one consistency check question"
        
        # Check question properties
        for question in questions:
            assert question.text, "Question should have text"
            assert question.type == "consistency_check", "Question should be of type consistency_check"
            assert hasattr(question, 'related_fields'), "Consistency check questions should have related fields"
            assert len(question.related_fields) >= 2, "Consistency check questions should relate at least two fields"
    
    def test_branching_logic(self, question_service, sample_profile):
        """Test that questions can be generated with branching logic."""
        # Generate a question with branching logic
        question = question_service.generate_question_with_branching(sample_profile)
        
        # Check question properties
        assert question.text, "Question should have text"
        assert hasattr(question, 'branches'), "Question should have branches"
        assert len(question.branches) > 1, "Question should have multiple branches"
        
        # Check branch structure
        for branch in question.branches:
            assert 'condition' in branch, "Branch should have a condition"
            assert 'next_questions' in branch, "Branch should have next questions"
            assert len(branch['next_questions']) > 0, "Branch should have at least one next question"
    
    def test_question_prioritization(self, question_service, incomplete_profile):
        """Test that questions are properly prioritized based on profile completeness."""
        # Generate a set of questions
        all_questions = question_service.generate_all_questions(incomplete_profile)
        
        # Prioritize the questions
        prioritized_questions = question_service.prioritize_questions(all_questions, incomplete_profile)
        
        # Check that questions are prioritized
        assert len(prioritized_questions) == len(all_questions), "All questions should be included in prioritization"
        
        # Check that the most critical gaps are addressed first
        critical_fields = incomplete_profile.get_critical_incomplete_fields()
        if critical_fields:
            # At least the first question should target a critical field
            assert prioritized_questions[0].target_field in critical_fields, \
                "First question should target a critical field"
    
    def test_question_diversity(self, question_service, sample_profile):
        """Test that generated questions have diversity in types and topics."""
        # Generate a diverse set of questions
        questions = question_service.generate_diverse_question_set(sample_profile, count=10)
        
        # Check count
        assert len(questions) == 10, "Should generate requested number of questions"
        
        # Check diversity in question types
        question_types = [q.type for q in questions]
        unique_types = set(question_types)
        
        assert len(unique_types) >= 3, "Should have at least 3 different question types"
        
        # Check diversity in target fields
        target_fields = [q.target_field for q in questions if hasattr(q, 'target_field')]
        unique_fields = set(target_fields)
        
        assert len(unique_fields) >= 3, "Should target at least 3 different fields"
    
    def test_question_personalization(self, question_service, sample_profile):
        """Test that questions are personalized based on profile data."""
        # Generate personalized questions
        questions = question_service.generate_personalized_questions(sample_profile)
        
        # Check that questions were generated
        assert len(questions) > 0, "Should generate at least one personalized question"
        
        # Check for personalization markers in questions
        profile_name = sample_profile.name if hasattr(sample_profile, 'name') else None
        
        if profile_name:
            name_mentions = sum(1 for q in questions if profile_name in q.text)
            assert name_mentions > 0, "Some questions should mention the profile name"
        
        # Check for other personalization elements
        personalization_count = 0
        for question in questions:
            if hasattr(question, 'personalization_factors') and question.personalization_factors:
                personalization_count += 1
        
        assert personalization_count > 0, "Some questions should have personalization factors"
    
    def test_adaptive_question_generation(self, question_service, sample_profile):
        """Test that questions adapt based on previous answers."""
        # Mock previous questions and answers
        previous_qa = [
            {
                "question": Question(id="q1", text="Tell me about your experience with Python?", type="skill_deep_dive"),
                "answer": "I have 5 years of experience with Python, mainly in data science and backend development."
            },
            {
                "question": Question(id="q2", text="Have you worked on any machine learning projects?", type="experience_verification"),
                "answer": "Yes, I built a recommendation system using collaborative filtering."
            }
        ]
        
        # Generate adaptive questions
        questions = question_service.generate_adaptive_questions(sample_profile, previous_qa)
        
        # Check that questions were generated
        assert len(questions) > 0, "Should generate at least one adaptive question"
        
        # Check for references to previous answers
        references_found = 0
        for question in questions:
            # Look for keywords from previous answers in the new questions
            if "python" in question.text.lower() or "data science" in question.text.lower() or \
               "machine learning" in question.text.lower() or "recommendation" in question.text.lower():
                references_found += 1
        
        assert references_found > 0, "Some questions should reference information from previous answers"
        
        # Check for adaptive question properties
        for question in questions:
            assert question.text, "Question should have text"
            assert hasattr(question, 'adapts_from'), "Adaptive questions should reference what they adapt from"
    
    def test_algorithm_performance(self, question_service, benchmark):
        """Test the performance of the question generation algorithm."""
        # Create a large profile for testing
        large_profile = MagicMock()
        large_profile.skills = [MagicMock() for _ in range(50)]
        large_profile.experiences = [MagicMock() for _ in range(20)]
        large_profile.educations = [MagicMock() for _ in range(10)]
        
        # Benchmark the performance
        result = benchmark(question_service.generate_all_questions, large_profile)
        
        # Check that the generation completes within a reasonable time
        # This is a subjective threshold and may need to be adjusted
        assert result, "Question generation should complete successfully"
    
    def test_question_quality(self, question_service, sample_profile):
        """Test the quality of generated questions."""
        # Generate questions
        questions = question_service.generate_all_questions(sample_profile)
        
        # Check question quality metrics
        for question in questions:
            # Check question length (arbitrary thresholds for demonstration)
            assert 10 <= len(question.text) <= 200, "Question text should be reasonable length"
            
            # Check that questions end with question marks
            assert question.text.strip().endswith('?'), "Questions should end with question marks"
            
            # Check that questions are not duplicated
            question_texts = [q.text for q in questions]
            assert question_texts.count(question.text) == 1, "Questions should not be duplicated" 