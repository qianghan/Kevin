"""
Document service interfaces.

This module provides the interfaces for document services.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IDocumentService(ABC):
    """Interface for document services."""
    
    @abstractmethod
    async def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get documents for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            A list of documents
        """
        pass
    
    @abstractmethod
    async def analyze_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a document and identify issues or improvements.
        
        Args:
            document: The document to analyze
            
        Returns:
            Analysis results with issues and improvement suggestions
        """
        pass 