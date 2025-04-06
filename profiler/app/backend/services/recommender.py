"""
Recommendation service for suggesting profile improvements.

This service analyzes profile data and provides actionable
recommendations to improve the profile quality.
"""

import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import chromadb
from datetime import datetime
import logging
import json

from app.backend.core.deepseek.r1 import DeepSeekR1
from app.backend.config import settings
from app.backend.utils.logging import get_logger, log_function_call
from app.backend.utils.errors import ServiceError, ValidationError
from app.backend.utils.cache import cache_async
from app.backend.core.interfaces import AIClientInterface
from app.backend.services.interfaces import RecommendationServiceInterface
from app.backend.services.recommendation.models import Recommendation, ProfileSummary
from app.backend.services.recommendation.repository import RecommendationRepository
from app.backend.services.recommendation.scoring import ProfileScorer

logger = get_logger(__name__)

class Recommendation(BaseModel):
    """Model for profile recommendations"""
    category: str = Field(..., description="Category of recommendation")
    title: str = Field(..., description="Title of recommendation")
    description: str = Field(..., description="Detailed description")
    priority: int = Field(..., description="Priority level (1-5)")
    action_items: List[str] = Field(..., description="Specific action items")
    confidence: float = Field(..., description="Confidence score")

class ProfileSummary(BaseModel):
    """Model for profile summary"""
    strengths: List[str] = Field(..., description="Key strengths")
    areas_for_improvement: List[str] = Field(..., description="Areas to improve")
    unique_selling_points: List[str] = Field(..., description="Unique selling points")
    overall_quality: float = Field(..., description="Overall profile quality score")
    last_updated: str = Field(..., description="Last update timestamp")

