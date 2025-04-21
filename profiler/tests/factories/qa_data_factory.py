from typing import List, Dict, Any, Optional
import random

class QADataFactory:
    """
    Factory for generating test data for the Q&A system.
    """
    
    @staticmethod
    def generate_profile(profile_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Generate a test profile.
        
        Args:
            profile_id: Optional profile ID
            user_id: Optional user ID
            
        Returns:
            A test profile
        """
        if not profile_id:
            profile_id = f"profile_{random.randint(1000, 9999)}"
            
        if not user_id:
            user_id = f"user_{random.randint(1000, 9999)}"
            
        return {
            'id': profile_id,
            'user_id': user_id,
            'name': f"Test User {random.randint(1, 100)}",
            'email': f"test{random.randint(1, 100)}@example.com",
            'professional_info': {
                'title': random.choice(['Software Engineer', 'Product Manager', 'Data Scientist', 'UX Designer']),
                'company': random.choice(['Tech Co', 'Innovate Inc', 'Digital Solutions', 'Code Masters']),
                'years_experience': random.randint(1, 20),
                'industry': random.choice(['Technology', 'Finance', 'Healthcare', 'Education'])
            },
            'education': [
                {
                    'degree': random.choice(['Bachelor of Science', 'Master of Science', 'PhD']),
                    'field': random.choice(['Computer Science', 'Business', 'Engineering', 'Design']),
                    'institution': random.choice(['Tech University', 'State College', 'Institute of Design']),
                    'year_completed': random.randint(2000, 2022)
                }
            ],
            'skills': [
                {'name': 'Python', 'level': random.choice(['Beginner', 'Intermediate', 'Advanced', 'Expert'])},
                {'name': 'Java', 'level': random.choice(['Beginner', 'Intermediate', 'Advanced', 'Expert'])},
                {'name': 'Design', 'level': random.choice(['Beginner', 'Intermediate', 'Advanced', 'Expert'])}
            ]
        }
        
    @staticmethod
    def generate_questions(count: int = 5) -> List[Dict[str, Any]]:
        """
        Generate a list of test questions.
        
        Args:
            count: Number of questions to generate
            
        Returns:
            A list of test questions
        """
        questions = []
        categories = ['professional', 'education', 'skills', 'projects', 'goals']
        
        for i in range(1, count + 1):
            questions.append({
                'id': str(i),
                'text': f"Test question {i}?",
                'category': random.choice(categories),
                'follow_up_questions': [str(j) for j in range(i+1, min(i+3, count+1))]
            })
            
        return questions
        
    @staticmethod
    def generate_answers(questions: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Generate test answers for a list of questions.
        
        Args:
            questions: List of questions
            
        Returns:
            Dictionary mapping question IDs to answers
        """
        answers = {}
        
        for question in questions:
            answers[question['id']] = f"This is a test answer for question {question['id']}."
            
        return answers
        
    @staticmethod
    def generate_feedback(questions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Generate test feedback for a list of questions.
        
        Args:
            questions: List of questions
            
        Returns:
            Dictionary mapping question IDs to feedback
        """
        feedback = {}
        
        for question in questions:
            feedback[question['id']] = {
                'feedback_text': f"Feedback for question {question['id']}",
                'rating': random.randint(1, 5)
            }
            
        return feedback 