"""
Recommendation service for generating profile recommendations.

This module implements the IRecommendationService interface to provide
personalized recommendations for improving user profiles.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json

from ...utils.logging import get_logger, log_execution_time
from ...utils.errors import ValidationError, ServiceError
from ...utils.config_manager import ConfigManager
from ...core.interfaces import AIClientInterface
from ...services.interfaces import IRecommendationService
from .models import Recommendation, ProfileSummary
from .repository import RecommendationRepository
from .scoring import ProfileScorer

logger = get_logger(__name__)

class RecommendationService(IRecommendationService):
    """
    Service for generating personalized profile recommendations.
    
    This service analyzes user profiles to generate tailored recommendations
    for improving profile quality and effectiveness.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, ai_client: Optional[AIClientInterface] = None, repository: Optional[RecommendationRepository] = None):
        """
        Initialize the recommendation service.
        
        Args:
            config: Optional configuration dictionary
            ai_client: Optional client for AI model interactions
            repository: Optional repository for storing recommendations
        """
        # Load config
        self._full_config = config or ConfigManager().get_all()
        self._config = self._full_config.get("recommendation_service", {})
        
        # Initialize AI client if not provided
        if ai_client is None:
            if "ai_client" in self._full_config:
                self._client = self._full_config["ai_client"]
            elif "ai_clients" in self._full_config and "deepseek" in self._full_config["ai_clients"]:
                from ...core.deepseek.r1 import DeepSeekR1
                self._client = DeepSeekR1(
                    api_key=self._full_config["ai_clients"]["deepseek"]["api_key"],
                    base_url=self._full_config["ai_clients"]["deepseek"]["url"]
                )
            else:
                # Default to a mock client for testing
                from ...core.interfaces import AIClientInterface
                class MockClient(AIClientInterface):
                    async def complete(self, prompt, **kwargs):
                        return {"text": "This is a mock response"}
                self._client = MockClient()
        else:
            self._client = ai_client
        
        # Initialize repository
        self._repository = repository or RecommendationRepository()
        
        # Define recommendation categories with weights and subcategories
        self.categories = self._config.get("categories", {
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
        })
        
        # Initialize scorer
        self._scorer = ProfileScorer(self.categories)
        
        logger.info(f"Initialized RecommendationService with {len(self.categories)} categories")
    
    async def initialize(self) -> None:
        """
        Initialize the service and its dependencies.
        
        Raises:
            ServiceError: If initialization fails
        """
        try:
            logger.info("Initializing recommendation service")
            await self._repository.initialize()
            logger.info("Recommendation service initialized successfully")
        except Exception as e:
            logger.exception(f"Failed to initialize recommendation service: {str(e)}")
            raise ServiceError(f"Failed to initialize recommendation service: {str(e)}")
    
    async def shutdown(self) -> None:
        """
        Shutdown the service and release resources.
        """
        logger.info("Shutting down recommendation service")
        await self._repository.shutdown()
        logger.info("Recommendation service shut down successfully")
    
    @log_execution_time(logger)
    async def generate_recommendations(
        self, 
        profile_data: Dict[str, Any],
        categories: Optional[List[str]] = None
    ) -> List[Recommendation]:
        """
        Generate recommendations based on profile data.
        
        Args:
            profile_data: The user's profile data
            categories: Optional list of categories to generate recommendations for
            
        Returns:
            List of Recommendation objects
            
        Raises:
            ValidationError: If the profile data is invalid
            ServiceError: If recommendations cannot be generated
        """
        if not profile_data:
            logger.error("Empty profile data provided")
            raise ValidationError("Profile data cannot be empty")
            
        user_id = profile_data.get("user_id")
        if not user_id:
            logger.error("User ID is missing from profile data")
            raise ValidationError("User ID is required in profile data")
            
        # Extract profile content excluding user_id
        profile_content = {k: v for k, v in profile_data.items() if k != "user_id"}
        
        try:
            logger.info(f"Generating recommendations for user: {user_id}")
            
            # Filter categories if specified
            target_categories = categories or list(self.categories.keys())
            filtered_categories = {
                category: config for category, config in self.categories.items()
                if category in target_categories and category in profile_content
            }
            
            if not filtered_categories:
                logger.warning("No valid categories found for recommendation generation")
                return []
            
            # Generate recommendations for each category
            all_recommendations = []
            for category, config in filtered_categories.items():
                logger.info(f"Generating recommendations for category: {category}")
                category_data = profile_content.get(category, {})
                
                category_recs = await self._generate_category_recommendations(
                    category,
                    category_data,
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
                logger.info(f"Stored {len(all_recommendations)} recommendations for user: {user_id}")
            except Exception as e:
                # Log but don't fail if storage fails
                logger.error(f"Failed to store recommendations: {str(e)}")
            
            return all_recommendations
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.exception(f"Error generating recommendations for user {user_id}: {str(e)}")
            raise ServiceError(f"Failed to generate recommendations: {str(e)}")
    
    @log_execution_time(logger)
    async def get_profile_summary(self, profile_data: Dict[str, Any]) -> ProfileSummary:
        """
        Generate a summary of the user's profile.
        
        Args:
            profile_data: The user's profile data
            
        Returns:
            ProfileSummary object
            
        Raises:
            ValidationError: If the profile data is invalid
            ServiceError: If the summary cannot be generated
        """
        if not profile_data:
            logger.error("Empty profile data provided")
            raise ValidationError("Profile data cannot be empty")
            
        user_id = profile_data.get("user_id")
        if not user_id:
            logger.error("User ID is missing from profile data")
            raise ValidationError("User ID is required in profile data")
        
        try:
            logger.info(f"Generating profile summary for user: {user_id}")
            
            # Extract profile content excluding user_id
            profile_content = {k: v for k, v in profile_data.items() if k != "user_id"}
            
            # Calculate overall quality
            quality_score = self._scorer.calculate_quality_score(profile_content)
            
            # Generate summary using AI client
            summary_result = await self._generate_summary(profile_content)
            
            # Create and return ProfileSummary
            current_time = datetime.now(timezone.utc).isoformat()
            summary = ProfileSummary(
                strengths=summary_result.get("strengths", []),
                areas_for_improvement=summary_result.get("areas_for_improvement", []),
                unique_selling_points=summary_result.get("unique_selling_points", []),
                overall_quality=quality_score,
                last_updated=current_time
            )
            
            logger.info(f"Generated profile summary for user: {user_id}")
            return summary
            
        except ValidationError:
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
        """
        Generate recommendations for a specific category.
        
        Args:
            category: The category name
            category_data: Data for the specific category
            config: Configuration for the category
            
        Returns:
            List of Recommendation objects
        """
        if not category_data:
            logger.warning(f"Empty data for category: {category}")
            return []
        
        try:
            # Prepare prompt for AI model
            subcategories = config.get("subcategories", [])
            subcategory_data = {
                subcategory: category_data.get(subcategory, {})
                for subcategory in subcategories
                if subcategory in category_data
            }
            
            prompt = {
                "task": "generate_recommendations",
                "category": category,
                "category_data": json.dumps(category_data),
                "subcategories": subcategories,
                "num_recommendations": self._config.get("recommendations_per_category", 3)
            }
            
            # Get recommendations from AI model
            response = await self._client.generate_structured_output(
                messages=[
                    {"role": "system", "content": "You are a profile recommendation assistant."},
                    {"role": "user", "content": json.dumps(prompt)}
                ],
                response_schema={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                            "action_items": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                        },
                        "required": ["category", "title", "description", "priority", "action_items", "confidence"]
                    }
                }
            )
            
            # Parse response into Recommendation objects
            recommendations = []
            for item in response:
                recommendations.append(Recommendation(**item))
            
            logger.info(f"Generated {len(recommendations)} recommendations for category: {category}")
            return recommendations
            
        except Exception as e:
            logger.exception(f"Error generating recommendations for category {category}: {str(e)}")
            # Return empty list instead of failing the entire process
            return []
    
    async def _generate_summary(self, profile_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Generate a summary of profile strengths and areas for improvement.
        
        Args:
            profile_data: The profile data to summarize
            
        Returns:
            Dictionary with strengths, areas_for_improvement, and unique_selling_points
        """
        try:
            # Prepare prompt for AI model
            prompt = {
                "task": "generate_profile_summary",
                "profile_data": json.dumps(profile_data)
            }
            
            # Get summary from AI model
            response = await self._client.generate_structured_output(
                messages=[
                    {"role": "system", "content": "You are a profile summarization assistant."},
                    {"role": "user", "content": json.dumps(prompt)}
                ],
                response_schema={
                    "type": "object",
                    "properties": {
                        "strengths": {"type": "array", "items": {"type": "string"}},
                        "areas_for_improvement": {"type": "array", "items": {"type": "string"}},
                        "unique_selling_points": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["strengths", "areas_for_improvement", "unique_selling_points"]
                }
            )
            
            logger.info("Generated profile summary successfully")
            return response
            
        except Exception as e:
            logger.exception(f"Error generating profile summary: {str(e)}")
            # Return empty summary instead of failing
            return {
                "strengths": [],
                "areas_for_improvement": [],
                "unique_selling_points": []
            } 