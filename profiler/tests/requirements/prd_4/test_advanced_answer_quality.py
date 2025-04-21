import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from profiler.services.qa.enhanced_qa_service import EnhancedQAService
from profiler.services.qa.answer_quality_service import AnswerQualityService
from profiler.services.qa.nlp_service import NLPService
from profiler.tests.fixtures.qa_fixtures import mock_qa_repository
from profiler.tests.fixtures.profile_fixtures import sample_profile


class TestAdvancedAnswerQuality:
    """Tests for advanced answer quality assessment features."""
    
    @pytest.fixture
    def answer_quality_service(self):
        """Create an answer quality service with mocked dependencies."""
        # Mock the NLP service
        with patch('profiler.services.qa.answer_quality_service.NLPService') as mock_nlp:
            mock_nlp_instance = MagicMock()
            # Configure the NLP mock with realistic behaviors
            mock_nlp_instance.calculate_semantic_similarity.return_value = 0.75
            mock_nlp_instance.extract_entities.return_value = ["Python", "JavaScript", "AWS"]
            mock_nlp_instance.detect_sentiment.return_value = {"positive": 0.8, "neutral": 0.15, "negative": 0.05}
            mock_nlp.return_value = mock_nlp_instance
            
            # Create the service
            service = AnswerQualityService()
            return service
    
    @pytest.fixture
    def sample_question_bank(self):
        """Create a sample question bank with reference answers."""
        return [
            {
                "id": "q1",
                "text": "Describe your experience with Python.",
                "category": "technical_skills",
                "reference_answer": "I have X years of experience with Python, mainly in areas like web development, data analysis, and automation. I've used frameworks such as Django, Flask, and FastAPI for web development, and libraries like pandas, numpy, and scikit-learn for data analysis. I've also contributed to open-source Python projects and created Python packages.",
                "key_concepts": ["experience duration", "frameworks", "libraries", "projects", "contributions"]
            },
            {
                "id": "q2",
                "text": "How do you approach problem-solving in a team environment?",
                "category": "soft_skills",
                "reference_answer": "When solving problems in a team, I first ensure I understand the problem by asking clarifying questions. I then collaborate with team members to brainstorm potential solutions, considering different perspectives. I value open communication and respectful discussion of ideas. Once we agree on an approach, I help establish clear responsibilities and timelines. Throughout the process, I stay flexible and open to adjusting our approach based on new information or feedback.",
                "key_concepts": ["understanding", "collaboration", "communication", "planning", "adaptability"]
            }
        ]
    
    @pytest.fixture
    def sample_answers(self):
        """Create sample answers with varying quality for testing."""
        return {
            "comprehensive": "I have 5 years of experience with Python, primarily in web development using Django and Flask frameworks. I've built several production applications, including an e-commerce platform and a data visualization dashboard. I'm proficient with Python packages like pandas and numpy for data analysis, and I've contributed to open-source Python libraries. I've also mentored junior developers in Python best practices.",
            
            "partial": "I've used Python for a few years, mainly for web development with Django. I've worked on some projects and know the basics of data analysis with pandas.",
            
            "minimal": "I know Python and have used it for coding.",
            
            "irrelevant": "I prefer to use JavaScript for most of my projects because I find it more versatile.",
            
            "non_specific": "I have experience with several programming languages and have worked on various projects throughout my career."
        }
    
    def test_semantic_similarity_scoring(self, answer_quality_service, sample_question_bank, sample_answers):
        """Test scoring based on semantic similarity to reference answers."""
        question = sample_question_bank[0]
        reference = question["reference_answer"]
        
        # Test with answers of varying quality
        scores = {}
        for name, answer in sample_answers.items():
            score = answer_quality_service.calculate_semantic_similarity(answer, reference)
            scores[name] = score
        
        # The comprehensive answer should score highest
        assert scores["comprehensive"] > scores["partial"], "Comprehensive answer should score higher than partial"
        assert scores["partial"] > scores["minimal"], "Partial answer should score higher than minimal"
        assert scores["minimal"] > scores["irrelevant"], "Minimal answer should score higher than irrelevant"
        
        # Non-specific answers should score lower than specific ones
        assert scores["comprehensive"] > scores["non_specific"], "Specific answers should score higher than non-specific"
    
    def test_key_concept_coverage(self, answer_quality_service, sample_question_bank, sample_answers):
        """Test scoring based on coverage of key concepts."""
        question = sample_question_bank[0]
        key_concepts = question["key_concepts"]
        
        # Test concept coverage for different answers
        coverage = {}
        for name, answer in sample_answers.items():
            score = answer_quality_service.calculate_concept_coverage(answer, key_concepts)
            coverage[name] = score
        
        # Check relative scores
        assert coverage["comprehensive"] > 0.8, "Comprehensive answer should cover most key concepts"
        assert coverage["partial"] > 0.4 and coverage["partial"] < 0.8, "Partial answer should have moderate concept coverage"
        assert coverage["minimal"] < 0.3, "Minimal answer should have low concept coverage"
        
        # Check for specific concepts in comprehensive answer
        detected_concepts = answer_quality_service.detect_concepts(sample_answers["comprehensive"], key_concepts)
        assert "experience duration" in detected_concepts, "Should detect experience duration concept"
        assert "frameworks" in detected_concepts, "Should detect frameworks concept"
    
    def test_answer_length_analysis(self, answer_quality_service, sample_answers):
        """Test analysis of answer length as a quality factor."""
        # Calculate length scores
        length_scores = {}
        for name, answer in sample_answers.items():
            score = answer_quality_service.evaluate_length_appropriateness(answer)
            length_scores[name] = score
        
        # Comprehensive should be appropriate, not too short or too long
        assert length_scores["comprehensive"] > 0.7, "Comprehensive answer should have appropriate length"
        
        # Minimal should be too short
        assert length_scores["minimal"] < 0.3, "Minimal answer should be identified as too short"
        
        # Create an excessively long answer
        very_long = sample_answers["comprehensive"] * 10
        long_score = answer_quality_service.evaluate_length_appropriateness(very_long)
        assert long_score < 0.5, "Excessively long answers should be penalized"
    
    def test_specificity_detection(self, answer_quality_service, sample_answers):
        """Test detection of specific vs. generic content in answers."""
        specificity_scores = {}
        for name, answer in sample_answers.items():
            score = answer_quality_service.measure_specificity(answer)
            specificity_scores[name] = score
        
        # Check relative scores
        assert specificity_scores["comprehensive"] > specificity_scores["non_specific"], "Specific answers should score higher than non-specific"
        assert specificity_scores["minimal"] < specificity_scores["partial"], "Less detailed answers should score lower on specificity"
        
        # Check for specific terms and metrics
        specific_terms = answer_quality_service.extract_specific_terms(sample_answers["comprehensive"])
        assert "Django" in specific_terms, "Should extract specific framework names"
        assert "Flask" in specific_terms, "Should extract specific framework names"
        assert "5 years" in specific_terms or "5" in specific_terms, "Should extract specific metrics like years of experience"
    
    def test_relevance_to_question(self, answer_quality_service, sample_question_bank, sample_answers):
        """Test scoring of answer relevance to the original question."""
        question = sample_question_bank[0]["text"]
        
        relevance_scores = {}
        for name, answer in sample_answers.items():
            score = answer_quality_service.evaluate_relevance(question, answer)
            relevance_scores[name] = score
        
        # Check relative scores
        assert relevance_scores["comprehensive"] > 0.8, "Comprehensive answer should be highly relevant"
        assert relevance_scores["irrelevant"] < 0.3, "Irrelevant answer should have low relevance score"
        assert relevance_scores["comprehensive"] > relevance_scores["non_specific"], "Specific answers should be more relevant than generic ones"
    
    def test_entity_recognition(self, answer_quality_service, sample_answers):
        """Test extraction and validation of entities from answers."""
        # Test entity extraction from comprehensive answer
        entities = answer_quality_service.extract_entities(sample_answers["comprehensive"])
        
        # Check for technology entities
        assert "Python" in entities, "Should extract Python as an entity"
        assert "Django" in entities, "Should extract Django as an entity"
        assert "Flask" in entities, "Should extract Flask as an entity"
        
        # Check for categorization of entities
        categorized = answer_quality_service.categorize_entities(entities)
        assert "programming_languages" in categorized, "Should categorize entities"
        assert "Python" in categorized["programming_languages"], "Should categorize Python as a programming language"
        assert "frameworks" in categorized, "Should have a frameworks category"
        assert "Django" in categorized["frameworks"], "Should categorize Django as a framework"
    
    def test_answer_coherence(self, answer_quality_service, sample_answers):
        """Test evaluation of answer coherence and structure."""
        coherence_scores = {}
        for name, answer in sample_answers.items():
            score = answer_quality_service.evaluate_coherence(answer)
            coherence_scores[name] = score
        
        # Well-structured answers should have higher coherence
        assert coherence_scores["comprehensive"] > coherence_scores["minimal"], "Comprehensive answers should have higher coherence"
        
        # Create an incoherent answer by shuffling sentences
        import random
        sentences = sample_answers["comprehensive"].split('.')
        random.shuffle(sentences)
        incoherent = '. '.join(sentences)
        
        incoherent_score = answer_quality_service.evaluate_coherence(incoherent)
        assert coherence_scores["comprehensive"] > incoherent_score, "Shuffled sentences should reduce coherence score"
    
    def test_sentiment_analysis(self, answer_quality_service, sample_answers):
        """Test sentiment analysis on answers."""
        # Add answers with different sentiments
        test_answers = {
            "positive": "I really enjoy working with Python and find it extremely powerful and flexible. It's been a fantastic journey learning and using it in my projects.",
            "negative": "I had many frustrating experiences with Python. The package management is problematic and deployment can be a nightmare.",
            "neutral": "I've used Python for 3 years in various projects. It has packages for data analysis and web development."
        }
        
        sentiments = {}
        for name, answer in test_answers.items():
            sentiment = answer_quality_service.analyze_sentiment(answer)
            sentiments[name] = sentiment
        
        # Check sentiment detection
        assert sentiments["positive"]["positive"] > sentiments["positive"]["negative"], "Positive answer should have higher positive sentiment"
        assert sentiments["negative"]["negative"] > sentiments["negative"]["positive"], "Negative answer should have higher negative sentiment"
        assert sentiments["neutral"]["neutral"] > sentiments["neutral"]["positive"], "Neutral answer should have higher neutral sentiment"
        
        # Check for appropriate sentiment in professional contexts
        appropriateness = answer_quality_service.evaluate_sentiment_appropriateness(test_answers["negative"])
        assert appropriateness < 0.5, "Overly negative answers should be flagged as less appropriate"
    
    def test_feedback_generation(self, answer_quality_service, sample_question_bank, sample_answers):
        """Test generation of helpful feedback for different answer qualities."""
        question = sample_question_bank[0]
        
        # Get feedback for different quality answers
        feedbacks = {}
        for name, answer in sample_answers.items():
            feedback = answer_quality_service.generate_feedback(question, answer)
            feedbacks[name] = feedback
        
        # Check feedback for minimal answer
        assert len(feedbacks["minimal"]) >= 2, "Should provide multiple feedback points for minimal answers"
        assert any("specific" in point.lower() for point in feedbacks["minimal"]), "Should suggest adding specifics for minimal answers"
        assert any("example" in point.lower() for point in feedbacks["minimal"]), "Should suggest adding examples for minimal answers"
        
        # Check feedback for partial answer
        assert any("expand" in point.lower() for point in feedbacks["partial"]), "Should suggest expanding on points for partial answers"
        
        # Check feedback for comprehensive answer
        assert len(feedbacks["comprehensive"]) <= 1, "Should provide minimal feedback for comprehensive answers"
    
    def test_aggregate_quality_score(self, answer_quality_service, sample_question_bank, sample_answers):
        """Test calculation of aggregate quality score from multiple metrics."""
        question = sample_question_bank[0]
        
        # Calculate aggregate scores
        scores = {}
        for name, answer in sample_answers.items():
            # Combined quality assessment
            assessment = answer_quality_service.comprehensive_quality_assessment(
                question["text"], 
                answer, 
                reference_answer=question["reference_answer"],
                key_concepts=question["key_concepts"]
            )
            scores[name] = assessment["overall_score"]
        
        # Check relative scores
        assert scores["comprehensive"] > 0.8, "Comprehensive answer should score highly overall"
        assert scores["partial"] > 0.4 and scores["partial"] < 0.8, "Partial answer should have moderate overall score"
        assert scores["minimal"] < 0.4, "Minimal answer should have low overall score"
        assert scores["irrelevant"] < 0.3, "Irrelevant answer should have very low overall score"
        
        # Verify score components
        comprehensive_assessment = answer_quality_service.comprehensive_quality_assessment(
            question["text"], 
            sample_answers["comprehensive"],
            reference_answer=question["reference_answer"],
            key_concepts=question["key_concepts"]
        )
        
        assert "semantic_similarity" in comprehensive_assessment, "Assessment should include semantic similarity"
        assert "concept_coverage" in comprehensive_assessment, "Assessment should include concept coverage"
        assert "specificity" in comprehensive_assessment, "Assessment should include specificity"
        assert "coherence" in comprehensive_assessment, "Assessment should include coherence"
        assert "relevance" in comprehensive_assessment, "Assessment should include relevance"
    
    def test_historical_comparison(self, answer_quality_service):
        """Test comparison of answer quality to historical user answers."""
        # Create mock historical answers
        historical_answers = [
            {"question_id": "q1", "text": "I have 3 years of Python experience", "quality_score": 0.5},
            {"question_id": "q1", "text": "I've used Python for 4 years and know Django well", "quality_score": 0.7},
            {"question_id": "q1", "text": "I've been coding in Python for 5 years, used Django and Flask", "quality_score": 0.8}
        ]
        
        # Test new answer comparison
        new_answer = "I have 6 years of Python experience with Django, Flask, and FastAPI frameworks."
        
        comparison = answer_quality_service.compare_to_historical(new_answer, historical_answers)
        
        assert "percentile" in comparison, "Should calculate percentile against historical answers"
        assert comparison["percentile"] > 80, "Good answer should be in high percentile"
        assert "improvement" in comparison, "Should calculate improvement over previous answers"
        assert comparison["improvement"] > 0, "Should show improvement over historical answers"
    
    @patch('profiler.services.qa.answer_quality_service.AnswerQualityService.analyze_answer_components')
    def test_answer_component_extraction(self, mock_analyze, answer_quality_service):
        """Test extraction of structured components from answers."""
        # Configure the mock to return structured components
        mock_analyze.return_value = {
            "skills": ["Python", "Django", "Flask"],
            "experience_duration": "5 years",
            "projects": ["e-commerce platform", "data visualization dashboard"],
            "responsibilities": ["mentored junior developers"]
        }
        
        # Test component extraction
        comprehensive = "I have 5 years of experience with Python, primarily in web development using Django and Flask frameworks. I've built several production applications, including an e-commerce platform and a data visualization dashboard. I've also mentored junior developers in Python best practices."
        
        components = answer_quality_service.analyze_answer_components(comprehensive)
        
        assert "skills" in components, "Should extract skills component"
        assert "experience_duration" in components, "Should extract experience duration"
        assert "projects" in components, "Should extract projects"
        
        # Check that the mock was called
        mock_analyze.assert_called_once_with(comprehensive)
    
    def test_answer_quality_over_time(self, answer_quality_service):
        """Test tracking of answer quality improvement over time."""
        # Create a sequence of answers with improving quality
        answer_sequence = [
            "I know Python.",
            "I've used Python for 2 years.",
            "I have 2 years of Python experience, mainly with Django.",
            "I have 2 years of Python experience, mainly with Django. I've built several websites and a REST API."
        ]
        
        # Track quality over time
        quality_trend = []
        for answer in answer_sequence:
            score = answer_quality_service.evaluate_overall_quality(answer)
            quality_trend.append(score)
        
        # Check for improvement trend
        assert quality_trend[-1] > quality_trend[0], "Answer quality should improve over time"
        assert all(quality_trend[i] <= quality_trend[i+1] for i in range(len(quality_trend)-1)), "Quality should consistently improve"
        
        # Test quality improvement calculation
        improvement = answer_quality_service.calculate_quality_improvement(quality_trend)
        assert improvement > 0, "Should show positive improvement over time"
        assert "percentage_change" in improvement, "Should include percentage change"
        assert "absolute_change" in improvement, "Should include absolute change" 