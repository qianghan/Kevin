"""
Data models for the QA service.

This module defines Pydantic models for questions, answers, conversations,
and other data structures used by the QA service.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class QuestionCategory(str, Enum):
    """Categories for profile questions."""
    ACADEMIC = "academic"
    EXTRACURRICULAR = "extracurricular"
    PERSONAL = "personal"
    ESSAYS = "essays"
    GOALS = "goals"
    GENERAL = "general"

class Question(BaseModel):
    """Model for a question about a profile."""
    question_id: str = Field(..., description="Unique identifier for the question")
    category: QuestionCategory = Field(..., description="Category the question belongs to")
    question_text: str = Field(..., description="The actual question text")
    expected_response_type: str = Field(..., description="Type of response expected (e.g., text, list, date)")
    required: bool = Field(default=True, description="Whether an answer is required for profile completion")
    follow_up_questions: List[str] = Field(default_factory=list, description="Potential follow-up questions")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for the question")
    
    class Config:
        schema_extra = {
            "example": {
                "question_id": "q123",
                "category": "academic",
                "question_text": "What was your GPA in high school?",
                "expected_response_type": "number",
                "required": True,
                "follow_up_questions": ["Were there any factors that affected your GPA?"],
                "context": {"prior_answer": "I attended Lincoln High School"}
            }
        }

class Answer(BaseModel):
    """Model for an answer to a question."""
    question_id: str = Field(..., description="ID of the question being answered")
    response: Any = Field(..., description="The actual response content")
    confidence: float = Field(
        default=1.0, 
        ge=0.0, 
        le=1.0, 
        description="Confidence score (0.0-1.0) indicating certainty"
    )
    quality_score: Optional[float] = Field(
        default=None, 
        ge=0.0, 
        le=1.0, 
        description="Quality score (0.0-1.0) for the answer"
    )
    needs_follow_up: bool = Field(
        default=False, 
        description="Whether this answer needs follow-up questions"
    )
    extracted_info: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Structured information extracted from the answer"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When the answer was provided"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "question_id": "q123",
                "response": "My GPA was 3.8",
                "confidence": 0.95,
                "quality_score": 0.85,
                "needs_follow_up": True,
                "extracted_info": {"gpa": 3.8},
                "timestamp": "2023-05-15T14:30:00"
            }
        }

class ConversationMessage(BaseModel):
    """Model for a message in a conversation."""
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When the message was sent"
    )

class Conversation(BaseModel):
    """Model for a QA conversation."""
    conversation_id: str = Field(..., description="Unique identifier for the conversation")
    user_id: str = Field(..., description="ID of the user")
    messages: List[ConversationMessage] = Field(default_factory=list, description="Messages in the conversation")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context for the conversation")
    questions_asked: List[str] = Field(default_factory=list, description="IDs of questions asked")
    answers_received: List[str] = Field(default_factory=list, description="IDs of answers received")
    start_time: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When the conversation started"
    )
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When the conversation was last updated"
    )
    active: bool = Field(default=True, description="Whether the conversation is active")

class ConversationSummary(BaseModel):
    """Model for a summary of a conversation."""
    conversation_id: str = Field(..., description="ID of the conversation")
    user_id: str = Field(..., description="ID of the user")
    message_count: int = Field(..., description="Number of messages in the conversation")
    categories_covered: List[QuestionCategory] = Field(default_factory=list, description="Categories covered")
    extracted_info: Dict[str, Any] = Field(default_factory=dict, description="Extracted information by category")
    completion_percentage: float = Field(
        default=0.0, 
        ge=0.0, 
        le=100.0, 
        description="Percentage of profile completion"
    )
    summary_text: str = Field(..., description="Text summary of the conversation")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        description="When the summary was generated"
    ) 