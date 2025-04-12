from typing import Dict, Any, List, Optional, TypedDict
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class ProfileSection(str, Enum):
    """Enum for profile sections"""
    ACADEMIC = "academic"
    EXTRACURRICULAR = "extracurricular"
    PERSONAL = "personal"
    ESSAYS = "essays"

class ProfileStatus(str, Enum):
    """Enum for profile section status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    NEEDS_REVIEW = "needs_review"
    COMPLETED = "completed"

class SectionData(BaseModel):
    """Base model for section data"""
    status: ProfileStatus = Field(default=ProfileStatus.NOT_STARTED)
    recommendations: Optional[List[Dict[str, Any]]] = Field(default=None)
    quality_score: Optional[float] = Field(default=None)

class AcademicInfo(SectionData):
    """Model for academic information"""
    grades: List[Dict[str, Any]] = Field(default_factory=list)
    courses: List[Dict[str, Any]] = Field(default_factory=list)
    achievements: List[Dict[str, Any]] = Field(default_factory=list)

class ExtracurricularInfo(SectionData):
    """Model for extracurricular information"""
    activities: List[Dict[str, Any]] = Field(default_factory=list)
    leadership: List[Dict[str, Any]] = Field(default_factory=list)
    service: List[Dict[str, Any]] = Field(default_factory=list)

class PersonalInfo(SectionData):
    """Model for personal information"""
    background: Dict[str, Any] = Field(default_factory=dict)
    goals: Dict[str, Any] = Field(default_factory=dict)
    interests: List[str] = Field(default_factory=list)

class EssayInfo(SectionData):
    """Model for essay information"""
    topics: List[Dict[str, Any]] = Field(default_factory=list)
    content: Dict[str, Any] = Field(default_factory=dict)
    style: Dict[str, Any] = Field(default_factory=dict)

class ProfileState(BaseModel):
    """Model for the complete profile state"""
    user_id: str
    current_section: ProfileSection = Field(default=ProfileSection.ACADEMIC)
    current_questions: List[str] = Field(default_factory=list)
    current_answer: Optional[str] = Field(default=None)
    sections: Dict[ProfileSection, Dict[str, Any]] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    review_requests: List[Dict[str, Any]] = Field(default_factory=list)
    interaction_count: int = Field(default=0)
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = Field(default="initialized")
    error: Optional[str] = Field(default=None)
    summary: Optional[Dict[str, Any]] = Field(default=None)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            ProfileSection: lambda ps: ps.value,
            ProfileStatus: lambda ps: ps.value
        }

def create_initial_state(user_id: str) -> Dict[str, Any]:
    """Create initial profile state"""
    initial_state = {
        "user_id": user_id,
        "current_section": ProfileSection.ACADEMIC,
        "current_questions": [],
        "current_answer": None,
        "sections": {
            ProfileSection.ACADEMIC: AcademicInfo().model_dump(),
            ProfileSection.EXTRACURRICULAR: ExtracurricularInfo().model_dump(),
            ProfileSection.PERSONAL: PersonalInfo().model_dump(),
            ProfileSection.ESSAYS: EssayInfo().model_dump()
        },
        "context": {},
        "review_requests": [],
        "interaction_count": 0,
        "last_updated": datetime.utcnow().isoformat(),
        "status": "initialized",
        "error": None,
        "summary": None
    }
    
    # Validate and return
    return ProfileState(**initial_state).model_dump() 