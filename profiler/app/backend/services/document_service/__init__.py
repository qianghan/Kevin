"""
Document Service Module.

This module provides a SOLID-compliant document service for analyzing and processing 
various document types, extracting information, and generating insights.
"""

# Import models
from .models import DocumentAnalysis, DocumentType

# Import interfaces
from .interfaces import (
    DocumentAnalyzerInterface,
    InformationExtractorInterface,
    ConfidenceCalculatorInterface,
    PatternMatcherInterface
)

# Import concrete implementations
from .document_service import DocumentService
from .analyzers import TranscriptAnalyzer, EssayAnalyzer, ResumeAnalyzer
from .extractors import RegexExtractor, LLMExtractor
from .confidence import ConfidenceCalculator

__all__ = [
    # Models
    'DocumentAnalysis',
    'DocumentType',
    
    # Interfaces
    'DocumentAnalyzerInterface',
    'InformationExtractorInterface',
    'ConfidenceCalculatorInterface',
    'PatternMatcherInterface',
    
    # Concrete implementations
    'DocumentService',
    'TranscriptAnalyzer',
    'EssayAnalyzer',
    'ResumeAnalyzer',
    'RegexExtractor',
    'LLMExtractor',
    'ConfidenceCalculator',
] 