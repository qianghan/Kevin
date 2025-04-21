"""
Recommendation API router.

This module provides API endpoints for managing and generating recommendations.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query

from profiler.services.recommendation.models import Recommendation, RecommendationCategory
from profiler.services.recommendation.service import IRecommendationService
from profiler.dependencies import get_recommendation_service, get_current_user

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=List[Recommendation])
async def get_recommendations(
    status: Optional[str] = Query(None, description="Filter by status (active, completed, dismissed)"),
    current_user_id: str = Depends(get_current_user),
    recommendation_service: IRecommendationService = Depends(get_recommendation_service),
):
    """
    Get recommendations for the current user.

    Args:
        status: Optional filter by status.
        current_user_id: The ID of the current user.
        recommendation_service: The recommendation service.

    Returns:
        A list of recommendations for the user.
    """
    return await recommendation_service.get_recommendations_for_user(current_user_id, status)


@router.get("/generate", response_model=List[Recommendation])
async def generate_recommendations(
    current_user_id: str = Depends(get_current_user),
    recommendation_service: IRecommendationService = Depends(get_recommendation_service),
):
    """
    Generate new recommendations for the current user.

    Args:
        current_user_id: The ID of the current user.
        recommendation_service: The recommendation service.

    Returns:
        A list of newly generated recommendations for the user.
    """
    return await recommendation_service.generate_recommendations_for_user(current_user_id)


@router.get("/{recommendation_id}", response_model=Recommendation)
async def get_recommendation(
    recommendation_id: str,
    current_user_id: str = Depends(get_current_user),
    recommendation_service: IRecommendationService = Depends(get_recommendation_service),
):
    """
    Get a specific recommendation by ID.

    Args:
        recommendation_id: The ID of the recommendation to get.
        current_user_id: The ID of the current user.
        recommendation_service: The recommendation service.

    Returns:
        The recommendation if found.
    """
    recommendation = await recommendation_service.get_recommendation_by_id(recommendation_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if recommendation.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this recommendation")
    return recommendation


@router.patch("/{recommendation_id}/status", response_model=Recommendation)
async def update_status(
    recommendation_id: str,
    status: str,
    current_user_id: str = Depends(get_current_user),
    recommendation_service: IRecommendationService = Depends(get_recommendation_service),
):
    """
    Update the status of a recommendation.

    Args:
        recommendation_id: The ID of the recommendation to update.
        status: The new status (active, completed, dismissed).
        current_user_id: The ID of the current user.
        recommendation_service: The recommendation service.

    Returns:
        The updated recommendation if found.
    """
    # Verify the recommendation exists and belongs to the user
    recommendation = await recommendation_service.get_recommendation_by_id(recommendation_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if recommendation.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this recommendation")
    
    # Validate status value
    valid_statuses = ["active", "completed", "dismissed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    updated_recommendation = await recommendation_service.update_recommendation_status(recommendation_id, status)
    if not updated_recommendation:
        raise HTTPException(status_code=500, detail="Failed to update recommendation status")
    
    return updated_recommendation


@router.patch("/{recommendation_id}/progress", response_model=Recommendation)
async def update_progress(
    recommendation_id: str,
    progress: float,
    current_user_id: str = Depends(get_current_user),
    recommendation_service: IRecommendationService = Depends(get_recommendation_service),
):
    """
    Update the progress of a recommendation.

    Args:
        recommendation_id: The ID of the recommendation to update.
        progress: The new progress value (0.0 to 1.0).
        current_user_id: The ID of the current user.
        recommendation_service: The recommendation service.

    Returns:
        The updated recommendation if found.
    """
    # Verify the recommendation exists and belongs to the user
    recommendation = await recommendation_service.get_recommendation_by_id(recommendation_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    if recommendation.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this recommendation")
    
    # Validate progress value
    if progress < 0 or progress > 1:
        raise HTTPException(status_code=400, detail="Progress must be between 0.0 and 1.0")
    
    updated_recommendation = await recommendation_service.update_recommendation_progress(recommendation_id, progress)
    if not updated_recommendation:
        raise HTTPException(status_code=500, detail="Failed to update recommendation progress")
    
    return updated_recommendation


@router.get("/history", response_model=List[Recommendation])
async def get_recommendation_history(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering history"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering history"),
    current_user_id: str = Depends(get_current_user),
    recommendation_service: IRecommendationService = Depends(get_recommendation_service),
):
    """
    Get recommendation history for the current user.

    Args:
        start_date: Optional start date for filtering.
        end_date: Optional end date for filtering.
        current_user_id: The ID of the current user.
        recommendation_service: The recommendation service.

    Returns:
        A list of historical recommendations for the user.
    """
    return await recommendation_service.get_recommendation_history(current_user_id, start_date, end_date) 