from typing import Dict, Any, List, Optional
import logging
from .repository import RecommendationRepository
from .scoring import ProfileScorer
from .providers.university_provider import UniversityProvider
from .factory import UniversityProviderFactory
from .merger import RecommendationMerger

class RecommendationService:
    """Service for generating personalized recommendations"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.repository = None
        self.scorer = None
        self.university_provider = None
        self.recommendation_merger = RecommendationMerger()
        
        # Initialize scorer with categories
        categories = ["personal", "academic", "extracurricular", "essays"]
        self.scorer = ProfileScorer(categories)
        self.logger.info(f"Initialized RecommendationService with {len(categories)} categories")
        
    async def initialize(self):
        """Initialize the recommendation service"""
        self.logger.info("Initializing recommendation service")
        
        # Initialize repository
        self.repository = RecommendationRepository(self.config)
        await self.repository.initialize()
        
        # Initialize university provider if enabled
        self.university_provider = await UniversityProviderFactory.create_provider(self.config)
        
        self.logger.info("Recommendation service initialized successfully")
        
    async def get_recommendations(self, profile_state: dict) -> dict:
        """Get recommendations for a profile"""
        # Get standard recommendations
        standard_recs = await self._get_internal_recommendations(profile_state)
        
        # Add university recommendations if provider is available and profile is complete enough
        if self.university_provider and self._is_profile_complete_enough(profile_state):
            try:
                self.logger.info("Getting university recommendations")
                profile_data = self._extract_university_relevant_data(profile_state)
                university_recs = await self.university_provider.get_universities(profile_data)
                self.logger.info(f"Retrieved {len(university_recs)} university recommendations")
                return await self.recommendation_merger.merge_recommendations(standard_recs, university_recs)
            except Exception as e:
                self.logger.error(f"Error getting university recommendations: {e}")
                # Return standard recommendations if university recs fail
                return standard_recs
        
        return standard_recs
    
    async def _get_internal_recommendations(self, profile_state: dict) -> dict:
        """Get recommendations from internal sources"""
        recommendations = {
            "profile_quality": self.scorer.score_profile(profile_state),
            "improvement_suggestions": [],
            "content_suggestions": []
        }
        
        # Get recommendations from repository
        try:
            repo_recs = await self.repository.get_recommendations(profile_state)
            if repo_recs:
                recommendations.update(repo_recs)
        except Exception as e:
            self.logger.error(f"Error getting recommendations from repository: {e}")
            
        return recommendations
    
    def _extract_university_relevant_data(self, profile_state: dict) -> dict:
        """Extract relevant profile data for university recommendations"""
        return {
            "sections": profile_state.get("sections", {}),
            "context": profile_state.get("context", {})
        }
    
    def _is_profile_complete_enough(self, profile_state: dict) -> bool:
        """Check if profile has enough data for university recommendations"""
        academic = profile_state.get("sections", {}).get("academic", {})
        return academic.get("status") in ["completed", "reviewed"]
        
    async def shutdown(self):
        """Shutdown the recommendation service"""
        self.logger.info("Shutting down recommendation service")
        
        # Shutdown repository
        if self.repository:
            await self.repository.shutdown()
            
        # Shutdown university provider if available
        if self.university_provider:
            await self.university_provider.shutdown()
            
        self.logger.info("Recommendation service shut down successfully")
