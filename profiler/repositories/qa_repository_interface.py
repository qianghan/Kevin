from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class QARepositoryInterface(ABC):
    """
    Interface for the Q&A repository.
    This repository handles storage and retrieval of Q&A data.
    """
    
    @abstractmethod
    def get_questions_for_profile(self, profile_id: str) -> List[Dict[str, Any]]:
        """
        Get questions for a profile.
        
        Args:
            profile_id: The ID of the profile
            
        Returns:
            A list of question objects
        """
        pass
        
    @abstractmethod
    def save_question(self, question: Dict[str, Any]) -> str:
        """
        Save a question.
        
        Args:
            question: The question object
            
        Returns:
            The ID of the saved question
        """
        pass
        
    @abstractmethod
    def get_question(self, question_id: str) -> Dict[str, Any]:
        """
        Get a question by ID.
        
        Args:
            question_id: The ID of the question
            
        Returns:
            The question object
        """
        pass
        
    @abstractmethod
    def save_answer(self, question_id: str, answer: Dict[str, Any]) -> str:
        """
        Save an answer for a question.
        
        Args:
            question_id: The ID of the question
            answer: The answer object
            
        Returns:
            The ID of the saved answer
        """
        pass
        
    @abstractmethod
    def get_answer(self, question_id: str) -> Dict[str, Any]:
        """
        Get the answer for a question.
        
        Args:
            question_id: The ID of the question
            
        Returns:
            The answer object
        """
        pass
        
    @abstractmethod
    def get_processed_answer(self, question_id: str) -> Dict[str, Any]:
        """
        Get the processed answer for a question.
        
        Args:
            question_id: The ID of the question
            
        Returns:
            The processed answer object
        """
        pass
        
    @abstractmethod
    def get_followup_questions(self, question_id: str) -> List[Dict[str, Any]]:
        """
        Get follow-up questions for a question.
        
        Args:
            question_id: The ID of the question
            
        Returns:
            A list of follow-up question objects
        """
        pass
        
    @abstractmethod
    def save_feedback(self, question_id: str, feedback: Dict[str, Any]) -> str:
        """
        Save feedback for a question.
        
        Args:
            question_id: The ID of the question
            feedback: The feedback object
            
        Returns:
            The ID of the saved feedback
        """
        pass
        
    @abstractmethod
    def get_feedback(self, question_id: str) -> Dict[str, Any]:
        """
        Get feedback for a question.
        
        Args:
            question_id: The ID of the question
            
        Returns:
            The feedback object
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
    def get_question_analytics(self, question_id: str) -> Dict[str, Any]:
        """
        Get analytics for a question.
        
        Args:
            question_id: The ID of the question
            
        Returns:
            Analytics data for the question
        """
        pass
        
    @abstractmethod
    def get_all_question_analytics(self) -> Dict[str, Any]:
        """
        Get analytics for all questions.
        
        Returns:
            Analytics data for all questions
        """
        pass
        
    @abstractmethod
    def get_latest_question_id(self) -> str:
        """
        Get the ID of the latest question.
        
        Returns:
            The ID of the latest question
        """
        pass 