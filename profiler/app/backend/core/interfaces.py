"""
Interfaces for AI clients.

This module defines abstract base classes for AI clients to ensure
consistent interfaces regardless of the underlying model provider.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union

class AIClientInterface(ABC):
    """Interface for AI model clients."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the client."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the client and release resources."""
        pass
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on a prompt.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters for the generation
            
        Returns:
            Generated text as a string
        """
        pass
    
    @abstractmethod
    async def generate_structured_output(
        self, 
        messages: List[Dict[str, str]], 
        response_schema: Dict[str, Any],
        **kwargs
    ) -> Any:
        """
        Generate structured output based on a prompt, conforming to a schema.
        
        Args:
            messages: List of message dictionaries with role and content
            response_schema: JSON schema for the expected response
            **kwargs: Additional parameters for the generation
            
        Returns:
            Structured output conforming to the schema
        """
        pass
    
    @abstractmethod
    async def extract_data(
        self,
        text: str,
        data_schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract structured data from text.
        
        Args:
            text: The input text to extract data from
            data_schema: JSON schema for the expected data structure
            **kwargs: Additional parameters for the extraction
            
        Returns:
            Extracted data as a dictionary
        """
        pass
    
    @abstractmethod
    async def classify_text(
        self,
        text: str,
        categories: List[str],
        **kwargs
    ) -> Dict[str, float]:
        """
        Classify text into one or more categories.
        
        Args:
            text: The input text to classify
            categories: List of possible categories
            **kwargs: Additional parameters for the classification
            
        Returns:
            Dictionary mapping categories to confidence scores
        """
        pass
    
    @abstractmethod
    async def analyze_document(
        self,
        document: str,
        document_type: str,
        analysis_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze a document and extract insights.
        
        Args:
            document: The document content
            document_type: Type of document (e.g., "resume", "cover_letter")
            analysis_type: Type of analysis to perform
            **kwargs: Additional parameters for the analysis
            
        Returns:
            Analysis results as a dictionary
        """
        pass
    
    @abstractmethod
    async def generate_embeddings(
        self,
        texts: List[str],
        **kwargs
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to generate embeddings for
            **kwargs: Additional parameters for embedding generation
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chat completion response.
        
        Args:
            messages: List of message dictionaries with role and content
            **kwargs: Additional parameters for the completion
            
        Returns:
            Chat completion response
        """
        pass 