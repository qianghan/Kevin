import pytest
import time
from unittest.mock import MagicMock, patch
import random
import string

from profiler.services.qa.enhanced_qa_service import EnhancedQAService
from profiler.services.qa.qa_integration_service import QAIntegrationService
from profiler.tests.fixtures.qa_fixtures import mock_qa_repository

class TestBatchProcessing:
    """Performance tests for batch question processing."""
    
    @pytest.fixture
    def enhanced_qa_service(self, mock_qa_repository):
        """Create an enhanced QA service with a mock repository."""
        return EnhancedQAService(mock_qa_repository)
    
    @pytest.fixture
    def qa_integration_service(self, mock_qa_repository):
        """Create a QA integration service with a mock repository."""
        return QAIntegrationService(mock_qa_repository)
    
    @pytest.fixture
    def large_profile_batch(self):
        """Generate a batch of profile data for performance testing."""
        profiles = []
        for i in range(10):
            profile_id = f"profile_{i}"
            profile = {
                "id": profile_id,
                "personal": {
                    "name": f"Test User {i}",
                    "email": f"test{i}@example.com"
                },
                "professional": {
                    "experience": [
                        {
                            "company": f"Company {j}",
                            "position": f"Position {j}",
                            "duration": f"{random.randint(1, 5)} years",
                            "description": ''.join(random.choices(string.ascii_letters + ' ', k=200))
                        } for j in range(random.randint(1, 3))
                    ]
                },
                "education": {
                    "institutions": [
                        {
                            "name": f"University {j}",
                            "degree": f"Degree {j}",
                            "field": f"Field {j}",
                            "year": 2010 + j
                        } for j in range(random.randint(1, 2))
                    ]
                },
                "skills": {
                    "technical": [f"Skill {j}" for j in range(random.randint(3, 8))],
                    "soft": [f"Soft Skill {j}" for j in range(random.randint(2, 5))]
                }
            }
            profiles.append(profile)
        return profiles
    
    @pytest.fixture
    def batch_questions(self):
        """Generate a batch of questions for performance testing."""
        categories = ["professional", "education", "skills", "projects", "achievements"]
        questions = []
        for i in range(50):
            question = {
                "id": f"q{i}",
                "text": f"Question {i}: {''.join(random.choices(string.ascii_letters + ' ?', k=50))}",
                "category": random.choice(categories),
                "importance": round(random.uniform(0.1, 1.0), 1)
            }
            questions.append(question)
        return questions
    
    @pytest.fixture
    def batch_answers(self):
        """Generate a batch of answers for performance testing."""
        answers = []
        for i in range(200):
            answer = {
                "id": f"a{i}",
                "question_id": f"q{random.randint(0, 49)}",
                "profile_id": f"profile_{random.randint(0, 9)}",
                "answer_text": ''.join(random.choices(string.ascii_letters + ' .', k=random.randint(20, 300)))
            }
            answers.append(answer)
        return answers
    
    def test_batch_question_generation_performance(self, enhanced_qa_service, large_profile_batch, mocker):
        """Test performance of generating questions for multiple profiles in batch."""
        # Mock the question generation to avoid actual NLP processing
        mocker.patch.object(
            enhanced_qa_service, 
            'generate_questions', 
            side_effect=lambda profile, count=10: [
                {
                    "id": f"q{i}",
                    "text": f"Generated question {i} for {profile['id']}",
                    "category": random.choice(["professional", "education", "skills"]),
                    "importance": round(random.uniform(0.5, 1.0), 1)
                } for i in range(count)
            ]
        )
        
        # Run batch processing
        start_time = time.time()
        results = []
        for profile in large_profile_batch:
            questions = enhanced_qa_service.generate_questions(profile)
            results.append({
                "profile_id": profile["id"],
                "questions": questions
            })
        end_time = time.time()
        
        # Performance assertions
        processing_time = end_time - start_time
        num_profiles = len(large_profile_batch)
        avg_time_per_profile = processing_time / num_profiles
        
        # Print performance metrics for debugging
        print(f"\nBatch question generation performance:")
        print(f"Total profiles: {num_profiles}")
        print(f"Total processing time: {processing_time:.4f} seconds")
        print(f"Average time per profile: {avg_time_per_profile:.4f} seconds")
        
        # Assertions
        assert processing_time < 5.0, f"Batch processing should complete in under 5 seconds, took {processing_time:.4f}"
        assert avg_time_per_profile < 0.5, f"Each profile should process in under 0.5 seconds, took {avg_time_per_profile:.4f}"
        
        # Verify all profiles were processed
        assert len(results) == len(large_profile_batch), "All profiles should be processed"
        
        # Verify each profile has questions
        for result in results:
            assert len(result["questions"]) > 0, f"Profile {result['profile_id']} should have questions"
    
    def test_batch_answer_evaluation_performance(self, enhanced_qa_service, batch_questions, batch_answers, mocker):
        """Test performance of evaluating multiple answers in batch."""
        # Create a mapping from question_id to question for lookups
        question_map = {q["id"]: q for q in batch_questions}
        
        # Mock the answer evaluation to avoid actual NLP processing
        mocker.patch.object(
            enhanced_qa_service, 
            'evaluate_answer_quality', 
            side_effect=lambda question, answer_text: {
                "quality_score": round(random.uniform(0.1, 1.0), 2),
                "extracted_information": {"key": "value"} if len(answer_text) > 100 else {},
                "feedback": ["Add more detail"] if len(answer_text) < 100 else []
            }
        )
        
        # Run batch evaluation
        start_time = time.time()
        results = []
        for answer in batch_answers:
            if answer["question_id"] in question_map:
                quality_result = enhanced_qa_service.evaluate_answer_quality(
                    question_map[answer["question_id"]],
                    answer["answer_text"]
                )
                results.append({
                    "answer_id": answer["id"],
                    "quality_result": quality_result
                })
        end_time = time.time()
        
        # Performance assertions
        processing_time = end_time - start_time
        num_answers = len(batch_answers)
        avg_time_per_answer = processing_time / num_answers
        
        # Print performance metrics for debugging
        print(f"\nBatch answer evaluation performance:")
        print(f"Total answers: {num_answers}")
        print(f"Total processing time: {processing_time:.4f} seconds")
        print(f"Average time per answer: {avg_time_per_answer:.4f} seconds")
        
        # Assertions
        assert processing_time < 10.0, f"Batch processing should complete in under 10 seconds, took {processing_time:.4f}"
        assert avg_time_per_answer < 0.05, f"Each answer should process in under 0.05 seconds, took {avg_time_per_answer:.4f}"
        
        # Verify all answers with valid questions were processed
        valid_answers = [a for a in batch_answers if a["question_id"] in question_map]
        assert len(results) == len(valid_answers), "All valid answers should be processed"
    
    @patch("profiler.services.qa.qa_integration_service.QAIntegrationService.calculate_profile_completeness")
    def test_batch_profile_analysis_performance(self, mock_completeness, qa_integration_service, large_profile_batch):
        """Test performance of analyzing multiple profiles in batch."""
        # Mock the profile completeness calculation
        mock_completeness.side_effect = lambda profile_id: {
            "overall_score": round(random.uniform(0.3, 0.9), 2),
            "category_scores": {
                "professional": round(random.uniform(0.4, 0.9), 2),
                "education": round(random.uniform(0.4, 0.9), 2),
                "skills": round(random.uniform(0.4, 0.9), 2),
                "projects": round(random.uniform(0.2, 0.8), 2),
                "achievements": round(random.uniform(0.1, 0.7), 2)
            },
            "unanswered_questions": [f"q{i}" for i in range(random.randint(0, 5))]
        }
        
        # Run batch analysis
        start_time = time.time()
        results = []
        for profile in large_profile_batch:
            completeness = qa_integration_service.calculate_profile_completeness(profile["id"])
            gaps = qa_integration_service.identify_profile_gaps(completeness)
            results.append({
                "profile_id": profile["id"],
                "completeness": completeness,
                "gaps": gaps
            })
        end_time = time.time()
        
        # Performance assertions
        processing_time = end_time - start_time
        num_profiles = len(large_profile_batch)
        avg_time_per_profile = processing_time / num_profiles
        
        # Print performance metrics for debugging
        print(f"\nBatch profile analysis performance:")
        print(f"Total profiles: {num_profiles}")
        print(f"Total processing time: {processing_time:.4f} seconds")
        print(f"Average time per profile: {avg_time_per_profile:.4f} seconds")
        
        # Assertions
        assert processing_time < 2.0, f"Batch analysis should complete in under 2 seconds, took {processing_time:.4f}"
        assert avg_time_per_profile < 0.2, f"Each profile should be analyzed in under 0.2 seconds, took {avg_time_per_profile:.4f}"
        
        # Verify all profiles were analyzed
        assert len(results) == len(large_profile_batch), "All profiles should be analyzed"
    
    def test_parallel_batch_processing(self, enhanced_qa_service, large_profile_batch, mocker):
        """Test performance of parallel batch processing of profiles."""
        # This test simulates parallel processing using a threadpool
        import concurrent.futures
        
        # Mock the question generation to avoid actual NLP processing
        mocker.patch.object(
            enhanced_qa_service, 
            'generate_questions', 
            side_effect=lambda profile, count=10: [
                {
                    "id": f"q{i}",
                    "text": f"Generated question {i} for {profile['id']}",
                    "category": random.choice(["professional", "education", "skills"]),
                    "importance": round(random.uniform(0.5, 1.0), 1)
                } for i in range(count)
            ]
        )
        
        # Define a worker function for parallel processing
        def process_profile(profile):
            questions = enhanced_qa_service.generate_questions(profile)
            return {
                "profile_id": profile["id"],
                "questions": questions
            }
        
        # Run parallel batch processing
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(process_profile, large_profile_batch))
        end_time = time.time()
        
        # Performance assertions
        processing_time = end_time - start_time
        num_profiles = len(large_profile_batch)
        avg_time_per_profile = processing_time / num_profiles
        
        # Print performance metrics for debugging
        print(f"\nParallel batch processing performance:")
        print(f"Total profiles: {num_profiles}")
        print(f"Total processing time: {processing_time:.4f} seconds")
        print(f"Average time per profile: {avg_time_per_profile:.4f} seconds")
        
        # Assertions
        assert processing_time < 3.0, f"Parallel batch processing should complete in under 3 seconds, took {processing_time:.4f}"
        assert avg_time_per_profile < 0.3, f"Each profile should process in under 0.3 seconds (parallel), took {avg_time_per_profile:.4f}"
        
        # Verify all profiles were processed
        assert len(results) == len(large_profile_batch), "All profiles should be processed"
    
    def test_batch_question_recommendation_performance(self, qa_integration_service, large_profile_batch, mocker):
        """Test performance of recommending questions for multiple profiles in batch."""
        # Mock the recommendation function
        mocker.patch.object(
            qa_integration_service, 
            'recommend_next_questions', 
            side_effect=lambda profile_id, count=5: [
                {
                    "id": f"rec_q{i}",
                    "text": f"Recommended question {i} for {profile_id}",
                    "category": random.choice(["professional", "education", "skills"]),
                    "importance": round(random.uniform(0.7, 1.0), 1),
                    "reason": f"To improve profile completion in {random.choice(['professional', 'education', 'skills'])}"
                } for i in range(count)
            ]
        )
        
        # Run batch recommendation
        start_time = time.time()
        results = []
        for profile in large_profile_batch:
            recommended_questions = qa_integration_service.recommend_next_questions(profile["id"])
            results.append({
                "profile_id": profile["id"],
                "recommended_questions": recommended_questions
            })
        end_time = time.time()
        
        # Performance assertions
        processing_time = end_time - start_time
        num_profiles = len(large_profile_batch)
        avg_time_per_profile = processing_time / num_profiles
        
        # Print performance metrics for debugging
        print(f"\nBatch question recommendation performance:")
        print(f"Total profiles: {num_profiles}")
        print(f"Total processing time: {processing_time:.4f} seconds")
        print(f"Average time per profile: {avg_time_per_profile:.4f} seconds")
        
        # Assertions
        assert processing_time < 2.0, f"Batch recommendation should complete in under 2 seconds, took {processing_time:.4f}"
        assert avg_time_per_profile < 0.2, f"Each profile recommendation should process in under 0.2 seconds, took {avg_time_per_profile:.4f}"
        
        # Verify all profiles received recommendations
        assert len(results) == len(large_profile_batch), "All profiles should receive recommendations"
        
        # Verify each profile has the expected number of recommendations
        for result in results:
            assert len(result["recommended_questions"]) == 5, f"Profile {result['profile_id']} should have 5 recommended questions"
            
            # Check that recommendations have required fields
            for question in result["recommended_questions"]:
                assert "id" in question, "Question should have an ID"
                assert "text" in question, "Question should have text"
                assert "category" in question, "Question should have a category"
                assert "importance" in question, "Question should have importance"
                assert "reason" in question, "Question should have a reason for recommendation" 