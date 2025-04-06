"""
Document Service implementation.

This module provides the main DocumentService implementation that follows the SOLID principles,
utilizing specialized components for analyzing different types of documents.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from datetime import datetime

from ...core.interfaces import AIClientInterface
from ...utils.logging import get_logger
from ...utils.errors import ServiceError

from .interfaces import (
    DocumentServiceInterface, 
    DocumentAnalyzerInterface,
    InformationExtractorInterface,
    ConfidenceCalculatorInterface,
    PatternMatcherInterface,
    DocumentServiceFactoryInterface
)
from .models import DocumentType, DocumentAnalysis
from .pattern_matcher import RegexPatternMatcher
from .extractors import RegexExtractor, LLMExtractor
from .confidence import ConfidenceCalculator
from .analyzers import (
    TranscriptAnalyzer,
    EssayAnalyzer,
    ResumeAnalyzer,
    GenericDocumentAnalyzer
)

# Get logger
logger = get_logger(__name__)

class DocumentServiceFactory(DocumentServiceFactoryInterface):
    """Factory for creating document service components"""
    
    def __init__(self, ai_client: AIClientInterface):
        self.ai_client = ai_client
        self.pattern_matcher = RegexPatternMatcher()
        self.confidence_calculator = ConfidenceCalculator()
        
        # Create extractors
        self.regex_extractor = RegexExtractor(self.pattern_matcher)
        self.llm_extractor = LLMExtractor(self.ai_client)
        
        # Create analyzers
        self._analyzers = {
            DocumentType.TRANSCRIPT: TranscriptAnalyzer(
                self.regex_extractor,
                self.llm_extractor,
                self.confidence_calculator
            ),
            DocumentType.ESSAY: EssayAnalyzer(
                self.regex_extractor,
                self.llm_extractor,
                self.confidence_calculator
            ),
            DocumentType.RESUME: ResumeAnalyzer(
                self.regex_extractor,
                self.llm_extractor,
                self.confidence_calculator
            ),
            DocumentType.LETTER: GenericDocumentAnalyzer(
                self.regex_extractor,
                self.llm_extractor,
                self.confidence_calculator,
                DocumentType.LETTER
            ),
            DocumentType.OTHER: GenericDocumentAnalyzer(
                self.regex_extractor,
                self.llm_extractor,
                self.confidence_calculator
            )
        }
    
    def get_analyzer(self, document_type: DocumentType) -> DocumentAnalyzerInterface:
        """
        Get an analyzer for the specified document type.
        
        Args:
            document_type: Type of the document
            
        Returns:
            Analyzer for the specified document type
        """
        return self._analyzers.get(document_type, self._analyzers[DocumentType.OTHER])
    
    def get_extractor(self, extraction_type: str) -> InformationExtractorInterface:
        """
        Get an extractor of the specified type.
        
        Args:
            extraction_type: Type of extraction (regex, llm, etc.)
            
        Returns:
            Extractor of the specified type
        """
        if extraction_type == "llm":
            return self.llm_extractor
        else:
            return self.regex_extractor
    
    def get_confidence_calculator(self) -> ConfidenceCalculatorInterface:
        """
        Get a confidence calculator.
        
        Returns:
            Confidence calculator instance
        """
        return self.confidence_calculator

class DocumentService(DocumentServiceInterface):
    """Service for analyzing documents and extracting information"""
    
    def __init__(self, ai_client: AIClientInterface):
        self.factory = DocumentServiceFactory(ai_client)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the document service"""
        try:
            logger.info("Initializing document service")
            # Perform any necessary initialization
            self._initialized = True
            logger.info("Document service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing document service: {str(e)}")
            raise ServiceError(f"Failed to initialize document service: {str(e)}")
    
    async def shutdown(self) -> None:
        """Shutdown the document service"""
        try:
            logger.info("Shutting down document service")
            # Perform any necessary cleanup
            self._initialized = False
            logger.info("Document service shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down document service: {str(e)}")
            raise ServiceError(f"Failed to shut down document service: {str(e)}")
    
    async def analyze(
        self, 
        content: str, 
        document_type: DocumentType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentAnalysis:
        """
        Analyze document content and extract information.
        
        Args:
            content: The document content
            document_type: Type of the document
            metadata: Optional metadata about the document
            
        Returns:
            Document analysis results
        """
        if not self._initialized:
            logger.warning("Document service not initialized. Initializing now.")
            await self.initialize()
        
        try:
            logger.info(f"Analyzing document of type: {document_type}")
            
            # Get the appropriate analyzer for the document type
            analyzer = self.factory.get_analyzer(document_type)
            
            # Analyze the document
            result = await analyzer.analyze(content, metadata)
            
            # Create DocumentAnalysis object
            analysis = DocumentAnalysis(
                content_type=document_type,
                extracted_info=result["extracted_info"],
                insights=result.get("insights", []),
                confidence=result["confidence"],
                metadata=result["metadata"]
            )
            
            logger.info(
                f"Document analysis complete. "
                f"Type: {document_type}, "
                f"Confidence: {analysis.confidence:.2f}"
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing document: {str(e)}")
            raise ServiceError(f"Document analysis failed: {str(e)}")

    async def detect_document_type(self, content: str) -> DocumentType:
        """
        Detect the type of document based on content.
        
        Args:
            content: The document content
            
        Returns:
            Detected document type
        """
        if not self._initialized:
            logger.warning("Document service not initialized. Initializing now.")
            await self.initialize()
        
        try:
            logger.info("Detecting document type")
            
            # Use LLM extractor to detect document type
            extractor = self.factory.get_extractor("llm")
            
            # Extract basic info from generic document
            info = await extractor.extract_advanced_info(
                content, 
                DocumentType.OTHER,
                {}
            )
            
            # Determine document type based on LLM analysis
            likely_type = info.get("likely_document_type", "").lower()
            
            # Map to DocumentType enum
            if "transcript" in likely_type or "academic" in likely_type:
                detected_type = DocumentType.TRANSCRIPT
            elif "essay" in likely_type or "paper" in likely_type:
                detected_type = DocumentType.ESSAY
            elif "resume" in likely_type or "cv" in likely_type:
                detected_type = DocumentType.RESUME
            elif "letter" in likely_type or "correspondence" in likely_type:
                detected_type = DocumentType.LETTER
            else:
                detected_type = DocumentType.OTHER
            
            logger.info(f"Detected document type: {detected_type}")
            
            return detected_type
            
        except Exception as e:
            logger.error(f"Error detecting document type: {str(e)}")
            # Default to OTHER on error
            return DocumentType.OTHER 