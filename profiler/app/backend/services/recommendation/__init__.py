"""
Recommendation service package for generating profile recommendations.

This package contains components for generating recommendations based on user profiles,
calculating profile quality scores, and managing recommendation data.
"""

from .models import Recommendation, ProfileSummary
from .repository import RecommendationRepository
from .scoring import ProfileScorer
from .service import RecommendationService

__all__ = [
    'Recommendation',
    'ProfileSummary',
    'RecommendationRepository',
    'ProfileScorer',
    'RecommendationService',
] 