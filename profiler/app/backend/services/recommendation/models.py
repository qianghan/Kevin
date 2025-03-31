"""
Data models for the recommendation service.

This module defines Pydantic models for recommendations and profile summaries,
ensuring proper validation and documentation.
"""

from typing import List
from pydantic import BaseModel, Field

class Recommendation(BaseModel):
    """
    Model for profile recommendations.
    
    Represents a specific recommendation for improving a user's profile,
    including details on what to improve and how to do it.
    """
    category: str = Field(..., description="Category of recommendation (e.g., 'academic', 'extracurricular')")
    title: str = Field(..., description="Title summarizing the recommendation")
    description: str = Field(..., description="Detailed explanation of the recommendation")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1-5, where 5 is highest)")
    action_items: List[str] = Field(..., description="Specific actionable steps to implement the recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0) indicating certainty")
    
    class Config:
        schema_extra = {
            "example": {
                "category": "academic",
                "title": "Highlight Research Experience",
                "description": "Your profile lacks details about your research experience, which is crucial for academic applications.",
                "priority": 4,
                "action_items": [
                    "Add details about your research methodology",
                    "Mention any publications or presentations",
                    "Describe the impact of your research"
                ],
                "confidence": 0.85
            }
        }

class ProfileSummary(BaseModel):
    """
    Model for profile summaries.
    
    Provides an overview of a user's profile, highlighting strengths,
    areas for improvement, and unique selling points.
    """
    strengths: List[str] = Field(..., description="Key strengths identified in the profile")
    areas_for_improvement: List[str] = Field(..., description="Areas that need improvement")
    unique_selling_points: List[str] = Field(..., description="Unique aspects that make the profile stand out")
    overall_quality: float = Field(..., ge=0.0, le=1.0, description="Overall profile quality score (0.0-1.0)")
    last_updated: str = Field(..., description="ISO format timestamp of when the summary was last updated")
    
    class Config:
        schema_extra = {
            "example": {
                "strengths": [
                    "Strong academic record with 3.8 GPA",
                    "Leadership experience as club president",
                    "Relevant internship experience"
                ],
                "areas_for_improvement": [
                    "Limited community service involvement",
                    "Essays need more personal reflection",
                    "Extracurricular activities lack diversity"
                ],
                "unique_selling_points": [
                    "International experience studying abroad",
                    "Published research in peer-reviewed journal",
                    "Founded a student organization"
                ],
                "overall_quality": 0.78,
                "last_updated": "2023-03-15T14:30:45Z"
            }
        } 