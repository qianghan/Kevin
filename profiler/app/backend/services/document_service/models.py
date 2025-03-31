"""
Data models for the Document Service.

This module defines the Pydantic models and enums used throughout the document service.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class DocumentType(str, Enum):
    """Enum for supported document types"""
    TRANSCRIPT = "transcript"
    ESSAY = "essay"
    RESUME = "resume"
    LETTER = "letter"
    OTHER = "other"

class ExtractedInformation(BaseModel):
    """Base model for extracted information"""
    source_type: str = Field(..., description="Source of the extraction (regex, llm, etc)")
    extraction_time: datetime = Field(default_factory=datetime.utcnow, description="Time of extraction")

class TranscriptInfo(ExtractedInformation):
    """Model for transcript information"""
    grades: List[Dict[str, Any]] = Field(default_factory=list, description="List of grades")
    courses: List[Dict[str, Any]] = Field(default_factory=list, description="List of courses")
    terms: List[Dict[str, Any]] = Field(default_factory=list, description="List of academic terms")
    gpa: Optional[float] = Field(None, description="Grade point average")
    academic_standing: Optional[str] = Field(None, description="Academic standing")

class EssayInfo(ExtractedInformation):
    """Model for essay information"""
    word_count: int = Field(0, description="Word count")
    paragraph_count: int = Field(0, description="Paragraph count")
    key_phrases: List[str] = Field(default_factory=list, description="Key phrases")
    themes: List[str] = Field(default_factory=list, description="Main themes")
    tone: Optional[str] = Field(None, description="Writing tone")
    structure_quality: Optional[float] = Field(None, description="Structure quality score")

class ResumeInfo(ExtractedInformation):
    """Model for resume information"""
    sections: List[str] = Field(default_factory=list, description="Resume sections")
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    experiences: List[Dict[str, Any]] = Field(default_factory=list, description="Work experiences")
    education: List[Dict[str, Any]] = Field(default_factory=list, description="Education history")
    dates: List[str] = Field(default_factory=list, description="Dates mentioned")

class AnalysisInsight(BaseModel):
    """Model for analysis insights"""
    category: str = Field(..., description="Insight category")
    content: str = Field(..., description="Insight content")
    confidence: float = Field(..., description="Confidence score")
    importance: float = Field(1.0, description="Importance score")

class DocumentAnalysis(BaseModel):
    """Model for document analysis results"""
    content_type: DocumentType = Field(..., description="Type of document")
    extracted_info: Dict[str, Any] = Field(..., description="Extracted information")
    insights: List[AnalysisInsight] = Field(default_factory=list, description="Analysis insights")
    confidence: float = Field(..., description="Confidence score")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        validate_assignment = True 