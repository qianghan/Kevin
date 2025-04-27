"""
API data models for the KAI UI application.

This module defines TypeScript-like interfaces for all API entities using Python type hints.
These models serve as the shared contract between frontend and backend, and are also used
for type checking and documentation.
"""

from typing import Dict, List, Optional, Literal, Union, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    """Enumeration of possible user roles in the system."""
    STUDENT = "student"
    PARENT = "parent" 
    COUNSELOR = "counselor"
    ADMIN = "admin"


class NotificationPreference(BaseModel):
    """User preferences for different types of notifications."""
    email: bool = Field(True, description="Whether to receive email notifications")
    push: bool = Field(True, description="Whether to receive push notifications")
    in_app: bool = Field(True, description="Whether to receive in-app notifications")


class NotificationPreferences(BaseModel):
    """All notification preferences for a user."""
    chat: NotificationPreference = Field(
        default_factory=NotificationPreference,
        description="Notification preferences for chat messages"
    )
    system: NotificationPreference = Field(
        default_factory=NotificationPreference,
        description="Notification preferences for system messages"
    )
    updates: NotificationPreference = Field(
        default_factory=NotificationPreference,
        description="Notification preferences for application updates"
    )


class UserPreferences(BaseModel):
    """User preferences for the application."""
    theme: Literal["light", "dark", "system"] = Field(
        "system", description="User's preferred theme"
    )
    language: Literal["en", "zh", "fr"] = Field(
        "en", description="User's preferred language"
    )
    notifications: NotificationPreferences = Field(
        default_factory=NotificationPreferences,
        description="User's notification preferences"
    )


class User(BaseModel):
    """User entity representing a user in the system."""
    id: str = Field(description="Unique identifier for the user")
    firstName: str = Field(description="User's first name")
    lastName: str = Field(description="User's last name")
    email: EmailStr = Field(description="User's email address")
    role: UserRole = Field(description="User's role in the system")
    preferences: UserPreferences = Field(
        default_factory=UserPreferences, 
        description="User's preferences"
    )
    createdAt: datetime = Field(description="When the user was created")
    updatedAt: datetime = Field(description="When the user was last updated")


class ChatMessage(BaseModel):
    """A message in a chat conversation."""
    id: str = Field(description="Unique identifier for the message")
    conversationId: str = Field(description="ID of the conversation this message belongs to")
    content: str = Field(description="Content of the message")
    role: Literal["user", "assistant"] = Field(description="Role of the message sender")
    createdAt: datetime = Field(description="When the message was created")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the message"
    )


class ChatConversation(BaseModel):
    """A chat conversation between a user and the AI assistant."""
    id: str = Field(description="Unique identifier for the conversation")
    userId: str = Field(description="ID of the user who owns this conversation")
    title: str = Field(description="Title of the conversation")
    messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Messages in the conversation"
    )
    createdAt: datetime = Field(description="When the conversation was created")
    updatedAt: datetime = Field(description="When the conversation was last updated")


class Document(BaseModel):
    """A document stored in the system."""
    id: str = Field(description="Unique identifier for the document")
    userId: str = Field(description="ID of the user who owns this document")
    title: str = Field(description="Title of the document")
    content: str = Field(description="Content of the document")
    mimeType: str = Field(description="MIME type of the document")
    tags: List[str] = Field(
        default_factory=list,
        description="Tags associated with the document"
    )
    createdAt: datetime = Field(description="When the document was created")
    updatedAt: datetime = Field(description="When the document was last updated")


class ProfileSection(str, Enum):
    """Enumeration of possible profile sections."""
    EDUCATION = "education"
    EXPERIENCE = "experience"
    SKILLS = "skills"
    ACHIEVEMENTS = "achievements"
    INTERESTS = "interests"


class ProfileItem(BaseModel):
    """An item in a user's profile."""
    id: str = Field(description="Unique identifier for the profile item")
    userId: str = Field(description="ID of the user who owns this profile item")
    section: ProfileSection = Field(description="Section this item belongs to")
    title: str = Field(description="Title of the profile item")
    description: str = Field(description="Description of the profile item")
    startDate: Optional[datetime] = Field(None, description="Start date, if applicable")
    endDate: Optional[datetime] = Field(None, description="End date, if applicable")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the profile item"
    )
    createdAt: datetime = Field(description="When the profile item was created")
    updatedAt: datetime = Field(description="When the profile item was last updated")


class Profile(BaseModel):
    """A user's profile containing all profile items."""
    userId: str = Field(description="ID of the user who owns this profile")
    items: Dict[ProfileSection, List[ProfileItem]] = Field(
        default_factory=dict,
        description="Profile items organized by section"
    )
    lastUpdated: datetime = Field(description="When the profile was last updated")


class ErrorCode(str, Enum):
    """Enumeration of possible error codes."""
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    SERVICE_UNAVAILABLE = "service_unavailable"


class ErrorResponse(BaseModel):
    """Error response from the API."""
    code: ErrorCode = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional details about the error"
    )


class PaginationParams(BaseModel):
    """Parameters for paginated requests."""
    page: int = Field(1, description="Page number, starting from 1")
    limit: int = Field(20, description="Number of items per page")


class SortDirection(str, Enum):
    """Sort direction for sorted requests."""
    ASC = "asc"
    DESC = "desc"


class SortParams(BaseModel):
    """Parameters for sorted requests."""
    field: str = Field(description="Field to sort by")
    direction: SortDirection = Field(
        SortDirection.ASC, description="Sort direction"
    )


class PaginatedResponse(BaseModel):
    """Base class for paginated API responses."""
    items: List[Any] = Field(description="Items in the current page")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    limit: int = Field(description="Number of items per page")
    pages: int = Field(description="Total number of pages") 