class RecommenderService(RecommendationServiceInterface):
    """Service for generating profile recommendations"""
    
    def __init__(self, client: AIClientInterface, repository: Optional[RecommendationRepository] = None):
        """Initialize with AI client and optional repository"""
        self._client = client
        self._repository = repository or RecommendationRepository()
        
        # Define recommendation categories
        self.categories = {
            "academic": {
                "weight": 0.3,
                "subcategories": ["grades", "courses", "achievements"]
            },
            "extracurricular": {
                "weight": 0.25,
                "subcategories": ["activities", "leadership", "service"]
            },
            "personal": {
                "weight": 0.25,
                "subcategories": ["background", "goals", "interests"]
            },
            "essays": {
                "weight": 0.2,
                "subcategories": ["topics", "content", "style"]
            }
        }
        
        # Initialize scorer
        self._scorer = ProfileScorer(self.categories)
    
    async def initialize(self) -> None:
        """Initialize service dependencies"""
        logger.info("Initializing recommendation service")
        await self._repository.initialize()
    
    async def shutdown(self) -> None:
        """Clean up service resources"""
        logger.info("Shutting down recommendation service")
        await self._repository.shutdown()
    
    @log_function_call(logger)
    async def get_recommendations(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Get personalized recommendations for a profile"""
        if not profile:
            raise ValidationError("Profile data cannot be empty")
            
        user_id = profile.get("user_id")
        if not user_id:
            raise ValidationError("User ID is required")
            
        profile_data = {k: v for k, v in profile.items() if k != "user_id"}
        
        try:
            logger.info(f"Generating recommendations for user: {user_id}")
            
            # Generate recommendations for each category
            all_recommendations = []
            for category, config in self.categories.items():
                if category in profile_data:
                    category_recs = await self._generate_category_recommendations(
                        category,
                        profile_data.get(category, {}),
                        config
                    )
                    all_recommendations.extend(category_recs)
            
            # Sort by priority and confidence
            all_recommendations.sort(
                key=lambda x: (x.priority, x.confidence),
                reverse=True
            )
            
            # Store recommendations if repository available
            try:
                await self._repository.store_recommendations(user_id, all_recommendations)
            except Exception as e:
                # Log but don't fail if storage fails
                logger.error(f"Failed to store recommendations: {str(e)}")
            
            # Organize recommendations by category
            recommendations_by_category = {}
            for rec in all_recommendations:
                if rec.category not in recommendations_by_category:
                    recommendations_by_category[rec.category] = []
                recommendations_by_category[rec.category].append(rec.dict())
            
            # Calculate overall quality
            quality_score = self._scorer.calculate_quality_score(profile_data)
            
            return {
                "recommendations": recommendations_by_category,
                "overall_quality": quality_score
            }
            
        except ValidationError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.exception(f"Error generating recommendations for user {user_id}: {str(e)}")
            raise ServiceError(f"Failed to generate recommendations: {str(e)}")
    
    @log_function_call(logger)
    async def get_section_recommendations(self, section: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get recommendations for a specific profile section"""
        if section not in self.categories:
            raise ValidationError(f"Invalid section: {section}. Valid sections are: {list(self.categories.keys())}")
        
        try:
            logger.info(f"Generating recommendations for section: {section}")
            
            recommendations = await self._generate_category_recommendations(
                section,
                data,
                self.categories[section]
            )
            
            # Calculate section quality score
            section_data = {section: data}
            quality_score = self._scorer.calculate_category_score(
                section,
                data,
                self.categories[section]
            )
            
            return {
                "recommendations": [rec.dict() for rec in recommendations],
                "quality_score": quality_score
            }
            
        except ValidationError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.exception(f"Error generating recommendations for section {section}: {str(e)}")
            raise ServiceError(f"Failed to generate section recommendations: {str(e)}")
    
    @log_function_call(logger)
    @cache_async(ttl=3600)  # Cache for 1 hour
    async def get_profile_summary(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of a user profile"""
        if not profile:
            raise ValidationError("Profile data cannot be empty")
            
        user_id = profile.get("user_id")
        if not user_id:
            raise ValidationError("User ID is required")
            
        sections = profile.get("sections")
        if not sections:
            raise ValidationError("Profile sections are required")
        
        try:
            logger.info(f"Generating profile summary for user: {user_id}")
            
            # Generate summary using LLM
            summary = await self._generate_summary(sections)
            
            # Calculate overall quality
            quality_score = self._scorer.calculate_quality_score(sections)
            
            result = {
                "summary": {
                    "strengths": summary.get("strengths", []),
                    "areas_for_improvement": summary.get("areas_for_improvement", []),
                    "unique_selling_points": summary.get("unique_selling_points", []),
                    "overall_quality": quality_score,
                    "last_updated": datetime.utcnow().isoformat()
                }
            }
            
            logger.info(f"Generated profile summary for user: {user_id}")
            return result
            
        except ValidationError as e:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.exception(f"Error generating profile summary for user {user_id}: {str(e)}")
            raise ServiceError(f"Failed to generate profile summary: {str(e)}")
    
    async def _generate_category_recommendations(
        self,
        category: str,
        category_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Recommendation]:
        """Generate recommendations for a specific category"""
        try:
            logger.info(f"Generating recommendations for category: {category}")
            
            # Prepare analysis prompt
            prompt = f"""Analyze the following {category} profile data and provide recommendations:
            
            Data:
            {json.dumps(category_data, indent=2)}
            
            Consider:
            1. Strengths and achievements
            2. Areas for improvement
            3. Missing information
            4. Action items
            
            Provide 2-3 specific recommendations in JSON format with:
            - title: Clear title for the recommendation
            - description: Detailed description of the recommendation
            - priority: Priority level (1-5)
            - action_items: List of actionable items"""
            
            # Get analysis from LLM
            async with self._client as client:
                result = await client.analyze(
                    text=prompt,
                    analysis_type=f"profile_{category}"
                )
            
            # Parse recommendations
            recommendations = []
            recs_data = result.get("analysis", {}).get("recommendations", [])
            
            if not isinstance(recs_data, list):
                logger.warning(f"Unexpected recommendation format for {category}: {recs_data}")
                return []
                
            for rec_data in recs_data:
                try:
                    recommendations.append(
                        Recommendation(
                            category=category,
                            title=rec_data["title"],
                            description=rec_data["description"],
                            priority=rec_data["priority"],
                            action_items=rec_data["action_items"],
                            confidence=rec_data.get("confidence", 0.8)
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse recommendation: {rec_data}. Error: {str(e)}")
            
            logger.info(f"Generated {len(recommendations)} recommendations for category: {category}")
            return recommendations
            
        except Exception as e:
            logger.exception(f"Error generating {category} recommendations: {str(e)}")
            return []
    
    async def _generate_summary(self, profile_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate a comprehensive profile summary"""
        try:
            logger.info("Generating profile summary")
            
            # Prepare summary prompt
            prompt = f"""Analyze this student profile and provide:
            1. Key strengths (3-5)
            2. Areas for improvement (3-5)
            3. Unique selling points (2-3)
            
            Profile Data:
            {json.dumps(profile_data, indent=2)}
            
            Focus on:
            - Academic achievements
            - Extracurricular involvement
            - Personal experiences
            - Essay quality
            
            Respond with a JSON object containing:
            - strengths: array of strengths
            - areas_for_improvement: array of improvement areas
            - unique_selling_points: array of unique selling points"""
            
            # Get summary from LLM
            async with self._client as client:
                result = await client.analyze(
                    text=prompt,
                    analysis_type="profile_summary"
                )
            
            summary = result.get("analysis", {})
            
            # Ensure proper structure
            if not isinstance(summary.get("strengths"), list):
                summary["strengths"] = []
            if not isinstance(summary.get("areas_for_improvement"), list):
                summary["areas_for_improvement"] = []
            if not isinstance(summary.get("unique_selling_points"), list):
                summary["unique_selling_points"] = []
                
            logger.info("Successfully generated profile summary")
            return summary
            
        except Exception as e:
            logger.exception(f"Error generating profile summary: {str(e)}")
            return {
                "strengths": [],
                "areas_for_improvement": [],
                "unique_selling_points": []
            } 