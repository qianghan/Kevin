"""
Interfaces for the Document Service.

This module defines the interfaces used throughout the document service,
following the SOLID principles, particularly the Interface Segregation Principle.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Protocol, Type
from .models import DocumentType, DocumentAnalysis

class PatternMatcherInterface(ABC):
    """Interface for pattern matching in documents"""
    
    @abstractmethod
    async def match_patterns(self, content: str, patterns: Dict[str, str]) -> Dict[str, List[Any]]:
        """
        Match patterns in the document content.
        
        Args:
            content: The document content
            patterns: Dictionary of named patterns
            
        Returns:
            Dictionary of pattern matches
        """
        pass

class InformationExtractorInterface(ABC):
    """Interface for extracting information from documents"""
    
    @abstractmethod
    async def extract_basic_info(self, content: str, document_type: DocumentType) -> Dict[str, Any]:
        """
        Extract basic information from document content.
        
        Args:
            content: The document content
            document_type: Type of the document
            
        Returns:
            Dictionary of extracted information
        """
        pass
    
    @abstractmethod
    async def extract_advanced_info(self, content: str, document_type: DocumentType, 
                               basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract advanced information from document content.
        
        Args:
            content: The document content
            document_type: Type of the document
            basic_info: Previously extracted basic information
            
        Returns:
            Dictionary of extracted advanced information
        """
        pass

class DocumentAnalyzerInterface(ABC):
    """Interface for document analysis"""
    
    @abstractmethod
    async def analyze(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze document content.
        
        Args:
            content: The document content
            metadata: Optional metadata about the document
            
        Returns:
            Analysis results
        """
        pass
    
    @abstractmethod
    def get_document_type(self) -> DocumentType:
        """
        Get the document type this analyzer handles.
        
        Returns:
            The document type
        """
        pass

class ConfidenceCalculatorInterface(ABC):
    """Interface for calculating confidence scores"""
    
    @abstractmethod
    def calculate_confidence(self, info: Dict[str, Any], document_type: DocumentType) -> float:
        """
        Calculate confidence score for analysis.
        
        Args:
            info: Extracted information
            document_type: Type of the document
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        pass

class DocumentServiceFactoryInterface(Protocol):
    """Interface for document service factory"""
    
    def get_analyzer(self, document_type: DocumentType) -> DocumentAnalyzerInterface:
        """
        Get an analyzer for the specified document type.
        
        Args:
            document_type: Type of the document
            
        Returns:
            Analyzer for the specified document type
        """
        pass
    
    def get_extractor(self, extraction_type: str) -> InformationExtractorInterface:
        """
        Get an extractor of the specified type.
        
        Args:
            extraction_type: Type of extraction (regex, llm, etc.)
            
        Returns:
            Extractor of the specified type
        """
        pass
    
    def get_confidence_calculator(self) -> ConfidenceCalculatorInterface:
        """
        Get a confidence calculator.
        
        Returns:
            Confidence calculator instance
        """
        pass

class DocumentServiceInterface(ABC):
    """Interface for the document service"""
    
    @abstractmethod
    async def analyze(self, content: str, document_type: DocumentType, 
                 metadata: Optional[Dict[str, Any]] = None) -> DocumentAnalysis:
        """
        Analyze document content and extract information.
        
        Args:
            content: The document content
            document_type: Type of the document
            metadata: Optional metadata about the document
            
        Returns:
            Document analysis results
        """
        pass
    
    @abstractmethod
    async def store_document(self, content: str, document_type: DocumentType,
                            metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a document and return a unique identifier.
        
        Args:
            content: The document content
            document_type: Type of the document
            metadata: Optional metadata about the document
            
        Returns:
            A unique document ID
        """
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the document service"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the document service"""
        pass 