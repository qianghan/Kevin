"""
Models for Profile Service.

This module defines data models used by the profile service.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ProfileSectionData(BaseModel):
    """Data for a section of the profile."""
    
    section_id: str = Field(..., description="Unique identifier for the section")
    title: str = Field(..., description="Display title for the section")
    data: Dict[str, Any] = Field(default_factory=dict, description="Section data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    completed: bool = Field(default=False, description="Whether the section is completed")
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), 
                            description="Last update timestamp")


class ProfileConfig(BaseModel):
    """Configuration for a profile."""
    
    sections: List[str] = Field(..., description="List of section IDs in order")
    required_sections: List[str] = Field(..., description="List of required section IDs")
    section_dependencies: Dict[str, List[str]] = Field(
        default_factory=dict, 
        description="Dependencies between sections (key depends on values)"
    )
    validation_rules: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Validation rules for each section"
    )


class Profile(BaseModel):
    """User profile data model."""
    
    profile_id: str = Field(..., description="Unique identifier for the profile")
    user_id: str = Field(..., description="User ID associated with this profile")
    current_section: str = Field(..., description="Current active section")
    sections: Dict[str, ProfileSectionData] = Field(
        default_factory=dict, 
        description="Data for each profile section"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional profile metadata")
    config: ProfileConfig = Field(..., description="Profile configuration")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), 
                          description="Creation timestamp")
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), 
                            description="Last update timestamp")
    status: str = Field(default="active", description="Profile status")


class ProfileState(BaseModel):
    """The current state of a profile build session."""
    
    profile_id: str = Field(..., description="Unique identifier for the profile")
    user_id: str = Field(..., description="User ID associated with this profile")
    current_section: str = Field(..., description="Current active section")
    sections_completed: List[str] = Field(..., description="List of completed section IDs")
    sections_remaining: List[str] = Field(..., description="List of remaining section IDs")
    profile_data: Dict[str, Any] = Field(..., description="Aggregated profile data")
    last_updated: str = Field(..., description="Last update timestamp")
    status: str = Field(..., description="Profile status") 