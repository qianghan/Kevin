"""
Confidence calculator for the Document Service.

This module provides implementations of the ConfidenceCalculatorInterface
for calculating confidence scores for document analysis.
"""

import logging
from typing import Dict, Any, List, Set
import math

from .interfaces import ConfidenceCalculatorInterface
from .models import DocumentType

# Get logger
logger = logging.getLogger(__name__)

class ConfidenceCalculator(ConfidenceCalculatorInterface):
    """Implementation of ConfidenceCalculatorInterface for calculating confidence scores"""
    
    def __init__(self):
        # Define required fields for different document types
        self.required_fields = {
            DocumentType.TRANSCRIPT: {
                "grades", "courses", "terms"
            },
            DocumentType.ESSAY: {
                "word_count", "paragraph_count", "themes", "writing_style"
            },
            DocumentType.RESUME: {
                "sections", "skills", "experience_level"
            },
            DocumentType.LETTER: {
                "purpose", "tone", "key_points"
            },
            DocumentType.OTHER: {
                "content_summary"
            }
        }
        
        # Define field importance weights
        self.field_weights = {
            DocumentType.TRANSCRIPT: {
                "grades": 0.3, 
                "courses": 0.3, 
                "terms": 0.2,
                "academic_performance": 0.1,
                "gpa": 0.1
            },
            DocumentType.ESSAY: {
                "word_count": 0.1, 
                "paragraph_count": 0.1, 
                "themes": 0.25,
                "writing_style": 0.2,
                "structure_quality": 0.15,
                "argument_quality": 0.2
            },
            DocumentType.RESUME: {
                "sections": 0.15, 
                "skills": 0.25, 
                "key_achievements": 0.2,
                "career_progression": 0.15,
                "experience_level": 0.15,
                "strengths": 0.1
            },
            DocumentType.LETTER: {
                "greeting": 0.1,
                "closing": 0.1,
                "purpose": 0.3,
                "tone": 0.2,
                "key_points": 0.3
            },
            DocumentType.OTHER: {
                "likely_document_type": 0.2,
                "purpose": 0.3,
                "content_summary": 0.5
            }
        }
    
    def calculate_confidence(self, info: Dict[str, Any], document_type: DocumentType) -> float:
        """
        Calculate confidence score for analysis.
        
        Args:
            info: Extracted information
            document_type: Type of the document
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Check for LLM extraction errors
        if "error" in info:
            logger.warning(f"Error found in extracted info: {info['error']}")
            return 0.2  # Low confidence due to error
        
        # Calculate completeness score (presence of required fields)
        completeness_score = self._calculate_completeness(info, document_type)
        
        # Calculate richness score (amount of data extracted)
        richness_score = self._calculate_richness(info, document_type)
        
        # Calculate quality score (quality of extracted data)
        quality_score = self._calculate_quality(info, document_type)
        
        # Calculate source diversity score (how many different extraction methods contributed)
        source_diversity_score = self._calculate_source_diversity(info)
        
        # Calculate final confidence score (weighted average)
        final_score = (
            completeness_score * 0.4 +
            richness_score * 0.3 +
            quality_score * 0.2 +
            source_diversity_score * 0.1
        )
        
        logger.debug(
            f"Confidence calculation for {document_type}: "
            f"completeness={completeness_score:.2f}, "
            f"richness={richness_score:.2f}, "
            f"quality={quality_score:.2f}, "
            f"source_diversity={source_diversity_score:.2f}, "
            f"final={final_score:.2f}"
        )
        
        # Ensure the score is between 0 and 1
        return max(0.0, min(1.0, final_score))
    
    def _calculate_completeness(self, info: Dict[str, Any], document_type: DocumentType) -> float:
        """
        Calculate completeness score based on presence of required fields.
        
        Args:
            info: Extracted information
            document_type: Type of the document
            
        Returns:
            Completeness score between 0.0 and 1.0
        """
        # Get the required fields for this document type
        required = self.required_fields.get(document_type, set())
        
        if not required:
            return 0.5  # Default score for unknown document types
        
        # Count the number of required fields present in the info
        present_fields = set(info.keys()) & required
        
        # Calculate completeness score
        return len(present_fields) / len(required)
    
    def _calculate_richness(self, info: Dict[str, Any], document_type: DocumentType) -> float:
        """
        Calculate richness score based on amount of extracted data.
        
        Args:
            info: Extracted information
            document_type: Type of the document
            
        Returns:
            Richness score between 0.0 and 1.0
        """
        # Get weights for different fields
        weights = self.field_weights.get(document_type, {})
        
        if not weights:
            return 0.5  # Default score for unknown document types
        
        score = 0.0
        total_weight = 0.0
        
        for field, weight in weights.items():
            if field in info:
                field_value = info[field]
                
                # Calculate richness based on field type
                field_richness = 0.0
                
                if isinstance(field_value, list):
                    # For lists, use the length (capped at 10)
                    field_richness = min(1.0, len(field_value) / 10)
                elif isinstance(field_value, dict):
                    # For dictionaries, use the number of keys (capped at 10)
                    field_richness = min(1.0, len(field_value) / 10)
                elif isinstance(field_value, str):
                    # For strings, use the length (capped at 200 characters)
                    field_richness = min(1.0, len(field_value) / 200)
                elif isinstance(field_value, (int, float)):
                    # For numbers, just use 1.0 for non-zero values
                    field_richness = 1.0 if field_value != 0 else 0.0
                
                score += field_richness * weight
                total_weight += weight
        
        # If no fields matched, return minimum score
        if total_weight == 0:
            return 0.1
        
        # Return normalized score
        return score / total_weight
    
    def _calculate_quality(self, info: Dict[str, Any], document_type: DocumentType) -> float:
        """
        Calculate quality score based on quality of extracted data.
        
        Args:
            info: Extracted information
            document_type: Type of the document
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        # This is a simplified quality calculation
        # In a production system, this would be more sophisticated
        
        # Check if source is from LLM
        if info.get("source_type") == "llm":
            # Check for specific high-quality fields based on document type
            if document_type == DocumentType.TRANSCRIPT:
                if "academic_performance" in info and len(str(info["academic_performance"])) > 50:
                    return 0.8
            elif document_type == DocumentType.ESSAY:
                if "writing_style" in info and "structure_quality" in info:
                    return 0.8
            elif document_type == DocumentType.RESUME:
                if "skills_assessment" in info and "career_progression" in info:
                    return 0.8
            elif document_type == DocumentType.LETTER:
                if "purpose" in info and "effectiveness" in info:
                    return 0.8
            
            # Default LLM quality score
            return 0.6
        else:
            # For regex extraction, check field-specific quality
            if document_type == DocumentType.TRANSCRIPT:
                grades = info.get("grades", [])
                courses = info.get("courses", [])
                if len(grades) > 5 and len(courses) > 5:
                    return 0.9
                elif len(grades) > 2 and len(courses) > 2:
                    return 0.7
            elif document_type == DocumentType.ESSAY:
                word_count = info.get("word_count", 0)
                paragraph_count = info.get("paragraph_count", 0)
                if word_count > 500 and paragraph_count > 5:
                    return 0.85
                elif word_count > 200 and paragraph_count > 2:
                    return 0.7
            elif document_type == DocumentType.RESUME:
                sections = info.get("sections", [])
                skills = info.get("skills", [])
                if len(sections) > 4 and len(skills) > 5:
                    return 0.9
                elif len(sections) > 2 and len(skills) > 2:
                    return 0.7
            
            # Default regex quality score
            return 0.5
    
    def _calculate_source_diversity(self, info: Dict[str, Any]) -> float:
        """
        Calculate source diversity score based on extraction methods used.
        
        Args:
            info: Extracted information
            
        Returns:
            Source diversity score between 0.0 and 1.0
        """
        # Check for source types in the info
        sources = set()
        
        # Check top-level source type
        if "source_type" in info:
            sources.add(info["source_type"])
        
        # Scan for source types in nested dictionaries (up to 2 levels deep)
        for value in info.values():
            if isinstance(value, dict) and "source_type" in value:
                sources.add(value["source_type"])
                
                # Check one level deeper
                for nested_value in value.values():
                    if isinstance(nested_value, dict) and "source_type" in nested_value:
                        sources.add(nested_value["source_type"])
        
        # Calculate diversity score based on number of different sources
        # 1 source = 0.5, 2 sources = 0.9, 3+ sources = 1.0
        if len(sources) == 0:
            return 0.3
        elif len(sources) == 1:
            return 0.5
        elif len(sources) == 2:
            return 0.9
        else:
            return 1.0 