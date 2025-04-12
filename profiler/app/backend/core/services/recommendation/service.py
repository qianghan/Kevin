import logging
from typing import Dict, Any, List, Optional
from .providers.university_provider import UniversityProvider
from .merger import RecommendationMerger

class RecommendationService:
    def __init__(self, config: Dict[str, Any], university_provider: Optional[UniversityProvider] = None):
        self.config = config
        self.university_provider = university_provider
        self.logger = logging.getLogger(__name__)
        self.merger = RecommendationMerger()

    async def initialize(self) -> None:
        """Initialize the service and its dependencies"""
        if self.university_provider:
            try:
                await self.university_provider.initialize()
                self.logger.info("University provider initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize university provider: {e}")

    def _is_profile_complete_enough(self, profile_data: Dict[str, Any]) -> bool:
        """Check if profile has enough data for university recommendations"""
        required_sections = ["academic", "personal", "extracurricular"]
        return all(section in profile_data and profile_data[section] for section in required_sections)

    async def _get_standard_recommendations(self, profile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate standard recommendations based on profile data"""
        try:
            # Implementation of standard recommendation logic
            recommendations = []
            # Add logic for generating standard recommendations
            # This could include recommendations for:
            # - Study tips
            # - Extracurricular activities
            # - Test preparation
            # - General career guidance
            return recommendations
        except Exception as e:
            self.logger.error(f"Error generating standard recommendations: {e}")
            return []

    async def _get_university_recommendations(self, profile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get university recommendations with error handling"""
        if not self.university_provider:
            self.logger.info("No university provider configured, skipping university recommendations")
            return []

        if not self.university_provider.is_available:
            self.logger.warning(f"University provider unavailable: {self.university_provider.last_error}")
            return []

        try:
            return await self.university_provider.get_universities(profile_data)
        except Exception as e:
            self.logger.error(f"Error getting university recommendations: {e}")
            return []

    async def generate_recommendations(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations based on profile data"""
        try:
            # Get standard recommendations
            standard_recs = await self._get_standard_recommendations(profile_data)
            
            # Get university recommendations if profile is complete enough
            university_recs = []
            if self._is_profile_complete_enough(profile_data):
                university_recs = await self._get_university_recommendations(profile_data)
            
            # Merge recommendations
            merged_recs = await self.merger.merge_recommendations(standard_recs, university_recs)
            
            return {
                "recommendations": merged_recs,
                "has_university_recommendations": bool(university_recs),
                "recommendation_sources": {
                    "standard": True,
                    "university": bool(university_recs)
                }
            }
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return {
                "recommendations": [],
                "has_university_recommendations": False,
                "recommendation_sources": {
                    "standard": False,
                    "university": False
                },
                "error": str(e)
            }

    async def shutdown(self) -> None:
        """Clean up resources"""
        if self.university_provider:
            try:
                await self.university_provider.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down university provider: {e}") 