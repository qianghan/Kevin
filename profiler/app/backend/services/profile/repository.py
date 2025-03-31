"""
Repository implementation for the Profile Service.

This module provides concrete implementations of the ProfileRepositoryInterface.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from ...utils.errors import ResourceNotFoundError, StorageError
from ...utils.logging import get_logger
from .interfaces import ProfileRepositoryInterface
from .models import Profile

logger = get_logger(__name__)


class JSONFileProfileRepository(ProfileRepositoryInterface):
    """Profile repository implementation using JSON files."""
    
    def __init__(self, storage_dir: str):
        """
        Initialize the repository.
        
        Args:
            storage_dir: Directory to store profile files
        """
        self.storage_dir = storage_dir
        self.profiles_cache: Dict[str, Profile] = {}
    
    async def initialize(self) -> None:
        """Initialize the repository, ensuring the storage directory exists."""
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
            logger.info(f"Initialized JSONFileProfileRepository at {self.storage_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize profile repository: {str(e)}")
            raise StorageError(f"Failed to initialize profile repository: {str(e)}")
    
    async def shutdown(self) -> None:
        """Shutdown the repository, clearing the cache."""
        self.profiles_cache.clear()
        logger.info("Shutdown JSONFileProfileRepository")
    
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
        try:
            # Update the last_updated timestamp
            profile.last_updated = datetime.utcnow().isoformat()
            
            # Generate profile_id if not exists
            if not profile.profile_id:
                profile.profile_id = str(uuid.uuid4())
            
            # Define the file path
            file_path = os.path.join(self.storage_dir, f"{profile.profile_id}.json")
            
            # Convert to JSON and save
            with open(file_path, 'w') as f:
                f.write(profile.json())
            
            # Update cache
            self.profiles_cache[profile.profile_id] = profile
            
            logger.info(f"Saved profile {profile.profile_id} for user {profile.user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to save profile: {str(e)}")
            raise StorageError(f"Failed to save profile: {str(e)}")
    
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
        try:
            # Check cache first
            if profile_id in self.profiles_cache:
                return self.profiles_cache[profile_id]
            
            # Define the file path
            file_path = os.path.join(self.storage_dir, f"{profile_id}.json")
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"Profile {profile_id} not found")
                raise ResourceNotFoundError(f"Profile {profile_id} not found")
            
            # Load from file
            with open(file_path, 'r') as f:
                profile_data = json.load(f)
            
            # Parse into Profile object
            profile = Profile.parse_obj(profile_data)
            
            # Update cache
            self.profiles_cache[profile_id] = profile
            
            logger.info(f"Retrieved profile {profile_id}")
            return profile
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get profile {profile_id}: {str(e)}")
            raise StorageError(f"Failed to get profile {profile_id}: {str(e)}")
    
    async def delete_profile(self, profile_id: str) -> None:
        """
        Delete a profile by ID.
        
        Args:
            profile_id: The ID of the profile to delete
            
        Raises:
            ResourceNotFoundError: If the profile does not exist
            StorageError: If the profile cannot be deleted
        """
        try:
            # Define the file path
            file_path = os.path.join(self.storage_dir, f"{profile_id}.json")
            
            # Check if file exists
            if not os.path.exists(file_path):
                logger.warning(f"Profile {profile_id} not found for deletion")
                raise ResourceNotFoundError(f"Profile {profile_id} not found")
            
            # Delete file
            os.remove(file_path)
            
            # Remove from cache
            if profile_id in self.profiles_cache:
                del self.profiles_cache[profile_id]
            
            logger.info(f"Deleted profile {profile_id}")
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete profile {profile_id}: {str(e)}")
            raise StorageError(f"Failed to delete profile {profile_id}: {str(e)}")
    
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
        try:
            profiles = []
            
            # List all JSON files in the directory
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.storage_dir, filename)
                    
                    try:
                        # Load profile from file
                        with open(file_path, 'r') as f:
                            profile_data = json.load(f)
                        
                        # Parse into Profile object
                        profile = Profile.parse_obj(profile_data)
                        
                        # Filter by user_id if provided
                        if user_id is None or profile.user_id == user_id:
                            profiles.append(profile)
                            # Update cache
                            self.profiles_cache[profile.profile_id] = profile
                    except Exception as e:
                        # Log error but continue processing other files
                        logger.warning(f"Error loading profile from {file_path}: {str(e)}")
            
            logger.info(f"Listed {len(profiles)} profiles" + 
                     (f" for user {user_id}" if user_id else ""))
            return profiles
            
        except Exception as e:
            logger.error(f"Failed to list profiles: {str(e)}")
            raise StorageError(f"Failed to list profiles: {str(e)}")


class DatabaseProfileRepository(ProfileRepositoryInterface):
    """Profile repository implementation using a database."""
    
    # This would be an alternative implementation using a database
    # For now, it's a placeholder for future implementation
    
    async def initialize(self) -> None:
        """Initialize database connection."""
        pass
    
    async def shutdown(self) -> None:
        """Close database connection."""
        pass
    
    async def save_profile(self, profile: Profile) -> Profile:
        """Save profile to database."""
        pass
    
    async def get_profile(self, profile_id: str) -> Profile:
        """Get profile from database."""
        pass
    
    async def delete_profile(self, profile_id: str) -> None:
        """Delete profile from database."""
        pass
    
    async def list_profiles(self, user_id: Optional[str] = None) -> List[Profile]:
        """List profiles from database."""
        pass 