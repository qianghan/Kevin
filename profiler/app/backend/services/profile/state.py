"""
State calculator implementation for the Profile Service.

This module provides concrete implementations of the ProfileStateCalculatorInterface.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from ...utils.logging import get_logger
from .interfaces import ProfileStateCalculatorInterface
from .models import Profile, ProfileState

logger = get_logger(__name__)


class DefaultProfileStateCalculator(ProfileStateCalculatorInterface):
    """Default implementation of profile state calculator."""
    
    def calculate_state(self, profile: Profile) -> ProfileState:
        """
        Calculate the current state of a profile.
        
        Args:
            profile: The profile
            
        Returns:
            Current profile state
        """
        # Get all section IDs
        all_sections = profile.config.sections
        
        # Determine completed sections
        sections_completed = []
        for section_id, section_data in profile.sections.items():
            if section_data.completed:
                sections_completed.append(section_id)
        
        # Determine remaining sections
        sections_remaining = [s for s in all_sections if s not in sections_completed]
        
        # Aggregate profile data
        profile_data = {}
        for section_id, section_data in profile.sections.items():
            profile_data.update(section_data.data)
        
        # Create profile state
        profile_state = ProfileState(
            profile_id=profile.profile_id,
            user_id=profile.user_id,
            current_section=profile.current_section,
            sections_completed=sections_completed,
            sections_remaining=sections_remaining,
            profile_data=profile_data,
            last_updated=profile.last_updated,
            status=profile.status
        )
        
        logger.info(f"Calculated state for profile {profile.profile_id}: "
                  f"{len(sections_completed)}/{len(all_sections)} sections completed")
        
        return profile_state
    
    def get_next_section(self, profile: Profile) -> Optional[str]:
        """
        Get the next recommended section to complete.
        
        Args:
            profile: The profile
            
        Returns:
            Next section ID or None if all sections are completed
        """
        # Get all section IDs in order
        all_sections = profile.config.sections
        
        # Get completed sections
        completed_sections = set()
        for section_id, section_data in profile.sections.items():
            if section_data.completed:
                completed_sections.add(section_id)
        
        # Get section dependencies
        dependencies = profile.config.section_dependencies
        
        # Find first incomplete section that has all dependencies satisfied
        for section_id in all_sections:
            # Skip if already completed
            if section_id in completed_sections:
                continue
            
            # Check if all dependencies are satisfied
            if section_id in dependencies:
                dependent_sections = dependencies[section_id]
                if not all(dep in completed_sections for dep in dependent_sections):
                    # Dependencies not satisfied, skip this section
                    continue
            
            # Found eligible section
            logger.info(f"Next recommended section for profile {profile.profile_id}: {section_id}")
            return section_id
        
        # No more sections to complete
        logger.info(f"No more sections to complete for profile {profile.profile_id}")
        return None 