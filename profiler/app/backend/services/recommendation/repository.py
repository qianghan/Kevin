"""
Repository for storing and retrieving recommendations.

This module provides a repository for managing recommendation data,
using ChromaDB as the underlying storage mechanism.
"""

import json
from typing import Dict, List, Any, Optional
import chromadb
from chromadb.config import Settings
from datetime import datetime, timezone

from ...utils.logging import get_logger
from ...utils.errors import DatabaseError
from ...utils.config_manager import ConfigManager
from .models import Recommendation, ProfileSummary
from .database.repository import PostgreSQLRecommendationRepository

logger = get_logger(__name__)

class RecommendationRepository:
    """Repository for storing and retrieving recommendations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the repository with optional configuration.
        
        Args:
            config: Optional configuration dictionary. If not provided,
                   configuration will be loaded from the config manager.
        """
        self._config = config or ConfigManager().get_value(["database", "chromadb", "collections", "recommendations"], {})
        self._client = None
        self._collection = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        Initialize the repository, setting up ChromaDB client and collection.
        
        Raises:
            DatabaseError: If the database cannot be initialized.
        """
        try:
            logger.info("Initializing recommendation repository")
            
            # Configure ChromaDB
            db_path = self._config.get("path", "./data/chroma")
            
            # Create a persistent client
            self._client = chromadb.PersistentClient(
                path=db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create recommendations collection
            collection_name = self._config.get("name", "recommendations")
            try:
                self._collection = self._client.get_collection(collection_name)
                logger.info(f"Using existing collection: {collection_name}")
            except (ValueError, chromadb.errors.NotFoundError):
                logger.info(f"Creating new collection: {collection_name}")
                self._collection = self._client.create_collection(
                    name=collection_name,
                    metadata={"description": "User profile recommendations"}
                )
            
            self._initialized = True
            logger.info("Recommendation repository initialized successfully")
        except Exception as e:
            logger.exception(f"Failed to initialize recommendation repository: {str(e)}")
            raise DatabaseError(f"Failed to initialize recommendation repository: {str(e)}")
    
    async def shutdown(self) -> None:
        """
        Shutdown the repository, closing connections and releasing resources.
        """
        if self._client:
            logger.info("Shutting down recommendation repository")
            self._client = None
            self._collection = None
            self._initialized = False
    
    async def store_recommendations(self, user_id: str, recommendations: List[Recommendation]) -> None:
        """
        Store recommendations for a user.
        
        Args:
            user_id: The ID of the user.
            recommendations: List of recommendations to store.
            
        Raises:
            DatabaseError: If recommendations cannot be stored.
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Storing {len(recommendations)} recommendations for user: {user_id}")
            
            # Prepare data for storage
            ids = []
            documents = []
            metadatas = []
            
            timestamp = datetime.now(timezone.utc).isoformat()
            
            for i, rec in enumerate(recommendations):
                rec_dict = rec.dict()
                rec_id = f"{user_id}_{rec.category}_{i}_{timestamp}"
                ids.append(rec_id)
                
                # Store full recommendation as document
                documents.append(json.dumps(rec_dict))
                
                # Store category, priority, and timestamp as metadata
                metadatas.append({
                    "user_id": user_id,
                    "category": rec.category,
                    "priority": rec.priority,
                    "timestamp": timestamp
                })
            
            # Add recommendations to collection
            self._collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully stored recommendations for user: {user_id}")
        except Exception as e:
            logger.exception(f"Failed to store recommendations for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to store recommendations: {str(e)}")
    
    async def get_recommendations(self, user_id: str, category: Optional[str] = None, 
                                 limit: int = 10) -> List[Recommendation]:
        """
        Retrieve recommendations for a user.
        
        Args:
            user_id: The ID of the user.
            category: Optional category to filter by.
            limit: Maximum number of recommendations to return.
            
        Returns:
            List of Recommendation objects.
            
        Raises:
            DatabaseError: If recommendations cannot be retrieved.
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Retrieving recommendations for user: {user_id}")
            
            # Build query filter
            where_filter = {"user_id": user_id}
            if category:
                where_filter["category"] = category
            
            # Query the collection
            results = self._collection.query(
                where=where_filter,
                limit=limit
            )
            
            # Parse results into Recommendation objects
            recommendations = []
            for doc in results.get("documents", []):
                try:
                    rec_dict = json.loads(doc)
                    recommendations.append(Recommendation(**rec_dict))
                except Exception as e:
                    logger.error(f"Failed to parse recommendation: {str(e)}")
            
            logger.info(f"Retrieved {len(recommendations)} recommendations for user: {user_id}")
            return recommendations
        except Exception as e:
            logger.exception(f"Failed to retrieve recommendations for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to retrieve recommendations: {str(e)}")
    
    async def delete_user_recommendations(self, user_id: str) -> None:
        """
        Delete all recommendations for a user.
        
        Args:
            user_id: The ID of the user.
            
        Raises:
            DatabaseError: If recommendations cannot be deleted.
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            logger.info(f"Deleting recommendations for user: {user_id}")
            
            # Delete recommendations for the user
            self._collection.delete(
                where={"user_id": user_id}
            )
            
            logger.info(f"Successfully deleted recommendations for user: {user_id}")
        except Exception as e:
            logger.exception(f"Failed to delete recommendations for user {user_id}: {str(e)}")
            raise DatabaseError(f"Failed to delete recommendations: {str(e)}")

