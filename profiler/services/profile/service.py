"""
Profile service interfaces.

This module provides the interfaces for profile services.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IProfileService(ABC):
    """Interface for profile services."""
    
    @abstractmethod
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a user's profile.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            The user's profile, or None if not found
        """
        pass
    
    @abstractmethod
    async def get_similar_skill_profiles(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get profiles with similar skills to the given user.
        
        Args:
            user_id: The ID of the user
            limit: Maximum number of profiles to return
            
        Returns:
            A list of similar profiles
        """
        pass 