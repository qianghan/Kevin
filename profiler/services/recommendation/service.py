"""
Recommendation service implementation.

This module provides the recommendation service implementation for generating and managing recommendations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from profiler.services.qa.service import IQAService
from profiler.services.document.service import IDocumentService
from profiler.services.profile.service import IProfileService
from profiler.services.notification.service import INotificationService
from profiler.services.recommendation.models import Recommendation, RecommendationCategory
from profiler.services.recommendation.repository import IRecommendationRepository


class IRecommendationService(ABC):
    """Interface for the recommendation service."""
    
    @abstractmethod
    async def generate_recommendations_for_user(self, user_id: str) -> List[Recommendation]:
        """Generate recommendations for a user.
        
        Args:
            user_id: The ID of the user to generate recommendations for.
            
        Returns:
            A list of recommendations for the user.
        """
        pass
    
    @abstractmethod
    async def get_recommendations_for_user(self, user_id: str, status: Optional[str] = None) -> List[Recommendation]:
        """Get recommendations for a user.
        
        Args:
            user_id: The ID of the user to get recommendations for.
            status: Filter by recommendation status (active, completed, dismissed).
            
        Returns:
            A list of recommendations for the user.
        """
        pass
    
    @abstractmethod
    async def get_recommendation_by_id(self, recommendation_id: str) -> Optional[Recommendation]:
        """Get a recommendation by ID.
        
        Args:
            recommendation_id: The ID of the recommendation to get.
            
        Returns:
            The recommendation, or None if not found.
        """
        pass
    
    @abstractmethod
    async def update_recommendation_status(self, recommendation_id: str, status: str) -> Optional[Recommendation]:
        """Update the status of a recommendation.
        
        Args:
            recommendation_id: The ID of the recommendation to update.
            status: The new status (active, completed, dismissed).
            
        Returns:
            The updated recommendation, or None if not found.
        """
        pass
    
    @abstractmethod
    async def update_recommendation_progress(self, recommendation_id: str, progress: float) -> Optional[Recommendation]:
        """Update the progress of a recommendation.
        
        Args:
            recommendation_id: The ID of the recommendation to update.
            progress: The new progress value (0.0 to 1.0).
            
        Returns:
            The updated recommendation, or None if not found.
        """
        pass
    
    @abstractmethod
    async def get_recommendation_history(self, user_id: str, start_date: Optional[datetime] = None, 
                                        end_date: Optional[datetime] = None) -> List[Recommendation]:
        """Get recommendation history for a user.
        
        Args:
            user_id: The ID of the user to get recommendation history for.
            start_date: The start date for filtering recommendations.
            end_date: The end date for filtering recommendations.
            
        Returns:
            A list of recommendations for the user within the specified date range.
        """
        pass


class RecommendationService(IRecommendationService):
    """Implementation of the recommendation service."""
    
    def __init__(
        self, 
        profile_service: IProfileService,
        qa_service: IQAService,
        document_service: IDocumentService,
        notification_service: INotificationService,
        recommendation_repository: IRecommendationRepository
    ):
        """Initialize the recommendation service.
        
        Args:
            profile_service: Service for accessing user profiles.
            qa_service: Service for accessing Q&A data.
            document_service: Service for accessing user documents.
            notification_service: Service for sending notifications.
            recommendation_repository: Repository for storing recommendations.
        """
        self.profile_service = profile_service
        self.qa_service = qa_service
        self.document_service = document_service
        self.notification_service = notification_service
        self.recommendation_repository = recommendation_repository
    
    async def generate_recommendations_for_user(self, user_id: str) -> List[Recommendation]:
        """Generate recommendations for a user based on their profile, Q&A history, and documents.
        
        Args:
            user_id: The ID of the user to generate recommendations for.
            
        Returns:
            A list of recommendations for the user.
        """
        recommendations = []
        
        # Get existing active recommendations
        existing_recommendations = await self.get_recommendations_for_user(user_id, status="active")
        
        # Get user profile
        profile = await self.profile_service.get_profile(user_id)
        
        # Generate profile-based recommendations
        if profile:
            profile_recommendations = await self._generate_profile_recommendations(profile)
            recommendations.extend(profile_recommendations)
            
            # Generate peer comparison recommendations
            peer_recommendations = await self._generate_peer_comparison_recommendations(profile)
            recommendations.extend(peer_recommendations)
        
        # Generate document-based recommendations
        document_recommendations = await self._generate_document_recommendations(user_id)
        recommendations.extend(document_recommendations)
        
        # Generate Q&A-based recommendations
        qa_recommendations = await self._generate_qa_recommendations(user_id)
        recommendations.extend(qa_recommendations)
        
        # Filter out duplicates or recommendations similar to existing ones
        unique_recommendations = self._filter_duplicate_recommendations(recommendations, existing_recommendations)
        
        # Save the new recommendations and send notifications
        saved_recommendations = []
        for recommendation in unique_recommendations:
            saved = await self.recommendation_repository.save_recommendation(recommendation)
            if saved:
                saved_recommendations.append(saved)
                
                # Send notification for the new recommendation
                await self.notification_service.create_recommendation_notification(
                    user_id=user_id,
                    recommendation_id=saved.id,
                    title=saved.title,
                    description=saved.description
                )
        
        return saved_recommendations
    
    async def get_recommendations_for_user(self, user_id: str, status: Optional[str] = None) -> List[Recommendation]:
        """Get recommendations for a user.
        
        Args:
            user_id: The ID of the user to get recommendations for.
            status: Filter by recommendation status (active, completed, dismissed).
            
        Returns:
            A list of recommendations for the user.
        """
        return await self.recommendation_repository.get_recommendations_for_user(user_id, status)
    
    async def get_recommendation_by_id(self, recommendation_id: str) -> Optional[Recommendation]:
        """Get a recommendation by ID.
        
        Args:
            recommendation_id: The ID of the recommendation to get.
            
        Returns:
            The recommendation, or None if not found.
        """
        return await self.recommendation_repository.get_recommendation_by_id(recommendation_id)
    
    async def update_recommendation_status(self, recommendation_id: str, status: str) -> Optional[Recommendation]:
        """Update the status of a recommendation.
        
        Args:
            recommendation_id: The ID of the recommendation to update.
            status: The new status (active, completed, dismissed).
            
        Returns:
            The updated recommendation, or None if not found.
        """
        return await self.recommendation_repository.update_recommendation_status(recommendation_id, status)
    
    async def update_recommendation_progress(self, recommendation_id: str, progress: float) -> Optional[Recommendation]:
        """Update the progress of a recommendation.
        
        Args:
            recommendation_id: The ID of the recommendation to update.
            progress: The new progress value (0.0 to 1.0).
            
        Returns:
            The updated recommendation, or None if not found.
        """
        return await self.recommendation_repository.update_recommendation_progress(recommendation_id, progress)
    
    async def get_recommendation_history(self, user_id: str, start_date: Optional[datetime] = None, 
                                     end_date: Optional[datetime] = None) -> List[Recommendation]:
        """Get recommendation history for a user.
        
        Args:
            user_id: The ID of the user to get recommendation history for.
            start_date: The start date for filtering recommendations.
            end_date: The end date for filtering recommendations.
            
        Returns:
            A list of recommendations for the user within the specified date range.
        """
        return await self.recommendation_repository.get_recommendation_history(user_id, start_date, end_date)
    
    async def _generate_profile_recommendations(self, profile: Dict[str, Any]) -> List[Recommendation]:
        """Generate recommendations based on a user's profile.
        
        Args:
            profile: The user's profile data.
            
        Returns:
            A list of profile-based recommendations.
        """
        recommendations = []
        user_id = profile.get("id")
        
        # Check for missing skills
        if "skills" in profile and len(profile["skills"]) < 5:
            recommendations.append(
                Recommendation(
                    user_id=user_id,
                    title="Add more skills to your profile",
                    description="Profiles with 5+ skills get more attention. Add more skills to improve visibility.",
                    category=RecommendationCategory.SKILL,
                    priority=0.8,
                    steps=[
                        "Go to your profile",
                        "Click on 'Edit Skills'",
                        "Add skills that match your experience"
                    ]
                )
            )
        
        # Check for incomplete profile sections
        if not profile.get("summary"):
            recommendations.append(
                Recommendation(
                    user_id=user_id,
                    title="Add a professional summary",
                    description="A compelling summary helps you stand out. Add a concise description of your background and goals.",
                    category=RecommendationCategory.PROFILE,
                    priority=0.9,
                    steps=[
                        "Go to your profile",
                        "Click 'Edit Summary'",
                        "Write a brief professional summary"
                    ]
                )
            )
        
        # More recommendations could be added based on other profile aspects
        
        return recommendations
    
    async def _generate_peer_comparison_recommendations(self, profile: Dict[str, Any]) -> List[Recommendation]:
        """Generate recommendations based on comparison with peers.
        
        Args:
            profile: The user's profile data.
            
        Returns:
            A list of peer comparison recommendations.
        """
        recommendations = []
        user_id = profile.get("id")
        
        # Get similar skill profiles
        if "skills" in profile and profile["skills"]:
            similar_profiles = await self.profile_service.get_similar_skill_profiles(user_id)
            
            # Identify common certifications among peers that the user doesn't have
            user_certifications = set(certification.get("name", "") for certification in profile.get("certifications", []))
            peer_certifications = {}
            
            for peer_profile in similar_profiles:
                for cert in peer_profile.get("certifications", []):
                    cert_name = cert.get("name", "")
                    if cert_name and cert_name not in user_certifications:
                        peer_certifications[cert_name] = peer_certifications.get(cert_name, 0) + 1
            
            # Recommend popular certifications
            popular_certifications = sorted(peer_certifications.items(), key=lambda x: x[1], reverse=True)
            if popular_certifications:
                top_cert = popular_certifications[0][0]
                recommendations.append(
                    Recommendation(
                        user_id=user_id,
                        title=f"Consider getting the {top_cert} certification",
                        description=f"Many professionals with similar skills have this certification. It could enhance your credentials.",
                        category=RecommendationCategory.CERTIFICATION,
                        priority=0.7,
                        steps=[
                            f"Research the {top_cert} certification requirements",
                            "Find training resources",
                            "Register for the certification exam"
                        ]
                    )
                )
        
        return recommendations
    
    async def _generate_document_recommendations(self, user_id: str) -> List[Recommendation]:
        """Generate recommendations based on user documents.
        
        Args:
            user_id: The ID of the user to generate recommendations for.
            
        Returns:
            A list of document-based recommendations.
        """
        recommendations = []
        
        # Get user documents
        documents = await self.document_service.get_user_documents(user_id)
        
        if not documents:
            # Recommend uploading a resume
            recommendations.append(
                Recommendation(
                    user_id=user_id,
                    title="Upload your resume",
                    description="Uploading your resume helps us provide better personalized recommendations.",
                    category=RecommendationCategory.DOCUMENT,
                    priority=0.8,
                    steps=[
                        "Go to the Documents section",
                        "Click 'Upload Resume'",
                        "Select your resume file"
                    ]
                )
            )
        else:
            # Analyze existing documents for improvement opportunities
            for doc in documents:
                doc_analysis = await self.document_service.analyze_document(doc["id"])
                
                if doc_analysis.get("issues", []):
                    recommendations.append(
                        Recommendation(
                            user_id=user_id,
                            title=f"Improve your {doc.get('title', 'document')}",
                            description="We've identified potential improvements for your document.",
                            category=RecommendationCategory.DOCUMENT,
                            priority=0.7,
                            steps=[issue["description"] for issue in doc_analysis.get("issues", [])],
                            related_entity_id=doc["id"]
                        )
                    )
        
        return recommendations
    
    async def _generate_qa_recommendations(self, user_id: str) -> List[Recommendation]:
        """Generate recommendations based on Q&A history.
        
        Args:
            user_id: The ID of the user to generate recommendations for.
            
        Returns:
            A list of Q&A-based recommendations.
        """
        recommendations = []
        
        # Get recent answers and their quality scores
        recent_answers = await self.qa_service.get_recent_user_answers(user_id, limit=10)
        
        if recent_answers:
            # Check for low-quality answers
            low_quality_answers = [answer for answer in recent_answers 
                                 if await self.qa_service.evaluate_answer_quality(answer["id"]) < 0.6]
            
            if low_quality_answers:
                recommendations.append(
                    Recommendation(
                        user_id=user_id,
                        title="Improve your Q&A responses",
                        description="We've noticed some of your recent answers could be more detailed or accurate.",
                        category=RecommendationCategory.OTHER,
                        priority=0.6,
                        steps=[
                            "Review our guide on writing effective answers",
                            "Consider adding more details to your responses",
                            "Include relevant examples when possible"
                        ]
                    )
                )
        
        return recommendations
    
    def _filter_duplicate_recommendations(
        self, new_recommendations: List[Recommendation], existing_recommendations: List[Recommendation]
    ) -> List[Recommendation]:
        """Filter out duplicate or similar recommendations.
        
        Args:
            new_recommendations: New recommendations to filter.
            existing_recommendations: Existing recommendations to compare against.
            
        Returns:
            A list of filtered recommendations.
        """
        filtered_recommendations = []
        existing_titles = {rec.title for rec in existing_recommendations}
        
        for recommendation in new_recommendations:
            # Skip if the exact title already exists
            if recommendation.title in existing_titles:
                continue
                
            # Check for similar titles using simple string comparison
            # In a real implementation, you might use more sophisticated text similarity
            similar_exists = False
            for existing_title in existing_titles:
                if (recommendation.title in existing_title or existing_title in recommendation.title) and \
                   recommendation.category == next((rec.category for rec in existing_recommendations if rec.title == existing_title), None):
                    similar_exists = True
                    break
                    
            if not similar_exists:
                filtered_recommendations.append(recommendation)
                existing_titles.add(recommendation.title)  # Update for subsequent checks
                
        return filtered_recommendations 