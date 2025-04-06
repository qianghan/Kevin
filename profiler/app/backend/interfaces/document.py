"""
Interface definitions for document service.

This module defines the interfaces for the document analysis service.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class DocumentAnalysis:
    """Represents the results of document analysis."""
    
    def __init__(
        self,
        document_id: str,
        content_type: str,
        text_content: str,
        extracted_data: Dict[str, Any],
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None,
        sections: Optional[List[Dict[str, Any]]] = None,
        analysis: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a DocumentAnalysis object.
        
        Args:
            document_id: Unique identifier for the document
            content_type: Type of the document (e.g., transcript, essay)
            text_content: The text content of the document
            extracted_data: Structured data extracted from the document
            confidence: Confidence score for the extraction (0-1)
            metadata: Additional metadata about the document
            sections: Optional list of document sections
            analysis: Optional additional analysis results
        """
        self.document_id = document_id
        self.content_type = content_type
        self.text_content = text_content
        self.extracted_data = extracted_data
        self.confidence = confidence
        self.metadata = metadata or {}
        self.sections = sections or []
        self.analysis = analysis or {}
    
    def dict(self) -> Dict[str, Any]:
        """
        Convert the DocumentAnalysis object to a dictionary.
        
        Returns:
            A dictionary representation of the DocumentAnalysis
        """
        result = {
            "content_type": self.content_type,
            "extracted_info": self.extracted_data,
            "confidence": self.confidence
        }
        
        if self.metadata:
            result["metadata"] = self.metadata
        
        return result


class IDocumentService(ABC):
    """Interface for document services."""
    
    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the service with the provided settings.
        
        Args:
            config: Configuration parameters for the service
        """
        pass
    
    @abstractmethod
    def analyze_document(
        self,
        content: str,
        document_type: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentAnalysis:
        """
        Analyze a document and extract structured information.
        
        Args:
            content: The text content of the document
            document_type: The type of document being analyzed
            user_id: ID of the user who uploaded the document
            metadata: Optional metadata about the document
            
        Returns:
            A DocumentAnalysis object with the analysis results
        """
        pass
    
    @abstractmethod
    def validate_document_type(self, document_type: str) -> bool:
        """
        Check if a document type is supported by the service.
        
        Args:
            document_type: The document type to validate
            
        Returns:
            True if the document type is supported, False otherwise
        """
        pass
    
    @abstractmethod
    def validate_document_format(
        self, 
        content: str, 
        document_type: str
    ) -> bool:
        """
        Validate that a document's content matches the expected format.
        
        Args:
            content: The document content to validate
            document_type: The expected document type
            
        Returns:
            True if the document format is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_document_types(self) -> List[str]:
        """
        Get a list of document types supported by the service.
        
        Returns:
            A list of supported document type identifiers
        """
        pass 