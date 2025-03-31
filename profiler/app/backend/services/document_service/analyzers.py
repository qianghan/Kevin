"""
Document analyzers for the Document Service.

This module provides implementations of the DocumentAnalyzerInterface
for analyzing different types of documents.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .interfaces import (
    DocumentAnalyzerInterface, 
    InformationExtractorInterface,
    ConfidenceCalculatorInterface
)
from .models import DocumentType, DocumentAnalysis, AnalysisInsight

# Get logger
logger = logging.getLogger(__name__)

class BaseDocumentAnalyzer(DocumentAnalyzerInterface):
    """Base document analyzer with common functionality"""
    
    def __init__(
        self,
        document_type: DocumentType,
        basic_extractor: InformationExtractorInterface,
        advanced_extractor: InformationExtractorInterface,
        confidence_calculator: ConfidenceCalculatorInterface
    ):
        self.document_type = document_type
        self.basic_extractor = basic_extractor
        self.advanced_extractor = advanced_extractor
        self.confidence_calculator = confidence_calculator
    
    async def analyze(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze document content.
        
        Args:
            content: The document content
            metadata: Optional metadata about the document
            
        Returns:
            Analysis results
        """
        try:
            # Extract basic information
            basic_info = await self.basic_extractor.extract_basic_info(content, self.document_type)
            
            # Extract advanced information
            advanced_info = await self.advanced_extractor.extract_advanced_info(
                content, self.document_type, basic_info
            )
            
            # Merge results
            combined_info = {**basic_info, **advanced_info}
            
            # Generate insights
            insights = self._generate_insights(combined_info)
            
            # Calculate confidence
            confidence = self.confidence_calculator.calculate_confidence(
                combined_info,
                self.document_type
            )
            
            # Create final result
            result = {
                "extracted_info": combined_info,
                "insights": insights,
                "confidence": confidence,
                "metadata": {
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "document_length": len(content),
                    "document_type": self.document_type.value,
                    **(metadata or {})
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {self.document_type} document: {str(e)}")
            # Return basic error result
            return {
                "extracted_info": {"error": str(e)},
                "insights": [],
                "confidence": 0.0,
                "metadata": {
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "document_length": len(content),
                    "document_type": self.document_type.value,
                    "error": str(e),
                    **(metadata or {})
                }
            }
    
    def get_document_type(self) -> DocumentType:
        """
        Get the document type this analyzer handles.
        
        Returns:
            The document type
        """
        return self.document_type
    
    def _generate_insights(self, info: Dict[str, Any]) -> List[AnalysisInsight]:
        """
        Generate insights from extracted information.
        
        Args:
            info: Extracted information
            
        Returns:
            List of insights
        """
        # This should be implemented by subclasses
        return []

class TranscriptAnalyzer(BaseDocumentAnalyzer):
    """Specialized analyzer for transcript documents"""
    
    def __init__(
        self,
        basic_extractor: InformationExtractorInterface,
        advanced_extractor: InformationExtractorInterface,
        confidence_calculator: ConfidenceCalculatorInterface
    ):
        super().__init__(
            DocumentType.TRANSCRIPT,
            basic_extractor,
            advanced_extractor,
            confidence_calculator
        )
    
    def _generate_insights(self, info: Dict[str, Any]) -> List[AnalysisInsight]:
        """Generate insights from transcript information"""
        insights = []
        
        # Add insights based on academic performance
        if "academic_performance" in info:
            insights.append(
                AnalysisInsight(
                    category="performance",
                    content=info["academic_performance"],
                    confidence=0.8,
                    importance=1.0
                )
            )
        
        # Add insights based on course patterns
        if "course_patterns" in info:
            insights.append(
                AnalysisInsight(
                    category="courses",
                    content=info["course_patterns"],
                    confidence=0.7,
                    importance=0.8
                )
            )
        
        # Add strengths as insights
        if "strengths" in info and isinstance(info["strengths"], list):
            for i, strength in enumerate(info["strengths"]):
                insights.append(
                    AnalysisInsight(
                        category="strength",
                        content=strength,
                        confidence=0.75,
                        importance=0.9 - (i * 0.1)  # Decreasing importance
                    )
                )
        
        # Add weaknesses as insights
        if "weaknesses" in info and isinstance(info["weaknesses"], list):
            for i, weakness in enumerate(info["weaknesses"]):
                insights.append(
                    AnalysisInsight(
                        category="improvement",
                        content=weakness,
                        confidence=0.7,
                        importance=0.8 - (i * 0.1)  # Decreasing importance
                    )
                )
        
        # Add trends as insights
        if "trends" in info:
            insights.append(
                AnalysisInsight(
                    category="trend",
                    content=info["trends"],
                    confidence=0.6,
                    importance=0.7
                )
            )
        
        return insights

class EssayAnalyzer(BaseDocumentAnalyzer):
    """Specialized analyzer for essay documents"""
    
    def __init__(
        self,
        basic_extractor: InformationExtractorInterface,
        advanced_extractor: InformationExtractorInterface,
        confidence_calculator: ConfidenceCalculatorInterface
    ):
        super().__init__(
            DocumentType.ESSAY,
            basic_extractor,
            advanced_extractor,
            confidence_calculator
        )
    
    def _generate_insights(self, info: Dict[str, Any]) -> List[AnalysisInsight]:
        """Generate insights from essay information"""
        insights = []
        
        # Add insights based on themes
        if "themes" in info and isinstance(info["themes"], list):
            for i, theme in enumerate(info["themes"]):
                insights.append(
                    AnalysisInsight(
                        category="theme",
                        content=theme,
                        confidence=0.8,
                        importance=0.9 - (i * 0.1)  # Decreasing importance
                    )
                )
        
        # Add writing style insight
        if "writing_style" in info:
            insights.append(
                AnalysisInsight(
                    category="style",
                    content=info["writing_style"],
                    confidence=0.75,
                    importance=0.8
                )
            )
        
        # Add structure quality insight
        if "structure_quality" in info:
            quality = float(info["structure_quality"])
            assessment = ""
            if quality >= 8:
                assessment = "Excellent essay structure with clear organization."
            elif quality >= 6:
                assessment = "Good essay structure, but could be improved in some areas."
            elif quality >= 4:
                assessment = "Adequate essay structure, but significant improvements needed."
            else:
                assessment = "Poor essay structure requiring major revisions."
            
            insights.append(
                AnalysisInsight(
                    category="structure",
                    content=assessment,
                    confidence=0.7,
                    importance=0.85
                )
            )
        
        # Add argument quality insight
        if "argument_quality" in info:
            quality = float(info["argument_quality"])
            assessment = ""
            if quality >= 8:
                assessment = "Strong, compelling arguments with good supporting evidence."
            elif quality >= 6:
                assessment = "Decent arguments that could benefit from more supporting evidence."
            elif quality >= 4:
                assessment = "Arguments present but lack depth and supporting evidence."
            else:
                assessment = "Weak arguments that need substantial improvement."
            
            insights.append(
                AnalysisInsight(
                    category="argumentation",
                    content=assessment,
                    confidence=0.7,
                    importance=0.9
                )
            )
        
        # Add vocabulary assessment insight
        if "vocabulary_assessment" in info:
            insights.append(
                AnalysisInsight(
                    category="vocabulary",
                    content=info["vocabulary_assessment"],
                    confidence=0.65,
                    importance=0.7
                )
            )
        
        # Add tone insight
        if "tone" in info:
            insights.append(
                AnalysisInsight(
                    category="tone",
                    content=f"The essay's tone is {info['tone']}.",
                    confidence=0.6,
                    importance=0.6
                )
            )
        
        return insights

class ResumeAnalyzer(BaseDocumentAnalyzer):
    """Specialized analyzer for resume documents"""
    
    def __init__(
        self,
        basic_extractor: InformationExtractorInterface,
        advanced_extractor: InformationExtractorInterface,
        confidence_calculator: ConfidenceCalculatorInterface
    ):
        super().__init__(
            DocumentType.RESUME,
            basic_extractor,
            advanced_extractor,
            confidence_calculator
        )
    
    def _generate_insights(self, info: Dict[str, Any]) -> List[AnalysisInsight]:
        """Generate insights from resume information"""
        insights = []
        
        # Add insights based on key achievements
        if "key_achievements" in info and isinstance(info["key_achievements"], list):
            for i, achievement in enumerate(info["key_achievements"]):
                if i < 3:  # Limit to top 3 achievements
                    insights.append(
                        AnalysisInsight(
                            category="achievement",
                            content=achievement,
                            confidence=0.8,
                            importance=0.9 - (i * 0.1)  # Decreasing importance
                        )
                    )
        
        # Add skills assessment insight
        if "skills_assessment" in info:
            insights.append(
                AnalysisInsight(
                    category="skills",
                    content=info["skills_assessment"],
                    confidence=0.75,
                    importance=0.85
                )
            )
        
        # Add career progression insight
        if "career_progression" in info:
            insights.append(
                AnalysisInsight(
                    category="career",
                    content=info["career_progression"],
                    confidence=0.7,
                    importance=0.8
                )
            )
        
        # Add improvement areas as insights
        if "improvement_areas" in info and isinstance(info["improvement_areas"], list):
            for i, area in enumerate(info["improvement_areas"]):
                if i < 3:  # Limit to top 3 improvement areas
                    insights.append(
                        AnalysisInsight(
                            category="improvement",
                            content=area,
                            confidence=0.65,
                            importance=0.7 - (i * 0.1)  # Decreasing importance
                        )
                    )
        
        # Add experience level insight
        if "experience_level" in info:
            insights.append(
                AnalysisInsight(
                    category="experience",
                    content=f"Experience level: {info['experience_level']}",
                    confidence=0.75,
                    importance=0.8
                )
            )
        
        # Add strengths as insights
        if "strengths" in info and isinstance(info["strengths"], list):
            for i, strength in enumerate(info["strengths"]):
                if i < 3:  # Limit to top 3 strengths
                    insights.append(
                        AnalysisInsight(
                            category="strength",
                            content=strength,
                            confidence=0.7,
                            importance=0.75 - (i * 0.1)  # Decreasing importance
                        )
                    )
        
        return insights
        
class GenericDocumentAnalyzer(BaseDocumentAnalyzer):
    """Fallback analyzer for general documents"""
    
    def __init__(
        self,
        basic_extractor: InformationExtractorInterface,
        advanced_extractor: InformationExtractorInterface,
        confidence_calculator: ConfidenceCalculatorInterface,
        document_type: DocumentType = DocumentType.OTHER
    ):
        super().__init__(
            document_type,
            basic_extractor,
            advanced_extractor,
            confidence_calculator
        )
    
    def _generate_insights(self, info: Dict[str, Any]) -> List[AnalysisInsight]:
        """Generate insights from generic document information"""
        insights = []
        
        # Add document type assessment
        if "likely_document_type" in info:
            insights.append(
                AnalysisInsight(
                    category="document_type",
                    content=f"This appears to be a {info['likely_document_type']}.",
                    confidence=0.6,
                    importance=0.7
                )
            )
        
        # Add purpose insight
        if "purpose" in info:
            insights.append(
                AnalysisInsight(
                    category="purpose",
                    content=info["purpose"],
                    confidence=0.65,
                    importance=0.8
                )
            )
        
        # Add content summary insight
        if "content_summary" in info:
            insights.append(
                AnalysisInsight(
                    category="summary",
                    content=info["content_summary"],
                    confidence=0.7,
                    importance=0.9
                )
            )
        
        # Add notable elements as insights
        if "notable_elements" in info and isinstance(info["notable_elements"], list):
            for i, element in enumerate(info["notable_elements"]):
                insights.append(
                    AnalysisInsight(
                        category="notable",
                        content=element,
                        confidence=0.6,
                        importance=0.6 - (i * 0.1)  # Decreasing importance
                    )
                )
        
        return insights 