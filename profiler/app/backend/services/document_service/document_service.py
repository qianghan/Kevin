"""
Document Service implementation.

This module provides the main DocumentService implementation that follows the SOLID principles,
utilizing specialized components for analyzing different types of documents.
"""

import logging
from typing import Dict, Any, List, Optional, Type
from datetime import datetime
import asyncio
import uuid

from ...core.interfaces import AIClientInterface
from ...utils.logging import get_logger
from ...utils.errors import ServiceError
from ...utils.config_manager import ConfigManager

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
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the document service.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or ConfigManager().get_all()
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Get AI client from config
        ai_client = None
        if "ai_client" in self.config:
            ai_client = self.config["ai_client"]
        elif "ai_clients" in self.config and "deepseek" in self.config["ai_clients"]:
            from ...core.deepseek.r1 import DeepSeekR1
            ai_client = DeepSeekR1(
                api_key=self.config["ai_clients"]["deepseek"]["api_key"],
                base_url=self.config["ai_clients"]["deepseek"]["url"]
            )
        else:
            # Default to a mock client for testing
            from ...core.interfaces import AIClientInterface
            class MockClient(AIClientInterface):
                async def complete(self, prompt, **kwargs):
                    return {"text": "This is a mock response"}
            ai_client = MockClient()
        
        self.factory = DocumentServiceFactory(ai_client)
    
    async def initialize(self) -> None:
        """Initialize the service asynchronously."""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:  # Double check to prevent race conditions
                return
                
            try:
                logger.info("Initializing document service")
                # Add any async initialization logic here
                # For example, connecting to databases or external services
                await asyncio.sleep(0)  # Placeholder for actual initialization
                self._initialized = True
                logger.info("Document service initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize DocumentService: {str(e)}")
                raise ServiceError(f"DocumentService initialization failed: {str(e)}")
    
    async def shutdown(self) -> None:
        """Shutdown the document service."""
        if not self._initialized:
            return
            
        async with self._lock:
            if not self._initialized:  # Double check to prevent race conditions
                return
                
            try:
                logger.info("Shutting down document service")
                # Add cleanup logic here
                self._initialized = False
                logger.info("Document service shut down successfully")
                
            except Exception as e:
                logger.error(f"Failed to shut down DocumentService: {str(e)}")
                raise ServiceError(f"Failed to shut down DocumentService: {str(e)}")
    
    async def close(self) -> None:
        """Alias for shutdown to maintain backward compatibility."""
        await self.shutdown()
    
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

    async def store_document(
        self, 
        content: str, 
        document_type: DocumentType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a document and return a unique identifier.
        
        Args:
            content: The document content
            document_type: Type of the document
            metadata: Optional metadata about the document
            
        Returns:
            A unique document ID
        """
        if not self._initialized:
            logger.warning("Document service not initialized. Initializing now.")
            await self.initialize()
        
        try:
            logger.info(f"Storing document of type: {document_type}")
            
            # Generate a unique document ID
            document_id = str(uuid.uuid4())
            
            # Add timestamp and document_id to metadata
            metadata_with_id = {
                **(metadata or {}),
                "document_id": document_id,
                "stored_at": datetime.utcnow().isoformat(),
                "document_type": document_type.value,
                "document_length": len(content)
            }
            
            # In a real implementation, this would store the document in a database
            # For this implementation, we'll just log it
            logger.info(f"Document stored with ID: {document_id}")
            
            # If we had a repository, we would do something like:
            # await self.repository.store_document(document_id, content, document_type, metadata_with_id)
            
            return document_id
            
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            raise ServiceError(f"Document storage failed: {str(e)}") 