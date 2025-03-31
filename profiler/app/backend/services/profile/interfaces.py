"""
Interfaces for Profile Service.

This module defines interfaces used by the profile service,
following the SOLID principles, particularly Interface Segregation Principle.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Protocol

from .models import Profile, ProfileState, ProfileSectionData


class ProfileRepositoryInterface(ABC):
    """Interface for profile data storage operations."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the repository."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the repository and release resources."""
        pass
    
    @abstractmethod
    async def save_profile(self, profile: Profile) -> Profile:
        """
        Save a profile to the repository.
        
        Args:
            profile: The profile to save
            
        Returns:
            The saved profile
            
        Raises:
            StorageError: If the profile cannot be saved
        """
        pass
    
    @abstractmethod
    async def get_profile(self, profile_id: str) -> Profile:
        """
        Get a profile by ID.
        
        Args:
            profile_id: The ID of the profile to get
            
        Returns:
            The profile
            
        Raises:
            ResourceNotFoundError: If the profile does not exist
            StorageError: If the profile cannot be retrieved
        """
        pass
    
    @abstractmethod
    async def delete_profile(self, profile_id: str) -> None:
        """
        Delete a profile by ID.
        
        Args:
            profile_id: The ID of the profile to delete
            
        Raises:
            ResourceNotFoundError: If the profile does not exist
            StorageError: If the profile cannot be deleted
        """
        pass
    
    @abstractmethod
    async def list_profiles(self, user_id: Optional[str] = None) -> List[Profile]:
        """
        List profiles, optionally filtered by user ID.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            List of profiles
            
        Raises:
            StorageError: If the profiles cannot be listed
        """
        pass


class ProfileValidatorInterface(ABC):
    """Interface for profile data validation."""
    
    @abstractmethod
    def validate_section_data(self, section_id: str, section_data: Dict[str, Any], 
                            validation_rules: Dict[str, Any]) -> List[str]:
        """
        Validate section data against rules.
        
        Args:
            section_id: ID of the section being validated
            section_data: Data to validate
            validation_rules: Rules to validate against
            
        Returns:
            List of validation errors, empty if valid
        """
        pass
    
    @abstractmethod
    def validate_section_transition(self, profile: Profile, current_section: str, 
                                  target_section: str) -> List[str]:
        """
        Validate if a transition between sections is allowed.
        
        Args:
            profile: Current profile
            current_section: Current section ID
            target_section: Target section ID
            
        Returns:
            List of validation errors, empty if valid
        """
        pass


class ProfileStateCalculatorInterface(ABC):
    """Interface for profile state calculations."""
    
    @abstractmethod
    def calculate_state(self, profile: Profile) -> ProfileState:
        """
        Calculate the current state of a profile.
        
        Args:
            profile: The profile
            
        Returns:
            Current profile state
        """
        pass
    
    @abstractmethod
    def get_next_section(self, profile: Profile) -> Optional[str]:
        """
        Get the next recommended section to complete.
        
        Args:
            profile: The profile
            
        Returns:
            Next section ID or None if all sections are completed
        """
        pass


class ProfileNotifierInterface(Protocol):
    """Interface for profile update notifications."""
    
    async def notify_profile_updated(self, profile_id: str, profile_state: ProfileState) -> None:
        """
        Notify subscribers that a profile has been updated.
        
        Args:
            profile_id: ID of the updated profile
            profile_state: Current state of the profile
        """
        pass
    
    async def notify_profile_deleted(self, profile_id: str) -> None:
        """
        Notify subscribers that a profile has been deleted.
        
        Args:
            profile_id: ID of the deleted profile
        """
        pass


class ProfileFactoryInterface(Protocol):
    """Interface for creating profile-related components."""
    
    def get_repository(self) -> ProfileRepositoryInterface:
        """
        Get a profile repository instance.
        
        Returns:
            Profile repository instance
        """
        pass
    
    def get_validator(self) -> ProfileValidatorInterface:
        """
        Get a profile validator instance.
        
        Returns:
            Profile validator instance
        """
        pass
    
    def get_state_calculator(self) -> ProfileStateCalculatorInterface:
        """
        Get a profile state calculator instance.
        
        Returns:
            Profile state calculator instance
        """
        pass
    
    def get_notifier(self) -> ProfileNotifierInterface:
        """
        Get a profile notifier instance.
        
        Returns:
            Profile notifier instance
        """
        pass 