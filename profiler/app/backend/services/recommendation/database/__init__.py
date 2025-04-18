"""
Database implementations for the recommendation service.

This package contains database-specific implementations for the recommendation service.
"""

from .models import (
    Base,
    RecommendationModel,
    ActionItemModel,
    ProfileSummaryModel,
    ProfileStrengthModel,
    ProfileImprovementModel,
    ProfileSellingPointModel
)
from .connection import DatabaseManager
from .repository import PostgreSQLRecommendationRepository

__all__ = [
    'Base',
    'RecommendationModel',
    'ActionItemModel',
    'ProfileSummaryModel',
    'ProfileStrengthModel',
    'ProfileImprovementModel',
    'ProfileSellingPointModel',
    'DatabaseManager',
    'PostgreSQLRecommendationRepository'
] 