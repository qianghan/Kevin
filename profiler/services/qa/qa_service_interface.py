from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class QAServiceInterface(ABC):
    """
    Interface for the Q&A service.
    This service handles question generation, answer processing, and feedback collection.
    """
    
    @abstractmethod
    def generate_questions(self, profile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate questions based on a user's profile.
        
        Args:
            profile_data: The user's profile data
            
        Returns:
            A list of question objects
        """
        pass
        
    @abstractmethod
    def process_answer(self, question_id: str, answer: str) -> Dict[str, Any]:
        """
        Process a user's answer to a question.
        
        Args:
            question_id: The ID of the question being answered
            answer: The user's answer text
            
        Returns:
            The processed answer object
        """
        pass
        
    @abstractmethod
    def generate_followup_questions(self, profile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate follow-up questions based on previous answers.
        
        Args:
            profile_data: The user's profile data
            
        Returns:
            A list of follow-up question objects
        """
        pass
        
    @abstractmethod
    def process_feedback(self, question_id: str, feedback: str, rating: Optional[int] = None) -> Dict[str, Any]:
        """
        Process user feedback on a question/answer.
        
        Args:
            question_id: The ID of the question that received feedback
            feedback: The feedback text
            rating: Optional numeric rating
            
        Returns:
            The processed feedback object
        """
        pass
        
    @abstractmethod
    def get_question_history(self, profile_id: str) -> List[Dict[str, Any]]:
        """
        Get the history of questions and answers for a profile.
        
        Args:
            profile_id: The ID of the profile
            
        Returns:
            A list of question/answer pairs
        """
        pass
        
    @abstractmethod
    def get_question_analytics(self, question_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get analytics for questions.
        
        Args:
            question_id: Optional ID of a specific question
            
        Returns:
            Analytics data for the question(s)
        """
        pass 