class DatabaseRecommendationRepository:
    """Recommendation repository implementation using PostgreSQL database."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the repository with database configuration.
        
        Args:
            config: Optional database configuration dictionary
        """
        self._postgres_repo = PostgreSQLRecommendationRepository(config)
    
    async def initialize(self) -> None:
        """Initialize the repository."""
        await self._postgres_repo.initialize()
    
    async def shutdown(self) -> None:
        """Shutdown the repository and release resources."""
        await self._postgres_repo.shutdown()
    
    async def store_recommendations(self, user_id: str, recommendations: List[Recommendation]) -> None:
        """
        Store recommendations for a user.
        
        Args:
            user_id: The ID of the user.
            recommendations: List of recommendations to store.
            
        Raises:
            DatabaseError: If recommendations cannot be stored.
        """
        await self._postgres_repo.store_recommendations(user_id, recommendations)
    
    async def get_recommendations(self, user_id: str, category: Optional[str] = None, 
                                 limit: int = 10) -> List[Recommendation]:
        """
        Retrieve recommendations for a user.
        
        Args:
            user_id: The ID of the user.
            category: Optional category to filter by.
            limit: Maximum number of recommendations to return.
            
        Returns:
            List of Recommendation objects.
            
        Raises:
            DatabaseError: If recommendations cannot be retrieved.
        """
        return await self._postgres_repo.get_recommendations(user_id, category, limit)
    
    async def delete_user_recommendations(self, user_id: str) -> None:
        """
        Delete all recommendations for a user.
        
        Args:
            user_id: The ID of the user.
            
        Raises:
            DatabaseError: If recommendations cannot be deleted.
        """
        await self._postgres_repo.delete_user_recommendations(user_id)
    
    async def store_profile_summary(self, user_id: str, summary: ProfileSummary) -> None:
        """
        Store a profile summary for a user.
        
        Args:
            user_id: The ID of the user.
            summary: The profile summary to store.
            
        Raises:
            DatabaseError: If the summary cannot be stored.
        """
        await self._postgres_repo.store_profile_summary(user_id, summary)
    
    async def get_profile_summary(self, user_id: str) -> Optional[ProfileSummary]:
        """
        Retrieve a profile summary for a user.
        
        Args:
            user_id: The ID of the user.
            
        Returns:
            The profile summary or None if not found.
            
        Raises:
            DatabaseError: If the summary cannot be retrieved.
        """
        return await self._postgres_repo.get_profile_summary(user_id)
    
    async def delete_user_summary(self, user_id: str) -> None:
        """
        Delete a profile summary for a user.
        
        Args:
            user_id: The ID of the user.
            
        Raises:
            DatabaseError: If the summary cannot be deleted.
        """
        await self._postgres_repo.delete_user_summary(user_id) 