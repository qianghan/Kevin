"""
Scoring module for evaluating profile quality.

This module provides functionality for calculating quality scores
for user profiles, both at the overall level and for specific sections.
"""

from typing import Dict, Any, List, Optional
import statistics

from ...utils.logging import get_logger

logger = get_logger(__name__)

class ProfileScorer:
    """
    Service for calculating profile quality scores.
    
    This class implements algorithms to evaluate the quality of user profiles
    based on completeness, relevance, and other factors.
    """
    
    def __init__(self, categories_config: Dict[str, Dict[str, Any]]):
        """
        Initialize the scorer with category configuration.
        
        Args:
            categories_config: Dictionary mapping category names to their configuration,
                              including weights and subcategories.
        """
        self.categories = categories_config
        logger.info(f"Initialized ProfileScorer with {len(categories_config)} categories")
    
    def calculate_quality_score(self, profile_data: Dict[str, Any]) -> float:
        """
        Calculate an overall quality score for a profile.
        
        Args:
            profile_data: Dictionary containing profile data organized by category
            
        Returns:
            Float between 0.0 and 1.0 representing overall quality
        """
        logger.info("Calculating overall profile quality score")
        
        # Check if profile is empty
        if not profile_data:
            logger.warning("Empty profile data - returning 0.0 quality score")
            return 0.0
        
        category_scores = []
        category_weights = []
        
        # Calculate score for each category
        for category, config in self.categories.items():
            if category in profile_data:
                weight = config.get("weight", 1.0)
                score = self.calculate_category_score(category, profile_data[category], config)
                
                category_scores.append(score)
                category_weights.append(weight)
                logger.debug(f"Category {category} score: {score:.2f} (weight: {weight:.2f})")
        
        # Return 0 if no categories were scored
        if not category_scores:
            logger.warning("No categories could be scored - returning 0.0 quality score")
            return 0.0
        
        # Calculate weighted average
        total_weight = sum(category_weights)
        if total_weight == 0:
            logger.warning("Total weight is 0 - using simple average instead")
            overall_score = statistics.mean(category_scores)
        else:
            weighted_sum = sum(score * weight for score, weight in zip(category_scores, category_weights))
            overall_score = weighted_sum / total_weight
        
        logger.info(f"Overall profile quality score: {overall_score:.2f}")
        return min(max(overall_score, 0.0), 1.0)  # Ensure score is between 0 and 1
    
    def calculate_category_score(self, category: str, category_data: Dict[str, Any], 
                               config: Dict[str, Any]) -> float:
        """
        Calculate a quality score for a specific category.
        
        Args:
            category: Name of the category
            category_data: Data for the category
            config: Configuration for the category
            
        Returns:
            Float between 0.0 and 1.0 representing category quality
        """
        logger.info(f"Calculating quality score for category: {category}")
        
        if not category_data:
            logger.warning(f"Empty data for category {category} - returning 0.0")
            return 0.0
        
        subcategories = config.get("subcategories", [])
        
        # If no subcategories defined, calculate completeness score
        if not subcategories:
            logger.debug(f"No subcategories defined for {category} - using simple completeness score")
            return self._calculate_completeness_score(category_data)
        
        # Calculate scores for each subcategory
        subcategory_scores = []
        for subcategory in subcategories:
            if subcategory in category_data:
                score = self._calculate_subcategory_score(subcategory, category_data[subcategory])
                subcategory_scores.append(score)
                logger.debug(f"Subcategory {subcategory} score: {score:.2f}")
            else:
                logger.debug(f"Subcategory {subcategory} not found in data")
        
        # Return average of subcategory scores, or 0 if none
        if not subcategory_scores:
            logger.warning(f"No subcategories could be scored for {category} - returning 0.0")
            return 0.0
        
        category_score = statistics.mean(subcategory_scores)
        logger.info(f"Category {category} score: {category_score:.2f}")
        return category_score
    
    def _calculate_subcategory_score(self, subcategory: str, data: Any) -> float:
        """
        Calculate a quality score for a specific subcategory.
        
        Args:
            subcategory: Name of the subcategory
            data: Data for the subcategory
            
        Returns:
            Float between 0.0 and 1.0 representing subcategory quality
        """
        if data is None:
            return 0.0
        
        # For list/array data, check length and content
        if isinstance(data, list):
            if not data:
                return 0.0
            
            # Simple scoring based on number of items (up to 5)
            # More sophisticated scoring could analyze content quality
            return min(len(data) / 5.0, 1.0)
        
        # For string data, check length
        elif isinstance(data, str):
            # Simple scoring based on length
            # More sophisticated scoring could analyze text quality
            return min(len(data) / 500.0, 1.0)
        
        # For dict data, check number of fields
        elif isinstance(data, dict):
            if not data:
                return 0.0
            return min(len(data) / 5.0, 1.0)
        
        # For numeric data, assume it's already a score
        elif isinstance(data, (int, float)):
            return min(max(float(data), 0.0), 1.0)
        
        # Default case
        return 0.5
    
    def _calculate_completeness_score(self, data: Dict[str, Any]) -> float:
        """
        Calculate a simple completeness score based on filled fields.
        
        Args:
            data: Dictionary containing field data
            
        Returns:
            Float between 0.0 and 1.0 representing completeness
        """
        if not data:
            return 0.0
        
        filled_fields = sum(1 for value in data.values() if value is not None and value != "" and value != [])
        total_fields = len(data)
        
        if total_fields == 0:
            return 0.0
        
        return filled_fields / total_fields 