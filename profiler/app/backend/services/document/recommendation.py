"""
Document recommendation service.

This module provides functionality for recommending documents to users based on 
profile content, usage patterns, and similarity to existing documents.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from datetime import datetime
import json
import math
from enum import Enum
import uuid
import heapq

from ...utils.logging import get_logger
from ...utils.errors import ValidationError, ResourceNotFoundError
from .profile_link import DocumentProfileLink, LinkType, ProfileDocumentLink

logger = get_logger(__name__)


class RecommendationSource(Enum):
    """Sources of document recommendations."""
    PROFILE_CONTENT = "profile_content"       # Based on profile content
    CONTENT_SIMILARITY = "content_similarity"  # Similar to documents user has read
    COLLABORATIVE = "collaborative"          # Based on similar users
    TRENDING = "trending"                    # Popular within the system
    RECENT_ACTIVITY = "recent_activity"      # Based on recent user activity
    CUSTOM = "custom"                        # Custom recommendation source


class RecommendationStrength(Enum):
    """Strength of document recommendations."""
    STRONG = "strong"        # Very relevant recommendation
    MEDIUM = "medium"        # Moderately relevant
    WEAK = "weak"            # Slightly relevant
    EXPLORATORY = "exploratory"  # For expanding user's horizons


class DocumentRecommendation:
    """Represents a document recommendation for a user or profile."""
    
    def __init__(self,
                 document_id: str,
                 profile_id: str,
                 source: RecommendationSource,
                 strength: RecommendationStrength,
                 score: float,
                 explanation: str,
                 created_at: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 recommendation_id: Optional[str] = None):
        """
        Initialize a document recommendation.
        
        Args:
            document_id: ID of the recommended document
            profile_id: ID of the profile receiving the recommendation
            source: Source of the recommendation
            strength: Strength/relevance of the recommendation
            score: Numerical score for the recommendation (0-1)
            explanation: Human-readable explanation for the recommendation
            created_at: When the recommendation was created
            metadata: Additional metadata about the recommendation
            recommendation_id: Unique ID for this recommendation
        """
        self.document_id = document_id
        self.profile_id = profile_id
        self.source = source
        self.strength = strength
        self.score = max(0.0, min(1.0, score))  # Clamp to 0-1
        self.explanation = explanation
        self.created_at = created_at or datetime.utcnow()
        self.metadata = metadata or {}
        self.recommendation_id = recommendation_id or str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert recommendation to dictionary for storage or serialization."""
        return {
            "recommendation_id": self.recommendation_id,
            "document_id": self.document_id,
            "profile_id": self.profile_id,
            "source": self.source.value,
            "strength": self.strength.value,
            "score": self.score,
            "explanation": self.explanation,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentRecommendation':
        """Create a recommendation from a dictionary."""
        source = RecommendationSource(data.get("source"))
        strength = RecommendationStrength(data.get("strength"))
        created_at = datetime.fromisoformat(data.get("created_at")) if data.get("created_at") else None
        
        return cls(
            document_id=data.get("document_id"),
            profile_id=data.get("profile_id"),
            source=source,
            strength=strength,
            score=data.get("score", 0.0),
            explanation=data.get("explanation", ""),
            created_at=created_at,
            metadata=data.get("metadata", {}),
            recommendation_id=data.get("recommendation_id")
        )


class ContentSimilarityCalculator:
    """Calculator for content similarity between documents."""
    
    def __init__(self):
        """Initialize the content similarity calculator."""
        pass
    
    async def calculate_similarity(self, 
                               doc1_content: Dict[str, Any], 
                               doc2_content: Dict[str, Any]) -> float:
        """
        Calculate similarity between two document contents.
        
        Args:
            doc1_content: Content representation of first document
            doc2_content: Content representation of second document
            
        Returns:
            Similarity score (0-1)
        """
        # Check for empty content
        if not doc1_content or not doc2_content:
            return 0.0
        
        # Extract text content if available
        text1 = doc1_content.get("text", "")
        text2 = doc2_content.get("text", "")
        
        if not text1 or not text2:
            return 0.0
        
        # Use cosine similarity if embeddings are available
        embeddings1 = doc1_content.get("embeddings")
        embeddings2 = doc2_content.get("embeddings")
        
        if embeddings1 and embeddings2 and len(embeddings1) == len(embeddings2):
            return self._cosine_similarity(embeddings1, embeddings2)
        
        # Fall back to naive text similarity
        return self._text_similarity(text1, text2)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))
        
        # Avoid division by zero
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate naive text similarity based on word overlap."""
        # Convert to lowercase and split into words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        # Avoid division by zero
        if union == 0:
            return 0.0
        
        return intersection / union


class DocumentRecommender:
    """
    Service for recommending documents based on profile content.
    
    This service generates personalized document recommendations for users
    based on their profile content, document interaction history, and 
    similar documents in the system.
    """
    
    def __init__(self, 
                 document_repository=None, 
                 profile_repository=None,
                 document_profile_link_service=None):
        """
        Initialize the document recommendation service.
        
        Args:
            document_repository: Repository for accessing documents
            profile_repository: Repository for accessing profiles
            document_profile_link_service: Service for document-profile links
        """
        self.document_repository = document_repository
        self.profile_repository = profile_repository
        self.link_service = document_profile_link_service
        self.similarity_calculator = ContentSimilarityCalculator()
        
        # In-memory cache of recommendations
        self._recommendations: Dict[str, Dict[str, DocumentRecommendation]] = {}  # profile_id -> {document_id -> recommendation}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the document recommendation service."""
        if self._initialized:
            return
        
        # Initialize dependencies
        if self.document_repository:
            await self.document_repository.initialize()
        
        if self.profile_repository:
            await self.profile_repository.initialize()
        
        if self.link_service:
            await self.link_service.initialize()
        
        self._initialized = True
        logger.info("Document recommendation service initialized")
    
    async def refresh_recommendations(self, profile_id: str) -> List[DocumentRecommendation]:
        """
        Generate fresh recommendations for a profile.
        
        Args:
            profile_id: ID of the profile to generate recommendations for
            
        Returns:
            List of document recommendations
            
        Raises:
            ResourceNotFoundError: If profile is not found
        """
        if not self._initialized:
            await self.initialize()
        
        # Check if profile exists
        if self.profile_repository:
            profile = await self.profile_repository.get_profile(profile_id)
            if not profile:
                raise ResourceNotFoundError(f"Profile {profile_id} not found")
        
        # Get existing documents for this profile
        existing_documents = set()
        if self.link_service:
            links = await self.link_service.get_profile_documents(profile_id)
            existing_documents = {link.document_id for link in links}
        
        # Generate recommendations from different sources
        recommendations = []
        
        # Content-based recommendations
        content_recs = await self._generate_content_based_recommendations(profile_id, existing_documents)
        recommendations.extend(content_recs)
        
        # Collaborative recommendations
        collab_recs = await self._generate_collaborative_recommendations(profile_id, existing_documents)
        recommendations.extend(collab_recs)
        
        # Trending recommendations
        trending_recs = await self._generate_trending_recommendations(profile_id, existing_documents)
        recommendations.extend(trending_recs)
        
        # Sort by score (descending)
        recommendations.sort(key=lambda r: r.score, reverse=True)
        
        # Update cache
        self._recommendations[profile_id] = {r.document_id: r for r in recommendations}
        
        logger.info(f"Generated {len(recommendations)} recommendations for profile {profile_id}")
        return recommendations
    
    async def _generate_content_based_recommendations(self, 
                                                  profile_id: str, 
                                                  existing_document_ids: Set[str]) -> List[DocumentRecommendation]:
        """Generate recommendations based on profile content."""
        if not self.profile_repository or not self.document_repository:
            return []
        
        try:
            # Get profile content
            profile = await self.profile_repository.get_profile(profile_id)
            if not profile:
                return []
            
            # Extract relevant profile data
            profile_data = {
                "interests": profile.get("interests", []),
                "skills": profile.get("skills", []),
                "education": profile.get("education", []),
                "experience": profile.get("experience", [])
            }
            
            # Get candidate documents (limit to recent ones for efficiency)
            all_documents = await self.document_repository.list_documents(limit=100, 
                                                                       sort_by="created_at", 
                                                                       sort_order="desc")
            
            # Filter out existing documents
            candidates = [doc for doc in all_documents if doc["document_id"] not in existing_document_ids]
            
            # Score each candidate document
            scored_docs = []
            for doc in candidates:
                score = await self._calculate_profile_document_relevance(profile_data, doc)
                if score > 0.1:  # Only include somewhat relevant docs
                    strength = self._score_to_strength(score)
                    explanation = self._generate_content_explanation(profile_data, doc, score)
                    
                    recommendation = DocumentRecommendation(
                        document_id=doc["document_id"],
                        profile_id=profile_id,
                        source=RecommendationSource.PROFILE_CONTENT,
                        strength=strength,
                        score=score,
                        explanation=explanation
                    )
                    scored_docs.append(recommendation)
            
            # Return top recommendations
            return heapq.nlargest(10, scored_docs, key=lambda r: r.score)
        
        except Exception as e:
            logger.error(f"Error generating content-based recommendations: {str(e)}")
            return []
    
    async def _generate_collaborative_recommendations(self, 
                                                  profile_id: str, 
                                                  existing_document_ids: Set[str]) -> List[DocumentRecommendation]:
        """Generate recommendations based on similar users."""
        if not self.profile_repository or not self.link_service:
            return []
        
        try:
            # This would normally use a complex collaborative filtering algorithm
            # For demonstration, we'll use a simplified approach
            
            # Get documents from similar profiles
            # In a real system, this would involve finding similar profiles first
            recommendations = []
            
            # Placeholder for actual collaborative filtering
            # In a production system, this would be implemented with a proper algorithm
            
            # Return placeholder recommendations as a demonstration
            for i in range(3):
                rec_id = f"collab_{i}"
                doc_id = f"doc_{rec_id}"
                
                # Skip if document already exists for this profile
                if doc_id in existing_document_ids:
                    continue
                
                # Create recommendation
                score = 0.7 - (i * 0.1)  # Decreasing scores
                strength = self._score_to_strength(score)
                
                recommendation = DocumentRecommendation(
                    document_id=doc_id,
                    profile_id=profile_id,
                    source=RecommendationSource.COLLABORATIVE,
                    strength=strength,
                    score=score,
                    explanation=f"Recommended based on documents that similar users have found valuable"
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating collaborative recommendations: {str(e)}")
            return []
    
    async def _generate_trending_recommendations(self, 
                                             profile_id: str, 
                                             existing_document_ids: Set[str]) -> List[DocumentRecommendation]:
        """Generate recommendations based on trending documents."""
        if not self.document_repository:
            return []
        
        try:
            # Get trending documents (normally based on recent activity)
            # This would typically involve analytics data
            
            # For demonstration, we'll just use recent documents
            recent_docs = await self.document_repository.list_documents(
                limit=5,
                sort_by="created_at",
                sort_order="desc"
            )
            
            # Filter out existing documents
            candidates = [doc for doc in recent_docs if doc["document_id"] not in existing_document_ids]
            
            # Create recommendations
            recommendations = []
            for i, doc in enumerate(candidates):
                score = 0.6 - (i * 0.05)  # Decreasing scores
                strength = self._score_to_strength(score)
                
                recommendation = DocumentRecommendation(
                    document_id=doc["document_id"],
                    profile_id=profile_id,
                    source=RecommendationSource.TRENDING,
                    strength=strength,
                    score=score,
                    explanation=f"Trending document in the system"
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating trending recommendations: {str(e)}")
            return []
    
    async def _calculate_profile_document_relevance(self, 
                                               profile_data: Dict[str, Any], 
                                               document: Dict[str, Any]) -> float:
        """Calculate relevance score between a profile and document."""
        # Extract document metadata and content
        doc_metadata = document.get("metadata", {})
        doc_title = doc_metadata.get("title", "")
        doc_description = doc_metadata.get("description", "")
        doc_keywords = doc_metadata.get("keywords", [])
        doc_categories = doc_metadata.get("categories", [])
        
        # Extract profile interests and skills
        profile_interests = profile_data.get("interests", [])
        profile_skills = profile_data.get("skills", [])
        
        # Calculate keyword matches
        interest_matches = sum(1 for interest in profile_interests 
                             if interest.lower() in doc_title.lower() or
                                interest.lower() in doc_description.lower() or
                                any(interest.lower() in kw.lower() for kw in doc_keywords))
        
        skill_matches = sum(1 for skill in profile_skills 
                          if skill.lower() in doc_title.lower() or
                             skill.lower() in doc_description.lower() or
                             any(skill.lower() in kw.lower() for kw in doc_keywords))
        
        # Category matches
        category_relevance = sum(1 for cat in doc_categories 
                               if any(interest.lower() in cat.lower() for interest in profile_interests))
        
        # Combine scores (weights could be adjusted based on importance)
        base_score = (interest_matches * 0.4 + 
                    skill_matches * 0.4 + 
                    category_relevance * 0.2)
        
        # Normalize to 0-1 range
        return min(1.0, base_score / 10.0)
    
    def _score_to_strength(self, score: float) -> RecommendationStrength:
        """Convert numerical score to recommendation strength."""
        if score >= 0.8:
            return RecommendationStrength.STRONG
        elif score >= 0.5:
            return RecommendationStrength.MEDIUM
        elif score >= 0.3:
            return RecommendationStrength.WEAK
        else:
            return RecommendationStrength.EXPLORATORY
    
    def _generate_content_explanation(self, 
                                    profile_data: Dict[str, Any], 
                                    document: Dict[str, Any],
                                    score: float) -> str:
        """Generate human-readable explanation for a content-based recommendation."""
        # Extract document metadata
        doc_metadata = document.get("metadata", {})
        doc_title = doc_metadata.get("title", "Untitled document")
        
        # Extract profile interests and skills
        profile_interests = profile_data.get("interests", [])
        profile_skills = profile_data.get("skills", [])
        
        # Create explanation based on strength
        if score >= 0.8:
            return f"Strongly matches your interests in {', '.join(profile_interests[:2])}"
        elif score >= 0.5:
            return f"Related to your skills in {', '.join(profile_skills[:2])}"
        elif score >= 0.3:
            return f"Somewhat related to your profile"
        else:
            return f"Recommended to expand your knowledge"
    
    async def get_recommendations(self, 
                              profile_id: str, 
                              limit: int = 10,
                              refresh: bool = False) -> List[DocumentRecommendation]:
        """
        Get document recommendations for a profile.
        
        Args:
            profile_id: ID of the profile to get recommendations for
            limit: Maximum number of recommendations to return
            refresh: Whether to refresh recommendations
            
        Returns:
            List of document recommendations
            
        Raises:
            ResourceNotFoundError: If profile is not found
        """
        if not self._initialized:
            await self.initialize()
        
        # Refresh if requested or no recommendations exist
        if refresh or profile_id not in self._recommendations:
            await self.refresh_recommendations(profile_id)
        
        # Get recommendations from cache
        recommendations = list(self._recommendations.get(profile_id, {}).values())
        
        # Sort by score (descending) and apply limit
        recommendations.sort(key=lambda r: r.score, reverse=True)
        return recommendations[:limit]
    
    async def get_document_similarity(self, 
                                  document_id: str, 
                                  profile_id: Optional[str] = None) -> List[Tuple[str, float]]:
        """
        Find documents similar to the given document.
        
        Args:
            document_id: ID of the document to find similar documents for
            profile_id: Optional profile ID to filter by relevance
            
        Returns:
            List of (document_id, similarity_score) tuples
            
        Raises:
            ResourceNotFoundError: If document is not found
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.document_repository:
            return []
        
        try:
            # Get the source document
            document = await self.document_repository.get_document(document_id)
            if not document:
                raise ResourceNotFoundError(f"Document {document_id} not found")
            
            # Get document content
            document_content = await self.document_repository.get_document_content(document_id)
            
            # Get candidate documents (limit for efficiency)
            candidates = await self.document_repository.list_documents(limit=50)
            
            # Filter out the source document
            candidates = [doc for doc in candidates if doc["document_id"] != document_id]
            
            # Calculate similarity for each candidate
            similarities = []
            for candidate in candidates:
                candidate_id = candidate["document_id"]
                candidate_content = await self.document_repository.get_document_content(candidate_id)
                
                # Calculate content similarity
                similarity = await self.similarity_calculator.calculate_similarity(
                    document_content, candidate_content
                )
                
                if similarity > 0.1:  # Only include somewhat similar docs
                    similarities.append((candidate_id, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            return similarities[:10]  # Return top 10
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {str(e)}")
            return []
    
    async def create_custom_recommendation(self,
                                        document_id: str,
                                        profile_id: str,
                                        score: float,
                                        explanation: str,
                                        strength: Optional[RecommendationStrength] = None) -> DocumentRecommendation:
        """
        Create a custom recommendation.
        
        Args:
            document_id: ID of the document to recommend
            profile_id: ID of the profile to recommend to
            score: Recommendation score
            explanation: Explanation for the recommendation
            strength: Optional recommendation strength
            
        Returns:
            Created recommendation
            
        Raises:
            ValidationError: If parameters are invalid
        """
        if not self._initialized:
            await self.initialize()
        
        # Validate parameters
        if not document_id:
            raise ValidationError("Document ID is required")
        if not profile_id:
            raise ValidationError("Profile ID is required")
        if not explanation:
            raise ValidationError("Explanation is required")
        
        # Use provided strength or derive from score
        if strength is None:
            strength = self._score_to_strength(score)
        
        # Create recommendation
        recommendation = DocumentRecommendation(
            document_id=document_id,
            profile_id=profile_id,
            source=RecommendationSource.CUSTOM,
            strength=strength,
            score=score,
            explanation=explanation
        )
        
        # Update cache
        if profile_id not in self._recommendations:
            self._recommendations[profile_id] = {}
        self._recommendations[profile_id][document_id] = recommendation
        
        logger.info(f"Created custom recommendation for document {document_id} to profile {profile_id}")
        return recommendation 