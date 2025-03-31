from typing import Dict, Any, List, Optional, TypedDict
from enum import Enum
from datetime import datetime

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

class AcademicInfo(TypedDict):
    """Type for academic information"""
    grades: List[Dict[str, Any]]
    courses: List[Dict[str, Any]]
    achievements: List[Dict[str, Any]]
    status: ProfileStatus
    recommendations: Optional[List[Dict[str, Any]]]
    quality_score: Optional[float]

class ExtracurricularInfo(TypedDict):
    """Type for extracurricular information"""
    activities: List[Dict[str, Any]]
    leadership: List[Dict[str, Any]]
    service: List[Dict[str, Any]]
    status: ProfileStatus
    recommendations: Optional[List[Dict[str, Any]]]
    quality_score: Optional[float]

class PersonalInfo(TypedDict):
    """Type for personal information"""
    background: Dict[str, Any]
    goals: Dict[str, Any]
    interests: List[str]
    status: ProfileStatus
    recommendations: Optional[List[Dict[str, Any]]]
    quality_score: Optional[float]

class EssayInfo(TypedDict):
    """Type for essay information"""
    topics: List[Dict[str, Any]]
    content: Dict[str, Any]
    style: Dict[str, Any]
    status: ProfileStatus
    recommendations: Optional[List[Dict[str, Any]]]
    quality_score: Optional[float]

class ProfileState(TypedDict):
    """Type for the complete profile state"""
    user_id: str
    current_section: ProfileSection
    current_questions: List[str]
    current_answer: Optional[str]
    sections: Dict[ProfileSection, Dict[str, Any]]
    context: Dict[str, Any]
    review_requests: List[Dict[str, Any]]
    interaction_count: int
    last_updated: str
    status: str
    error: Optional[str]
    summary: Optional[Dict[str, Any]]

def create_initial_state(user_id: str) -> ProfileState:
    """Create initial profile state"""
    return {
        "user_id": user_id,
        "current_section": ProfileSection.ACADEMIC,
        "current_questions": [],
        "current_answer": None,
        "sections": {
            ProfileSection.ACADEMIC: {
                "grades": [],
                "courses": [],
                "achievements": [],
                "status": ProfileStatus.NOT_STARTED,
                "recommendations": None,
                "quality_score": None
            },
            ProfileSection.EXTRACURRICULAR: {
                "activities": [],
                "leadership": [],
                "service": [],
                "status": ProfileStatus.NOT_STARTED,
                "recommendations": None,
                "quality_score": None
            },
            ProfileSection.PERSONAL: {
                "background": {},
                "goals": {},
                "interests": [],
                "status": ProfileStatus.NOT_STARTED,
                "recommendations": None,
                "quality_score": None
            },
            ProfileSection.ESSAYS: {
                "topics": [],
                "content": {},
                "style": {},
                "status": ProfileStatus.NOT_STARTED,
                "recommendations": None,
                "quality_score": None
            }
        },
        "context": {},
        "review_requests": [],
        "interaction_count": 0,
        "last_updated": datetime.utcnow().isoformat(),
        "status": "initialized",
        "error": None,
        "summary": None
    } 