"""
QA service interfaces.

This module provides the interfaces for QA services.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union


class IQAService(ABC):
    """Interface for QA services."""
    
    @abstractmethod
    async def get_recent_user_answers(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent answers from a user.
        
        Args:
            user_id: The ID of the user
            limit: Maximum number of answers to return
            
        Returns:
            A list of recent answers
        """
        pass
    
    @abstractmethod
    async def evaluate_answer_quality(self, answer: Dict[str, Any]) -> float:
        """
        Evaluate the quality of an answer.
        
        Args:
            answer: The answer to evaluate
            
        Returns:
            A quality score between 0.0 and 1.0
        """
        pass 