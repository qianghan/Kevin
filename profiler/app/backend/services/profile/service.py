"""
Profile Service implementation.

This module provides the main implementation of the ProfileService,
following the SOLID principles. It uses dependency injection to receive
its collaborating components.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from ...utils.errors import ResourceNotFoundError, ValidationError, ServiceError
from ...utils.logging import get_logger
from ...services.interfaces import IProfileService
from .interfaces import (
    ProfileRepositoryInterface,
    ProfileValidatorInterface,
    ProfileStateCalculatorInterface,
    ProfileNotifierInterface
)
from .models import Profile, ProfileState, ProfileSectionData, ProfileConfig

logger = get_logger(__name__)


class ProfileService(IProfileService):
    """
    Profile service implementation.
    
    This service manages user profiles, including creation, updates, and state management.
    It delegates specific responsibilities to injected components.
    """
    
    def __init__(
        self,
        repository: ProfileRepositoryInterface,
        validator: ProfileValidatorInterface,
        state_calculator: ProfileStateCalculatorInterface,
        notifier: ProfileNotifierInterface
    ):
        """
        Initialize the service with required components.
        
        Args:
            repository: Profile repository for storage operations
            validator: Validator for profile data
            state_calculator: Calculator for profile state
            notifier: Notifier for profile updates
        """
        self.repository = repository
        self.validator = validator
        self.state_calculator = state_calculator
        self.notifier = notifier
        logger.info("Initialized ProfileService")
    
    async def initialize(self) -> None:
        """Initialize the service and its components."""
        await self.repository.initialize()
        logger.info("Initialized ProfileService components")
    
    async def shutdown(self) -> None:
        """Shutdown the service and release resources."""
        await self.repository.shutdown()
        logger.info("Shutdown ProfileService components")
    
    async def create_profile(self, user_id: str, initial_data: Optional[Dict[str, Any]] = None) -> ProfileState:
        """
        Create a new profile for a user.
        
        Args:
            user_id: The ID of the user
            initial_data: Optional initial data for the profile
            
        Returns:
            New ProfileState object
            
        Raises:
            ValidationError: If the user ID is invalid
            ServiceError: If the profile cannot be created
        """
        try:
            # Validate user ID
            if not user_id:
                raise ValidationError("User ID is required")
            
            # Create profile config
            config = self._create_default_config()
            
            # Get first section
            first_section = config.sections[0] if config.sections else "personal"
            
            # Create profile
            profile = Profile(
                profile_id=str(uuid.uuid4()),
                user_id=user_id,
                current_section=first_section,
                config=config
            )
            
            # Create initial sections
            for section_id in config.sections:
                profile.sections[section_id] = ProfileSectionData(
                    section_id=section_id,
                    title=self._get_section_title(section_id)
                )
            
            # Add initial data if provided
            if initial_data:
                for section_id, section_data in initial_data.items():
                    if section_id in profile.sections:
                        profile.sections[section_id].data.update(section_data)
                        
                        # Validate section data
                        errors = self.validator.validate_section_data(
                            section_id=section_id,
                            section_data=profile.sections[section_id].data,
                            validation_rules=config.validation_rules
                        )
                        
                        if errors:
                            raise ValidationError(f"Invalid data for section {section_id}: {', '.join(errors)}")
            
            # Save profile
            saved_profile = await self.repository.save_profile(profile)
            
            # Calculate state
            state = self.state_calculator.calculate_state(saved_profile)
            
            logger.info(f"Created profile {profile.profile_id} for user {user_id}")
            return state
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to create profile for user {user_id}: {str(e)}")
            raise ServiceError(f"Failed to create profile: {str(e)}")
    
    async def update_profile(self, profile_id: str, updates: Dict[str, Any]) -> ProfileState:
        """
        Update an existing profile.
        
        Args:
            profile_id: The ID of the profile to update
            updates: The updates to apply to the profile
            
        Returns:
            Updated ProfileState object
            
        Raises:
            ResourceNotFoundError: If the profile does not exist
            ValidationError: If the updates are invalid
            ServiceError: If the profile cannot be updated
        """
        try:
            # Get existing profile
            profile = await self.repository.get_profile(profile_id)
            
            # Check for section data updates
            section_updates = updates.get("sections", {})
            for section_id, section_data in section_updates.items():
                # Check if section exists
                if section_id not in profile.sections:
                    # Create section if it doesn't exist
                    profile.sections[section_id] = ProfileSectionData(
                        section_id=section_id,
                        title=self._get_section_title(section_id)
                    )
                
                # Update section data
                profile.sections[section_id].data.update(section_data)
                
                # Update completion status if specified
                if "completed" in section_data:
                    profile.sections[section_id].completed = bool(section_data["completed"])
                
                # Validate section data
                errors = self.validator.validate_section_data(
                    section_id=section_id,
                    section_data=profile.sections[section_id].data,
                    validation_rules=profile.config.validation_rules
                )
                
                if errors:
                    raise ValidationError(f"Invalid data for section {section_id}: {', '.join(errors)}")
            
            # Update current section if specified
            if "current_section" in updates:
                target_section = updates["current_section"]
                
                # Validate section transition
                errors = self.validator.validate_section_transition(
                    profile=profile,
                    current_section=profile.current_section,
                    target_section=target_section
                )
                
                if errors:
                    raise ValidationError(f"Invalid section transition: {', '.join(errors)}")
                
                profile.current_section = target_section
            
            # Update metadata if specified
            if "metadata" in updates:
                profile.metadata.update(updates["metadata"])
            
            # Update status if specified
            if "status" in updates:
                profile.status = updates["status"]
            
            # Update last_updated timestamp
            profile.last_updated = datetime.utcnow().isoformat()
            
            # Save updated profile
            updated_profile = await self.repository.save_profile(profile)
            
            # Calculate state
            state = self.state_calculator.calculate_state(updated_profile)
            
            # Notify subscribers
            await self.notifier.notify_profile_updated(profile_id, state)
            
            logger.info(f"Updated profile {profile_id}")
            return state
            
        except (ResourceNotFoundError, ValidationError):
            # Re-raise these specific errors
            raise
        except Exception as e:
            logger.error(f"Failed to update profile {profile_id}: {str(e)}")
            raise ServiceError(f"Failed to update profile: {str(e)}")
    
    async def get_profile(self, profile_id: str) -> ProfileState:
        """
        Get a profile by ID.
        
        Args:
            profile_id: The ID of the profile to get
            
        Returns:
            ProfileState object
            
        Raises:
            ResourceNotFoundError: If the profile does not exist
            ServiceError: If the profile cannot be retrieved
        """
        try:
            # Get profile
            profile = await self.repository.get_profile(profile_id)
            
            # Calculate state
            state = self.state_calculator.calculate_state(profile)
            
            logger.info(f"Retrieved profile {profile_id}")
            return state
            
        except ResourceNotFoundError:
            # Re-raise not found error
            raise
        except Exception as e:
            logger.error(f"Failed to get profile {profile_id}: {str(e)}")
            raise ServiceError(f"Failed to get profile: {str(e)}")
    
    async def delete_profile(self, profile_id: str) -> None:
        """
        Delete a profile by ID.
        
        Args:
            profile_id: The ID of the profile to delete
            
        Raises:
            ResourceNotFoundError: If the profile does not exist
            ServiceError: If the profile cannot be deleted
        """
        try:
            # Delete profile
            await self.repository.delete_profile(profile_id)
            
            # Notify subscribers
            await self.notifier.notify_profile_deleted(profile_id)
            
            logger.info(f"Deleted profile {profile_id}")
            
        except ResourceNotFoundError:
            # Re-raise not found error
            raise
        except Exception as e:
            logger.error(f"Failed to delete profile {profile_id}: {str(e)}")
            raise ServiceError(f"Failed to delete profile: {str(e)}")
    
    def _create_default_config(self) -> ProfileConfig:
        """
        Create default profile configuration.
        
        Returns:
            Default ProfileConfig
        """
        return ProfileConfig(
            sections=[
                "personal",
                "education",
                "experience",
                "skills",
                "projects",
                "achievements"
            ],
            required_sections=["personal", "education"],
            section_dependencies={
                "projects": ["education", "skills"],
                "achievements": ["education", "experience"]
            },
            validation_rules={
                "personal": {
                    "required_fields": ["name", "email"],
                    "field_types": {
                        "name": "string",
                        "email": "string",
                        "phone": "string",
                        "address": "string"
                    }
                },
                "education": {
                    "required_fields": ["institutions"]
                },
                "experience": {
                    "required_fields": ["positions"]
                }
            }
        )
    
    def _get_section_title(self, section_id: str) -> str:
        """
        Get display title for a section ID.
        
        Args:
            section_id: The section ID
            
        Returns:
            Display title for the section
        """
        titles = {
            "personal": "Personal Information",
            "education": "Education",
            "experience": "Work Experience",
            "skills": "Skills",
            "projects": "Projects",
            "achievements": "Achievements"
        }
        
        return titles.get(section_id, section_id.capitalize()) 