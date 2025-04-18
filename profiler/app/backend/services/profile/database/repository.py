"""
PostgreSQL repository implementation for Profile Service.

This module provides a concrete implementation of the ProfileRepositoryInterface using PostgreSQL.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from app.backend.utils.errors import ResourceNotFoundError, StorageError
from app.backend.utils.logging import get_logger
from ..interfaces import ProfileRepositoryInterface
from ..models import Profile, ProfileSectionData, ProfileConfig
from .connection import DatabaseManager
from .models import ProfileModel, ProfileSectionModel

logger = get_logger(__name__)


class PostgreSQLProfileRepository(ProfileRepositoryInterface):
    """Profile repository implementation using PostgreSQL."""
    
    def __init__(self, db_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the repository.
        
        Args:
            db_config: Optional database configuration dictionary
        """
        self.db_manager = DatabaseManager(db_config)
    
    async def initialize(self) -> None:
        """Initialize the repository, setting up database connection."""
        try:
            await self.db_manager.initialize()
            logger.info("Initialized PostgreSQLProfileRepository")
        except Exception as e:
            logger.error(f"Failed to initialize profile repository: {str(e)}")
            raise StorageError(f"Failed to initialize profile repository: {str(e)}")
    
    async def shutdown(self) -> None:
        """Shutdown the repository, closing database connection."""
        await self.db_manager.shutdown()
        logger.info("Shutdown PostgreSQLProfileRepository")
    
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
            
            async with self.db_manager.get_session() as session:
                async with session.begin():
                    # Check if profile exists
                    stmt = select(ProfileModel).where(ProfileModel.profile_id == profile.profile_id)
                    result = await session.execute(stmt)
                    profile_model = result.scalar_one_or_none()
                    
                    if profile_model:
                        # Update existing profile
                        profile_model.user_id = profile.user_id
                        profile_model.current_section = profile.current_section
                        profile_model.metadata = json.dumps(profile.metadata)
                        profile_model.config = json.dumps(profile.config.dict())
                        profile_model.status = profile.status
                        profile_model.last_updated = datetime.utcnow()
                        
                        # Delete existing sections (will be replaced)
                        await session.execute(
                            delete(ProfileSectionModel).where(
                                ProfileSectionModel.profile_id == profile.profile_id
                            )
                        )
                    else:
                        # Create new profile
                        profile_model = ProfileModel(
                            profile_id=profile.profile_id,
                            user_id=profile.user_id,
                            current_section=profile.current_section,
                            metadata=json.dumps(profile.metadata),
                            config=json.dumps(profile.config.dict()),
                            status=profile.status,
                            created_at=datetime.utcnow(),
                            last_updated=datetime.utcnow()
                        )
                        session.add(profile_model)
                    
                    # Create section models for all sections
                    for section_id, section_data in profile.sections.items():
                        section_model = ProfileSectionModel(
                            id=str(uuid.uuid4()),
                            profile_id=profile.profile_id,
                            section_id=section_id,
                            title=section_data.title,
                            data=json.dumps(section_data.data),
                            metadata=json.dumps(section_data.metadata),
                            completed=section_data.completed,
                            last_updated=datetime.utcnow()
                        )
                        session.add(section_model)
            
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
            async with self.db_manager.get_session() as session:
                # Get profile
                stmt = select(ProfileModel).where(ProfileModel.profile_id == profile_id)
                result = await session.execute(stmt)
                profile_model = result.scalar_one_or_none()
                
                if not profile_model:
                    raise ResourceNotFoundError(f"Profile {profile_id} not found")
                
                # Get sections
                stmt = select(ProfileSectionModel).where(ProfileSectionModel.profile_id == profile_id)
                sections_result = await session.execute(stmt)
                section_models = sections_result.scalars().all()
                
                # Build Profile object
                sections = {}
                for section in section_models:
                    sections[section.section_id] = ProfileSectionData(
                        section_id=section.section_id,
                        title=section.title,
                        data=json.loads(section.data) if section.data else {},
                        metadata=json.loads(section.metadata) if section.metadata else {},
                        completed=section.completed,
                        last_updated=section.last_updated.isoformat()
                    )
                
                profile = Profile(
                    profile_id=profile_model.profile_id,
                    user_id=profile_model.user_id,
                    current_section=profile_model.current_section,
                    sections=sections,
                    metadata=json.loads(profile_model.metadata) if profile_model.metadata else {},
                    config=ProfileConfig.parse_obj(json.loads(profile_model.config)),
                    created_at=profile_model.created_at.isoformat(),
                    last_updated=profile_model.last_updated.isoformat(),
                    status=profile_model.status
                )
                
                logger.info(f"Retrieved profile {profile_id}")
                return profile
                
        except ResourceNotFoundError:
            logger.error(f"Profile {profile_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve profile {profile_id}: {str(e)}")
            raise StorageError(f"Failed to retrieve profile: {str(e)}")
    
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
            async with self.db_manager.get_session() as session:
                async with session.begin():
                    # Check if profile exists
                    stmt = select(ProfileModel).where(ProfileModel.profile_id == profile_id)
                    result = await session.execute(stmt)
                    profile_model = result.scalar_one_or_none()
                    
                    if not profile_model:
                        raise ResourceNotFoundError(f"Profile {profile_id} not found")
                    
                    # Delete profile (cascade will delete sections)
                    await session.execute(
                        delete(ProfileModel).where(ProfileModel.profile_id == profile_id)
                    )
            
            logger.info(f"Deleted profile {profile_id}")
            
        except ResourceNotFoundError:
            logger.error(f"Profile {profile_id} not found")
            raise
        except Exception as e:
            logger.error(f"Failed to delete profile {profile_id}: {str(e)}")
            raise StorageError(f"Failed to delete profile: {str(e)}")
    
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
            async with self.db_manager.get_session() as session:
                # Build query
                stmt = select(ProfileModel)
                if user_id:
                    stmt = stmt.where(ProfileModel.user_id == user_id)
                
                # Execute query
                result = await session.execute(stmt)
                profile_models = result.scalars().all()
                
                # Build profile objects
                profiles = []
                for profile_model in profile_models:
                    # Get sections for this profile
                    sections_stmt = select(ProfileSectionModel).where(
                        ProfileSectionModel.profile_id == profile_model.profile_id
                    )
                    sections_result = await session.execute(sections_stmt)
                    section_models = sections_result.scalars().all()
                    
                    # Build sections dictionary
                    sections = {}
                    for section in section_models:
                        sections[section.section_id] = ProfileSectionData(
                            section_id=section.section_id,
                            title=section.title,
                            data=json.loads(section.data) if section.data else {},
                            metadata=json.loads(section.metadata) if section.metadata else {},
                            completed=section.completed,
                            last_updated=section.last_updated.isoformat()
                        )
                    
                    # Build profile
                    profile = Profile(
                        profile_id=profile_model.profile_id,
                        user_id=profile_model.user_id,
                        current_section=profile_model.current_section,
                        sections=sections,
                        metadata=json.loads(profile_model.metadata) if profile_model.metadata else {},
                        config=ProfileConfig.parse_obj(json.loads(profile_model.config)),
                        created_at=profile_model.created_at.isoformat(),
                        last_updated=profile_model.last_updated.isoformat(),
                        status=profile_model.status
                    )
                    
                    profiles.append(profile)
                
                logger.info(f"Listed {len(profiles)} profiles" + 
                         (f" for user {user_id}" if user_id else ""))
                return profiles
                
        except Exception as e:
            logger.error(f"Failed to list profiles: {str(e)}")
            raise StorageError(f"Failed to list profiles: {str(e)}") 