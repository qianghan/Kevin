"""
Recommendation data models.

This module defines the data models for recommendations.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union

from pydantic import BaseModel, Field, model_validator


class RecommendationCategory(str, Enum):
    """Categories of recommendations."""
    SKILL = "skill"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    DOCUMENT = "document"
    PROFILE = "profile"
    NETWORKING = "networking"
    CERTIFICATION = "certification"
    OTHER = "other"


class RecommendationStep(BaseModel):
    """A step to complete a recommendation."""
    title: str
    description: Optional[str] = None
    completed: bool = False


class Recommendation(BaseModel):
    """
    Model representing a recommendation.
    """
    id: Optional[str] = None
    user_id: str
    title: str
    description: str
    category: RecommendationCategory
    priority: Optional[float] = 0.5
    steps: List[Union[str, RecommendationStep]] = []
    detailed_steps: Optional[str] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "active"
    progress: float = 0.0
    related_entity_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    @model_validator(mode='after')
    def convert_step_strings(self):
        """Convert step strings to RecommendationStep objects if needed."""
        converted_steps = []
        for step in self.steps:
            if isinstance(step, str):
                converted_steps.append(RecommendationStep(title=step))
            else:
                converted_steps.append(step)
        self.steps = converted_steps
        return self
    
    class Config:
        """Configuration for the model."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        } 